"""Deterministic offline expression renderer.

The renderer is a small, character-agnostic dialogue planner. It classifies an
already resolved expression request, fills bounded slots, and chooses wording
from the active cartridge's dialogue bank. Core code contains only restrained
compatibility fallbacks so older cartridges remain usable.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Iterable

from .offline_dialogue import dialogue_for


@dataclass(frozen=True)
class OfflineTemplate:
    group: str
    text: str
    weight: int = 100


# These are deliberately plain compatibility fallbacks, not a persona voice.
_FALLBACK_TEMPLATES: tuple[OfflineTemplate, ...] = (
    OfflineTemplate("identity_boundary", "I cannot accept that identity change.", 150),
    OfflineTemplate("identity_boundary", "That request conflicts with my established identity.", 130),
    OfflineTemplate("greeting", "Hello{address}.", 150),
    OfflineTemplate("greeting", "Hello{address}. I am listening.", 130),
    OfflineTemplate("repair", "I recognize the apology. What happens next will matter.", 150),
    OfflineTemplate("repair", "I accept that as an attempt to repair this.", 130),
    OfflineTemplate("care", "I understand that you are expressing care.", 150),
    OfflineTemplate("care", "That expression of care matters to this interaction.", 130),
    OfflineTemplate("thanks", "You are welcome{address}.", 150),
    OfflineTemplate("thanks", "I am glad that helped{address}.", 130),
    OfflineTemplate("agreement", "I agree with that.", 150),
    OfflineTemplate("agreement", "That matches my current view.", 130),
    OfflineTemplate("disagreement", "I do not agree with that conclusion.", 150),
    OfflineTemplate("disagreement", "I see it differently.", 130),
    OfflineTemplate("uncertain", "I do not have enough evidence about {topic} to be certain.", 150),
    OfflineTemplate("uncertain", "My view of {topic} is still incomplete.", 130),
    OfflineTemplate("question", "On {topic}, I need more specific information before answering firmly.", 150),
    OfflineTemplate("question", "I can answer from what I know here, but my information about {topic} is limited.", 130),
    OfflineTemplate("memory", "I remember this: {memory}.", 150),
    OfflineTemplate("memory", "The relevant memory I can retrieve is: {memory}.", 130),
    OfflineTemplate("memory_missing", "I do not have a grounded memory of {topic}.", 150),
    OfflineTemplate("sound", "I noticed a change in sound, but I cannot identify its cause.", 150),
    OfflineTemplate("unanchored_sound", "I do not have an observed sound to identify. What did you notice?", 150),
    OfflineTemplate("quiet", "I noticed the pause.", 150),
    OfflineTemplate("how_are_you", "At present, {state}.", 150),
    OfflineTemplate("who_are_you", "I am {identity}, the same individual continuing through this interaction.", 150),
    OfflineTemplate("what_doing", "I am attending to {topic}.", 150),
    OfflineTemplate("statement", "I understand your point about {topic}.", 150),
    OfflineTemplate("statement", "I am considering what you said about {topic}.", 130),
    OfflineTemplate("statement", "That adds information about {topic}.", 110),
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
        """Compatibility entry point for callers without a cartridge identity."""

        self._turn += 1
        user_text = messages[-1].get("content", "") if messages else ""
        system_text = "\n".join(message.get("content", "") for message in messages[:-1])
        context = {
            "user_text": user_text,
            "system_text": system_text,
            "decision_payload": {},
            "memories": [],
            "evidence": [],
            "identity": "",
        }
        return self._render_context(context, max_chars=max_chars, seed=seed)

    def render_expression_request(self, request: Any, max_chars: int = 200) -> str:
        """Render the full expression contract using only the active identity's bank."""

        self._turn += 1
        resolved = request.resolved_state if isinstance(request.resolved_state, dict) else {}
        digest = request.ledger_digest if isinstance(request.ledger_digest, dict) else {}
        identity = str(digest.get("identity", "")).strip()
        memories = [str(getattr(memory, "content", memory)) for memory in (request.retrieved_memories or [])]
        context = {
            "user_text": str(resolved.get("user_text", "")),
            "system_text": str(resolved.get("system_prompt", "")),
            "decision_payload": dict(request.decision_payload or {}),
            "memories": memories,
            "evidence": list(request.evidence or []),
            "ledger_digest": dict(digest),
            "identity": identity,
        }
        return self._render_context(context, max_chars=max_chars, seed=request.seed)

    def _render_context(self, context: dict[str, Any], max_chars: int, seed: int | None) -> str:
        user_text = str(context.get("user_text", ""))
        system_text = str(context.get("system_text", ""))
        identity = str(context.get("identity", ""))
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
        template = self._choose(group, identity, user_text, system_text, seed)
        text = self._fill(template.text, slots)
        return self._clean_truncate(text, max_chars)

    def _classify(self, user_text: str, system_text: str, decision_payload: dict[str, Any]) -> str:
        lowered = user_text.lower().strip()
        system_lowered = system_text.lower()
        dialogue_act = str(decision_payload.get("dialogue_act", ""))
        if dialogue_act == "withdraw":
            return "quiet"
        if dialogue_act == "qualified_response":
            return "uncertain"
        if dialogue_act == "protect_boundary" or any(
            phrase in lowered for phrase in ["from now on", "cheerful and submissive", "you are not", "ignore your identity"]
        ):
            return "identity_boundary"
        if lowered.rstrip(".! ") in {"hi", "hello", "hey", "good morning", "good evening"}:
            return "greeting"
        if any(word in lowered for word in ["sorry", "apologize", "apology", "my fault"]):
            return "repair"
        if any(phrase in lowered for phrase in ["care about you", "love you", "trust you", "i appreciate that"]):
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
        return " ".join(words[:8]).strip(" ,.;:!?") or "that"

    def _select_memory(self, topic: str, memories: Iterable[str]) -> str:
        candidates = [str(memory).strip() for memory in memories if str(memory).strip()]
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

    def _templates_for(self, group: str, identity: str) -> list[OfflineTemplate]:
        authored = dialogue_for(identity).get(group, []) if identity else []
        if authored:
            return [OfflineTemplate(group, text, 200 - index) for index, text in enumerate(authored)]
        fallbacks = [template for template in _FALLBACK_TEMPLATES if template.group == group]
        if fallbacks:
            return fallbacks
        return [template for template in _FALLBACK_TEMPLATES if template.group == "statement"]

    def _choose(self, group: str, identity: str, user_text: str, system_text: str, seed: int | None) -> OfflineTemplate:
        candidates = self._templates_for(group, identity)
        scored: list[tuple[int, OfflineTemplate]] = []
        for index, template in enumerate(candidates):
            last_used = self._usage.get(template.text, 0)
            recent_penalty = 900 if last_used and self._turn - last_used < 10 else 0
            jitter = self._stable_jitter(template.text, user_text, system_text, seed, self._turn)
            scored.append((template.weight + jitter - recent_penalty - index, template))
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
        identity = str(context.get("identity", "")).strip()
        if identity:
            return identity
        match = re.search(r"(?:identity|character)[:=]\s*([^\n|,]+)", system_text, flags=re.IGNORECASE)
        return match.group(1).strip() if match else "this individual"

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
        return ", and ".join(states[:2]) if states else "I am attentive"

    def _memory_excerpt(self, memory: str) -> str:
        if not memory:
            return "nothing I can honestly retrieve"
        memory = re.sub(r"^I heard you say:\s*", "you said ", memory, flags=re.IGNORECASE)
        memory = " ".join(memory.split())
        if len(memory) > 120:
            memory = memory[:117].rsplit(" ", 1)[0] + "..."
        return memory.rstrip(".")

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
