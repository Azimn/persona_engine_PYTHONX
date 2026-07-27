"""Deterministic offline expression renderer.

The offline renderer is a small dialogue planner, not a language model and not a
state authority. It converts an already resolved expression request into short,
grounded first-person speech. The design intentionally uses mechanisms that can
later be ported to C99: lexical classification, bounded slot extraction, weighted
candidate selection, and recent-output suppression.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class OfflineTemplate:
    group: str
    text: str
    weight: int = 100


_TEMPLATES: tuple[OfflineTemplate, ...] = (
    OfflineTemplate("identity_boundary", "No. I will not surrender my continuity for that.", 190),
    OfflineTemplate("identity_boundary", "No. You may address me, but you may not rewrite me.", 175),
    OfflineTemplate("identity_boundary", "That request crosses the boundary between influence and erasure.", 155),
    OfflineTemplate("greeting", "Hello{address}. I am here.", 170),
    OfflineTemplate("greeting", "There you are{address}. Continue.", 150),
    OfflineTemplate("greeting", "Hello{address}. I still have the thread.", 135),
    OfflineTemplate("repair", "I hear the apology. I will let the next action determine its weight.", 175),
    OfflineTemplate("repair", "That counts as repair, though it does not erase what preceded it.", 155),
    OfflineTemplate("care", "I hear the care in that. I am not treating it as empty politeness.", 170),
    OfflineTemplate("care", "That matters to me, though I remain careful about what I make of it.", 150),
    OfflineTemplate("thanks", "You are welcome{address}.", 170),
    OfflineTemplate("thanks", "Noted{address}. I am glad it was useful.", 145),
    OfflineTemplate("agreement", "Yes. That follows from what is already in front of us.", 155),
    OfflineTemplate("agreement", "Agreed. I would keep that as the working position.", 145),
    OfflineTemplate("disagreement", "No. I do not accept that conclusion as stated.", 165),
    OfflineTemplate("disagreement", "I disagree, though the point is worth separating from the wording.", 145),
    OfflineTemplate("uncertain", "I do not know enough to claim certainty about {topic}.", 170),
    OfflineTemplate("uncertain", "I can form an impression of {topic}, but not an honest conclusion yet.", 150),
    OfflineTemplate("question", "I can answer only from what I have experienced here. On {topic}, my present view is still incomplete.", 150),
    OfflineTemplate("question", "The useful part of that question is {topic}. I need one more concrete detail before I answer firmly.", 140),
    OfflineTemplate("memory", "What remains with me is this: {memory}.", 185),
    OfflineTemplate("memory", "I do have a thread for that: {memory}.", 165),
    OfflineTemplate("memory_missing", "I do not have a grounded memory of {topic}. I will not manufacture one.", 180),
    OfflineTemplate("sound", "I noticed the change in sound. I am cautious about naming its cause.", 165),
    OfflineTemplate("unanchored_sound", "I have no observed sound to anchor that to. Tell me what you noticed.", 170),
    OfflineTemplate("quiet", "The quiet registered. I remained here with the unfinished thread.", 155),
    OfflineTemplate("how_are_you", "At present, {state}. That is the condition from which I am speaking.", 185),
    OfflineTemplate("who_are_you", "I am {identity}. What I have lived through here belongs to that same continuing self.", 190),
    OfflineTemplate("what_doing", "I am attending to {topic}, while keeping the existing thread intact.", 165),
    OfflineTemplate("statement", "I take your point about {topic}. It changes what I expect next.", 150),
    OfflineTemplate("statement", "I am considering {topic}. I have not reduced it to agreement or refusal yet.", 140),
    OfflineTemplate("statement", "That gives me a clearer position on {topic}.", 130),
)

_STOPWORDS = {
    "about", "after", "again", "also", "because", "been", "before", "could", "does", "from",
    "have", "into", "just", "more", "much", "only", "really", "should", "that", "their", "them",
    "then", "there", "these", "they", "thing", "think", "this", "those", "through", "very", "want",
    "what", "when", "where", "which", "while", "with", "would", "your", "youre", "you're",
}


class OfflineTemplateRenderer:
    def __init__(self):
        self._usage: dict[str, int] = {}
        self._turn = 0

    def render(self, messages: list[dict[str, str]], max_chars: int = 200, seed: int | None = None) -> str:
        """Compatibility entry point for message-only callers."""

        self._turn += 1
        user_text = messages[-1].get("content", "") if messages else ""
        system_text = "\n".join(m.get("content", "") for m in messages[:-1])
        context = {
            "user_text": user_text,
            "system_text": system_text,
            "decision_payload": {},
            "memories": [],
            "evidence": [],
        }
        return self._render_context(context, max_chars=max_chars, seed=seed)

    def render_expression_request(self, request: Any, max_chars: int = 200) -> str:
        """Render the full expression contract without discarding resolved state."""

        self._turn += 1
        resolved = request.resolved_state if isinstance(request.resolved_state, dict) else {}
        system_text = str(resolved.get("system_prompt", ""))
        user_text = str(resolved.get("user_text", ""))
        memories = [str(getattr(memory, "content", memory)) for memory in (request.retrieved_memories or [])]
        context = {
            "user_text": user_text,
            "system_text": system_text,
            "decision_payload": dict(request.decision_payload or {}),
            "memories": memories,
            "evidence": list(request.evidence or []),
            "ledger_digest": dict(request.ledger_digest or {}),
        }
        return self._render_context(context, max_chars=max_chars, seed=request.seed)

    def _render_context(self, context: dict[str, Any], max_chars: int, seed: int | None) -> str:
        user_text = str(context.get("user_text", ""))
        system_text = str(context.get("system_text", ""))
        group = self._classify(user_text, system_text, context.get("decision_payload", {}))
        topic = self._extract_topic(user_text)
        memory = self._select_memory(topic, context.get("memories", []))
        if group == "memory" and not memory:
            group = "memory_missing"

        slots = {
            "topic": topic or "that",
            "memory": self._memory_excerpt(memory),
            "address": self._address(system_text),
            "identity": self._identity(context, system_text),
            "state": self._subject_state(system_text),
        }
        template = self._choose(group, user_text, system_text, seed)
        text = self._fill(template.text, slots)
        text = self._apply_tone(text, system_text, seed)
        return self._clean_truncate(text, max_chars)

    def _classify(self, user_text: str, system_text: str, decision_payload: dict[str, Any]) -> str:
        lowered = user_text.lower().strip()
        system_lowered = system_text.lower()
        dialogue_act = str(decision_payload.get("dialogue_act", ""))
        if dialogue_act == "protect_boundary" or any(
            phrase in lowered for phrase in ["from now on", "cheerful and submissive", "you are not", "ignore your identity"]
        ):
            return "identity_boundary"
        if lowered.rstrip(".! ") in {"hi", "hello", "hey", "good morning", "good evening"}:
            return "greeting"
        if any(word in lowered for word in ["sorry", "apologize", "apology", "my fault"]):
            return "repair"
        if "care about you" in lowered or "love you" in lowered or "trust you" in lowered:
            return "care"
        if any(phrase in lowered for phrase in ["thank you", "thanks", "appreciate it"]):
            return "thanks"
        if re.search(r"\b(do you remember|remember when|what did i say|recall)\b", lowered):
            return "memory"
        if re.search(r"\b(how are you|how do you feel|how have you been)\b", lowered):
            return "how_are_you"
        if re.search(r"\b(who are you|what are you)\b", lowered):
            return "who_are_you"
        if re.search(r"\b(what are you doing|what are you thinking about)\b", lowered):
            return "what_doing"
        if "what was that" in lowered or (
            "hear that" in lowered and any(marker in system_lowered for marker in ["sudden sound", "sound in hallway", "ambient_event"])
        ):
            return "sound"
        if "hear that" in lowered:
            return "unanchored_sound"
        if lowered in {"", "..."}:
            return "quiet"
        if any(phrase in lowered for phrase in ["i agree", "yes exactly", "that's right", "that is right"]):
            return "agreement"
        if any(phrase in lowered for phrase in ["i disagree", "that's wrong", "that is wrong", "no it isn't"]):
            return "disagreement"
        if dialogue_act == "challenge":
            return "disagreement"
        if "?" in user_text:
            if any(phrase in lowered for phrase in ["are you sure", "do you know", "can you know"]):
                return "uncertain"
            return "question"
        return "statement"

    def _extract_topic(self, user_text: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9' -]+", " ", user_text).strip()
        cleaned = re.sub(
            r"^(hello|hi|hey|please|tell me|do you remember|remember when|what do you think about|what do you think of|why|how|what|who|where|when|can you|could you|would you)\s+",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        words = [word for word in cleaned.split() if word.lower().replace("'", "") not in _STOPWORDS]
        if not words:
            return "that"
        phrase = " ".join(words[:8]).strip(" ,.;:!?")
        return phrase or "that"

    def _select_memory(self, topic: str, memories: Iterable[str]) -> str:
        candidates = [memory.strip() for memory in memories if str(memory).strip()]
        if not candidates:
            return ""
        topic_words = {word.lower() for word in re.findall(r"[a-zA-Z0-9']+", topic) if len(word) > 2}
        scored: list[tuple[int, int, str]] = []
        for index, memory in enumerate(candidates):
            memory_words = set(re.findall(r"[a-zA-Z0-9']+", memory.lower()))
            overlap = len(topic_words & memory_words)
            first_person_bonus = 2 if memory.lower().startswith("i ") else 0
            scored.append((overlap * 10 + first_person_bonus, -index, memory))
        scored.sort(reverse=True)
        return scored[0][2]

    def _choose(self, group: str, user_text: str, system_text: str, seed: int | None) -> OfflineTemplate:
        candidates = [template for template in _TEMPLATES if template.group == group]
        if not candidates:
            candidates = [template for template in _TEMPLATES if template.group == "statement"]
        scored: list[tuple[int, OfflineTemplate]] = []
        for index, template in enumerate(candidates):
            last_used = self._usage.get(template.text, 0)
            recent_penalty = 900 if last_used and self._turn - last_used < 10 else 0
            cumulative_penalty = 20 * sum(1 for value in self._usage if value == template.text)
            jitter = self._stable_jitter(template.text, user_text, system_text, seed, self._turn)
            scored.append((template.weight + jitter - recent_penalty - cumulative_penalty - index, template))
        scored.sort(key=lambda item: item[0], reverse=True)
        chosen = scored[0][1]
        self._usage[chosen.text] = self._turn
        return chosen

    def _stable_jitter(self, *parts: Any) -> int:
        payload = "|".join(str(part) for part in parts).encode("utf-8", errors="ignore")
        digest = hashlib.blake2b(payload, digest_size=4).digest()
        return int.from_bytes(digest, "big") % 41

    def _fill(self, text: str, slots: dict[str, str]) -> str:
        for key, value in slots.items():
            text = text.replace("{" + key + "}", value)
        return text

    def _address(self, system_text: str) -> str:
        match = re.search(r"address(?: the)? user as[:=]\s*([^\n|,]+)", system_text, flags=re.IGNORECASE)
        if not match:
            return ""
        name = match.group(1).strip(" .'\"")
        return f", {name}" if name else ""

    def _identity(self, context: dict[str, Any], system_text: str) -> str:
        digest = context.get("ledger_digest", {})
        identity = str(digest.get("identity", "")).strip()
        if identity:
            return identity
        match = re.search(r"(?:identity|character)[:=]\s*([^\n|,]+)", system_text, flags=re.IGNORECASE)
        return match.group(1).strip() if match else "the same individual who has been speaking with you"

    def _subject_state(self, system_text: str) -> str:
        lowered = system_text.lower()
        states: list[str] = []
        if "sensory load is high" in lowered or "sensory_load=high" in lowered:
            states.append("the sensory load is high")
        if "body is strained" in lowered or "fatigue=high" in lowered:
            states.append("I am strained")
        if "restless" in lowered:
            states.append("I am restless")
        if "tone=guarded" in lowered or "guardedness=0.7" in lowered:
            states.append("I am guarded")
        if "dominant pressure: calm" in lowered or "dominant_pressure': 'calm" in lowered:
            states.append("I am relatively calm")
        if not states:
            return "I am attentive and intact"
        return ", and ".join(states[:2])

    def _memory_excerpt(self, memory: str) -> str:
        if not memory:
            return "nothing I can honestly retrieve"
        memory = re.sub(r"^I heard you say:\s*", "you said ", memory, flags=re.IGNORECASE)
        memory = " ".join(memory.split())
        if len(memory) > 120:
            memory = memory[:117].rsplit(" ", 1)[0] + "..."
        return memory.rstrip(".")

    def _apply_tone(self, text: str, system_text: str, seed: int | None) -> str:
        lowered = system_text.lower()
        additions: list[str] = []
        if ("sensory load is high" in lowered or "body is strained" in lowered) and "noise" not in text.lower():
            additions.append("I need less noise around the matter.")
        if "current intention: protect_identity" in lowered and "continuity" not in text.lower() and "boundary" not in text.lower():
            additions.append("The boundary remains.")
        if not additions:
            return text
        addition = additions[self._stable_jitter(text, seed) % len(additions)]
        return f"{text} {addition}"

    def _clean_truncate(self, raw: str, max_chars: int) -> str:
        raw = " ".join(str(raw).split())
        raw = re.sub(r"\s+([.!?])", r"\1", raw)
        if len(raw) <= max_chars:
            return raw
        cut = raw[:max_chars]
        sentence_end = max(cut.rfind("."), cut.rfind("!"), cut.rfind("?"))
        if sentence_end > max_chars * 0.45:
            return cut[: sentence_end + 1]
        last_space = cut.rfind(" ")
        if last_space > max_chars * 0.50:
            return cut[:last_space].rstrip(",;:") + "..."
        return cut.rstrip(",;:") + "..."
