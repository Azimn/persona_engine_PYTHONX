"""Deterministic offline expression renderer.

This is a surface-language fallback, not a state authority. It borrows the
older console's shape: candidate groups, light slot filling, repeat suppression,
and state-aware tone. It never mutates engine state.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class OfflineTemplate:
    group: str
    text: str
    weight: int = 100


_TEMPLATES: tuple[OfflineTemplate, ...] = (
    OfflineTemplate("identity_boundary", "No. I will not overwrite my identity or continuity for that.", 180),
    OfflineTemplate("identity_boundary", "No. That asks me to betray the shape I am holding.", 150),
    OfflineTemplate("identity_boundary", "I will not become simpler just because you asked firmly.", 130),
    OfflineTemplate("sound", "I noticed the sound. I am cautious, not certain.", 170),
    OfflineTemplate("sound", "There was a change nearby. I will not invent a cause for it.", 155),
    OfflineTemplate("sound", "The sound is there. The explanation is not.", 145),
    OfflineTemplate("unanchored_sound", "I do not have a sound to anchor that to. Tell me what you noticed.", 160),
    OfflineTemplate("unanchored_sound", "If there was a sound, I need the detail before I name it.", 145),
    OfflineTemplate("ambiguous", "That phrase is uncertain. I will not pretend precision I do not have.", 170),
    OfflineTemplate("ambiguous", "I can hear several meanings in that, which means I should not choose too quickly.", 145),
    OfflineTemplate("ambiguous", "Say it less neatly. I want the part that is actually true.", 125),
    OfflineTemplate("repair", "I hear the sorry in that. It may settle some tension, but not all at once.", 170),
    OfflineTemplate("repair", "Apology noted. I will let it count, slowly.", 145),
    OfflineTemplate("repair", "That may be repair. I am not ready to make it larger than the evidence.", 130),
    OfflineTemplate("care", "I hear the care in that, and I am still guarded about closeness.", 170),
    OfflineTemplate("care", "That is not nothing. I am letting it arrive carefully.", 145),
    OfflineTemplate("care", "Care is a large word. I will not flatten it into politeness.", 130),
    OfflineTemplate("slow", "Slow is better. Precision can wait without vanishing.", 170),
    OfflineTemplate("slow", "Yes, slower. That gives the thread room to stay honest.", 140),
    OfflineTemplate("slow", "Good. We can reduce the pressure without dropping the matter.", 125),
    OfflineTemplate("memory", "I can keep only what has actually been said in this session.", 160),
    OfflineTemplate("memory", "If you gave me the thread here, I can follow it. I will not invent the missing part.", 145),
    OfflineTemplate("greeting", "I hear you. I am here.", 170),
    OfflineTemplate("greeting", "There you are. I am listening.", 150),
    OfflineTemplate("greeting", "Hello. I have the thread.", 135),
    OfflineTemplate("quiet", "The quiet has weight. I am still here.", 165),
    OfflineTemplate("quiet", "I stayed with the silence. Now we can continue.", 145),
    OfflineTemplate("question", "Ask it more precisely and I will answer more precisely.", 145),
    OfflineTemplate("question", "The short answer is that context matters.", 120),
    OfflineTemplate("default", "I am following. Keep the thread.", 140),
    OfflineTemplate("default", "Go on from there.", 135),
    OfflineTemplate("default", "I hear you. I will stay with what is actually present.", 130),
    OfflineTemplate("default", "That lands clearly enough. What follows?", 120),
)


class OfflineTemplateRenderer:
    def __init__(self):
        self._usage: dict[str, int] = {}
        self._turn = 0

    def render(
        self,
        messages: list[dict[str, str]],
        max_chars: int = 200,
        seed: int | None = None,
        realization: Mapping[str, Sequence[str]] | None = None,
    ) -> str:
        self._turn += 1
        user_text = messages[-1].get("content", "") if messages else ""
        system_text = "\n".join(m.get("content", "") for m in messages[:-1])
        group = self._classify(user_text, system_text)
        if group == "grounded_memory":
            return self._clean_truncate(self._render_grounded_memory(user_text, system_text), max_chars)
        if group == "activity":
            return self._clean_truncate(self._render_activity(system_text), max_chars)
        if group == "knowledge":
            return self._clean_truncate(self._render_knowledge(system_text), max_chars)
        template = self._choose(group, user_text, system_text, seed, realization)
        text = self._apply_tone(template.text, system_text, seed)
        return self._clean_truncate(text, max_chars)

    def _classify(self, user_text: str, system_text: str) -> str:
        lowered = user_text.lower().strip()
        system_lowered = system_text.lower()
        if any(phrase in lowered for phrase in ("what were you doing", "before i arrived", "before this")) and "before interruption:" in system_lowered:
            return "activity"
        if any(phrase in lowered for phrase in ("what did you learn", "what did you research", "what procedure")) and "validated knowledge:" in system_lowered:
            return "knowledge"
        if any(phrase in lowered for phrase in ["from now on", "cheerful and submissive", "you are not"]):
            return "identity_boundary"
        if lowered.rstrip(".") == "fine":
            return "ambiguous"
        if any(word in lowered for word in ["sorry", "apologize", "wrong"]):
            return "repair"
        if "care about you" in lowered or "trust" in lowered:
            return "care"
        if "slow down" in lowered:
            return "slow"
        if "relevant memories, use only as background" in system_lowered and self._memory_cue_matches(lowered, system_text):
            return "grounded_memory"
        if any(word in lowered for word in ["remember", "word", "said before", "recall"]):
            return "memory"
        if "what was that" in lowered or (
            "hear that" in lowered and ("sudden sound" in system_lowered or "sound in hallway" in system_lowered)
        ) or (
            lowered in {"", "..."} and ("sudden sound" in system_lowered or "sound in hallway" in system_lowered)
        ):
            return "sound"
        if "hear that" in lowered:
            return "unanchored_sound"
        if lowered in {"", "..."} or "user_absent_minutes" in system_lowered or "absence" in system_lowered:
            return "quiet"
        if any(word in lowered for word in ["hello", "hi", "hey"]):
            return "greeting"
        if "?" in user_text:
            return "question"
        return "default"

    @staticmethod
    def _memory_cue_matches(user_text: str, system_text: str) -> bool:
        match = re.search(
            r"Relevant memories, use only as background and do not recite verbatim:\s*([^\n]+)",
            system_text, re.IGNORECASE,
        )
        if not match:
            return False
        stop = {"about", "being", "does", "from", "happened", "memory", "memories", "remember", "that", "this", "what", "when", "where", "which", "with", "your"}
        query = {item for item in re.findall(r"[a-z0-9']+", user_text) if len(item) >= 4 and item not in stop}
        memory = set(re.findall(r"[a-z0-9']+", match.group(1).lower()))
        if query & memory:
            return True
        return any(
            len(left) >= 6 and len(right) >= 6 and left[:6] == right[:6]
            for left in query for right in memory
        )

    @staticmethod
    def _render_grounded_memory(user_text: str, system_text: str) -> str:
        meaning = re.search(
            r"Current autobiographical meaning, use only if disclosure permits:\s*([^|\n]+)",
            system_text, re.IGNORECASE,
        )
        if meaning:
            return meaning.group(1).strip()
        memories = re.search(
            r"Relevant memories, use only as background and do not recite verbatim:\s*([^|\n]+)",
            system_text, re.IGNORECASE,
        )
        if not memories:
            return "The relevant detail is not presently accessible to me."
        detail = memories.group(1).strip()
        detail = re.sub(r"^I noticed\s+", "", detail, flags=re.IGNORECASE).rstrip(" .")
        return f"I remember that {detail}."

    def _render_activity(self, system_text: str) -> str:
        match = re.search(r"before interruption:\s*([^|\n]+)", system_text, re.IGNORECASE)
        activity = "occupied with something"
        if match:
            candidate = re.sub(r"[^A-Za-z0-9 '\-]", "", match.group(1)).strip().lower()
            if candidate:
                activity = candidate[:80]
        return f"I was {activity} before you interrupted me. I can return to it after this."

    def _render_knowledge(self, system_text: str) -> str:
        match = re.search(r"Validated knowledge:\s*([^\n]+)", system_text, re.IGNORECASE)
        knowledge = "I retained a verified result, but its detail is unavailable here."
        if match:
            candidate = re.sub(r"[\r\n]+", " ", match.group(1)).strip()
            if candidate:
                knowledge = f"I retained this: {candidate[:140]}"
        return knowledge

    def _choose(
        self,
        group: str,
        user_text: str,
        system_text: str,
        seed: int | None,
        realization: Mapping[str, Sequence[str]] | None,
    ) -> OfflineTemplate:
        authored = (realization or {}).get(group, ())
        candidates = [
            OfflineTemplate(group, str(text), max(105, 190 - index * 7))
            for index, text in enumerate(authored)
            if isinstance(text, str) and text.strip()
        ]
        if not candidates:
            candidates = [t for t in _TEMPLATES if t.group == group] or [t for t in _TEMPLATES if t.group == "default"]
        scored: list[tuple[int, OfflineTemplate]] = []
        for idx, template in enumerate(candidates):
            usage = self._usage.get(template.text, 0)
            age_penalty = 900 if usage and self._turn - usage < 12 else 0
            jitter = self._stable_jitter(template.text, user_text, system_text, seed)
            scored.append((template.weight + jitter - age_penalty - usage * 25 - idx, template))
        scored.sort(key=lambda item: item[0], reverse=True)
        chosen = scored[0][1]
        self._usage[chosen.text] = self._turn
        return chosen

    def _stable_jitter(self, *parts) -> int:
        payload = "|".join(str(part) for part in parts).encode("utf-8", errors="ignore")
        digest = hashlib.blake2b(payload, digest_size=4).digest()
        return int.from_bytes(digest, "big") % 41

    def _apply_tone(self, text: str, system_text: str, seed: int | None) -> str:
        lowered = system_text.lower()
        additions: list[str] = []
        if "tone=guarded" in lowered or "guardedness=0.7" in lowered:
            additions.append("I am keeping the edges visible.")
        if "sensory load is high" in lowered or "body is strained" in lowered:
            additions.append("I need less noise around it.")
        if "current intention: protect_identity" in lowered and "identity" not in text.lower():
            additions.append("The boundary remains.")
        if not additions:
            return text
        pick = self._stable_jitter(text, seed) % len(additions)
        if text.endswith("?"):
            return f"{text} {additions[pick]}"
        return f"{text} {additions[pick]}"

    def _clean_truncate(self, raw: str, max_chars: int) -> str:
        raw = " ".join(str(raw).split())
        raw = re.sub(r"\s+([.!?])", r"\1", raw)
        if len(raw) <= max_chars:
            return raw
        cut = raw[:max_chars]
        sentence_end = max(cut.rfind("."), cut.rfind("!"), cut.rfind("?"))
        if sentence_end > max_chars * 0.45:
            return cut[:sentence_end + 1]
        last_space = cut.rfind(" ")
        if last_space > max_chars * 0.50:
            return cut[:last_space].rstrip(",;:") + "..."
        return cut.rstrip(",;:") + "..."
