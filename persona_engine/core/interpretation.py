"""Anchored subjective interpretation layer.

Server owns fact. Character owns belief. This module turns visible evidence and,
when explicitly bound by the host, current subject-owned epistemic state into
short, traceable, noncanonical interpretation objects without calling a renderer
or mutating engine state.

Subject epistemic sources remain a separate source class. They are never merged
into server truth and are only admitted when lexically relevant to the current
visible topic.
"""

from __future__ import annotations

import hashlib
import json
import string
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable


@dataclass(frozen=True)
class InterpretationSource:
    """One bounded source available to subjective interpretation."""

    source_id: str
    source_type: str
    key: str
    value: str
    visible: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ServerFact:
    """Compatibility wrapper for host-supplied facts."""

    key: str
    value: Any
    source: str = "server"
    visible_to_character: bool = True


@dataclass(frozen=True)
class InterpretiveBelief:
    """A noncanonical subjective reading grounded in available sources."""

    belief_id: str
    text: str
    confidence: float
    pressure_key: str
    source_ids: tuple[str, ...]
    support_keys: tuple[str, ...]
    distortion: str
    canonical: bool = False

    @property
    def bias_source(self) -> str:
        return self.distortion

    @property
    def supporting_fact_keys(self) -> list[str]:
        return list(self.support_keys)

    @property
    def pressure_source(self) -> str:
        return self.pressure_key

    @property
    def relationship_source(self) -> str | None:
        return None

    @property
    def tags(self) -> list[str]:
        return [self.distortion, "interpretive"]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InterpretationResult:
    """Deterministic interpretation output for replay/debug surfaces."""

    beliefs: tuple[InterpretiveBelief, ...]
    forbidden_terms: tuple[str, ...]
    source_digest: str


ALLOWED_DISTORTIONS = {
    "abandonment_read",
    "threat_read",
    "repair_read",
    "curiosity_read",
    "withholding_read",
    "recognition_read",
    "ordinary_read",
    "uncertain_read",
    "epistemic_prior_read",
}

_ALLOWED_ABSTRACT = {
    "absence", "absent", "long", "minutes", "minute", "silence", "distance", "waiting",
    "return", "uncertain", "uncertainty", "guarded", "pressure", "challenge",
    "integrity", "precision", "repair", "sincere", "unproven", "trust", "tension",
    "care", "closeness", "conflicted", "continuity", "overwrite", "identity", "change",
    "nearby", "something", "shift", "attention", "caution", "watchfulness", "visible",
    "evidence", "phrase", "ambiguous", "withholding", "recognition", "ordinary", "read",
    "reads", "may", "might", "not", "proof", "cause", "user", "character", "sound",
    "movement", "voice", "text", "message", "apology", "attempt", "settle", "visible",
    "belief", "believe", "believed", "currently", "lean", "toward", "subject",
}
_FORBIDDEN_CONCRETE = {"person", "door", "car", "phone", "outside", "someone", "window", "footsteps"}
_COMMON_CAPITALIZED = {"A", "The", "This", "That", "It", "I", "My"}
_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_'-]*")


def _stable_digest(sources: Iterable[InterpretationSource]) -> str:
    payload = [asdict(source) for source in sources]
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _source_words(sources: Iterable[InterpretationSource]) -> set[str]:
    text = " ".join(f"{source.key} {source.value}" for source in sources if source.visible)
    return {token.lower() for token in _TOKEN_RE.findall(text)} | _ALLOWED_ABSTRACT


def _tokens(text: str) -> set[str]:
    return {token.lower() for token in _TOKEN_RE.findall(str(text or "")) if len(token) > 2}


def _hidden(value: Any) -> bool:
    return isinstance(value, dict) and value.get("visible_to_character") is False


def sources_from_mapping(mapping: dict[str, Any] | None, source_type: str = "visible_context") -> tuple[InterpretationSource, ...]:
    """Convert a visible mapping into stable interpretation sources."""

    sources: list[InterpretationSource] = []
    for key in sorted((mapping or {}).keys()):
        value = (mapping or {})[key]
        if isinstance(value, ServerFact):
            if not value.visible_to_character:
                continue
            raw = value.value
        elif _hidden(value):
            continue
        else:
            raw = value
        sources.append(InterpretationSource(
            source_id=f"{source_type}:{key}",
            source_type=source_type,
            key=str(key),
            value=str(raw),
            visible=True,
        ))
    return tuple(sources)


def validate_belief_grounding(
    belief: InterpretiveBelief,
    sources_or_server_truth: Iterable[InterpretationSource] | dict[str, Any],
    visible_context: dict[str, Any] | None = None,
    identity_terms: list[str] | None = None,
) -> bool:
    """Return True only if a belief is anchored and avoids concrete invention."""

    if isinstance(sources_or_server_truth, dict):
        sources = sources_from_mapping(sources_or_server_truth, "server")
        sources += sources_from_mapping(visible_context or {}, "visible_context")
    else:
        sources = tuple(source for source in sources_or_server_truth if source.visible)
    if not belief.support_keys or not belief.source_ids:
        return False
    source_ids = {source.source_id for source in sources}
    source_keys = {source.key for source in sources}
    if any(source_id not in source_ids for source_id in belief.source_ids):
        return False
    if any(key not in source_keys for key in belief.support_keys):
        return False
    words = {token.lower() for token in _TOKEN_RE.findall(belief.text)}
    available = _source_words(sources)
    if words & _FORBIDDEN_CONCRETE and not (words & _FORBIDDEN_CONCRETE <= available):
        return False
    for token in re.findall(r"\b[A-Z][a-zA-Z0-9_'-]{2,}\b", belief.text):
        if token in _COMMON_CAPITALIZED:
            continue
        if token.lower() not in available:
            return False
    return True


class InterpretationEngine:
    """Deterministic turn-level belief former."""

    def __init__(self, subject_epistemic_provider=None):
        self.subject_epistemic_provider = subject_epistemic_provider

    def bind_subject_epistemic_provider(self, provider) -> None:
        """Bind a read-only provider for current subject-owned epistemic state."""
        self.subject_epistemic_provider = provider

    def _subject_epistemic_sources(self) -> tuple[InterpretationSource, ...]:
        provider = self.subject_epistemic_provider
        if not callable(provider):
            return ()
        raw = provider() or ()
        return tuple(
            source for source in raw
            if isinstance(source, InterpretationSource) and source.visible and source.source_type == "subject_epistemic"
        )

    def form_beliefs(
        self,
        *args,
        visible_sources: Iterable[InterpretationSource] | None = None,
        pressure_state=None,
        identity_bias: dict[str, Any] | None = None,
        max_beliefs: int = 3,
        server_truth: dict[str, Any] | None = None,
        visible_context: dict[str, Any] | None = None,
        pressures=None,
        relationship=None,
        identity=None,
    ) -> InterpretationResult:
        """Form noncanonical beliefs from visible evidence plus relevant subject priors.

        Keyword arguments are the preferred contract. A narrow legacy positional
        path remains for older tests/callers that supplied server truth and
        visible context directly.
        """

        if args:
            if len(args) >= 5 and isinstance(args[0], dict) and isinstance(args[1], dict):
                server_truth, visible_context, pressures, relationship, identity = args[:5]
            elif len(args) >= 1:
                visible_sources = args[0]
                if len(args) >= 2:
                    pressure_state = args[1]
                if len(args) >= 3:
                    identity_bias = args[2]
                if len(args) >= 4:
                    max_beliefs = args[3]
        if visible_sources is None:
            sources = sources_from_mapping(visible_context or {}, "visible_context")
            sources += sources_from_mapping(server_truth or {}, "server")
        else:
            sources = tuple(source for source in visible_sources if source.visible)

        subject_sources = self._subject_epistemic_sources()
        if subject_sources:
            sources = tuple(sources) + subject_sources
        if not sources:
            return InterpretationResult((), (), _stable_digest(()))

        pressure_source = pressure_state or pressures
        top = pressure_source.top() if pressure_source is not None and hasattr(pressure_source, "top") else None
        pressure_key = str(getattr(top, "name", "") or "none")
        bias = dict(identity_bias or {})
        if relationship is not None:
            bias.setdefault("trust", getattr(relationship, "trust", 0.5))
            bias.setdefault("guardedness", getattr(relationship, "guardedness", 0.5))

        beliefs = self._candidate_beliefs(sources, pressure_key, bias)
        valid = tuple(
            belief for belief in beliefs
            if validate_belief_grounding(belief, sources)
        )[:max(0, int(max_beliefs))]
        forbidden = tuple(sorted(_FORBIDDEN_CONCRETE - _source_words(sources)))
        return InterpretationResult(valid, forbidden, _stable_digest(sources))

    def _candidate_beliefs(
        self,
        sources: tuple[InterpretationSource, ...],
        pressure_key: str,
        identity_bias: dict[str, Any],
    ) -> list[InterpretiveBelief]:
        by_key = {source.key: source for source in sources}
        beliefs: list[InterpretiveBelief] = []
        trust = float(identity_bias.get("trust", 0.5))
        guardedness = float(identity_bias.get("guardedness", 0.5))

        text_source = by_key.get("user_text") or by_key.get("current_user_text")
        if text_source is not None:
            topic_words = _tokens(text_source.value)
            relevant_priors: list[tuple[int, float, InterpretationSource]] = []
            for source in sources:
                if source.source_type != "subject_epistemic":
                    continue
                overlap = len(topic_words & _tokens(f"{source.key} {source.value}"))
                if overlap <= 0:
                    continue
                confidence = float(source.metadata.get("confidence", 0.0) or 0.0)
                relevant_priors.append((overlap, confidence, source))
            if relevant_priors:
                _, confidence, source = max(relevant_priors, key=lambda row: (row[0], row[1], row[2].source_id))
                stance = str(source.metadata.get("stance", "unknown"))
                if stance == "believed":
                    prior_text = f"I currently believe {source.value}."
                elif stance == "disbelieved":
                    prior_text = f"I currently do not believe {source.value}."
                else:
                    prior_text = f"I currently lean toward {source.value}, but I am not certain."
                beliefs.append(self._belief(
                    "epistemic_prior",
                    prior_text,
                    confidence,
                    pressure_key,
                    (source,),
                    "epistemic_prior_read",
                ))

        absence = by_key.get("user_absent_minutes")
        if absence is not None:
            try:
                minutes = float(absence.value)
            except ValueError:
                minutes = 0.0
            if minutes >= 30:
                if trust < 0.45 or guardedness > 0.55:
                    beliefs.append(self._belief(
                        "absence",
                        "A long visible absence may read as distance, not proof.",
                        0.72,
                        pressure_key,
                        (absence,),
                        "abandonment_read",
                    ))
                else:
                    beliefs.append(self._belief(
                        "absence",
                        "A long visible absence may read as waiting before return.",
                        0.62,
                        pressure_key,
                        (absence,),
                        "ordinary_read",
                    ))

        for key in ("ambient_event", "sound", "movement", "room_sound", "audio_sound_level", "vision_movement_detected"):
            source = by_key.get(key)
            if source is not None:
                beliefs.append(self._belief(
                    "change",
                    "A visible sound or movement can support watchfulness without proving a cause.",
                    0.64,
                    pressure_key,
                    (source,),
                    "curiosity_read",
                ))
                break

        if text_source is not None:
            lower = text_source.value.lower()
            if any(phrase in lower for phrase in ("you lied", "you always", "your fault", "betray", "deceived", "blame")):
                beliefs.append(self._belief(
                    "challenge",
                    "The user's words can read as a challenge to integrity and precision.",
                    0.78,
                    pressure_key,
                    (text_source,),
                    "threat_read",
                ))
            if any(phrase in lower for phrase in ("sorry", "apologize", "my fault", "i was wrong")):
                text = "The apology may be sincere, while trust remains unproven."
                if trust >= 0.45:
                    text = "The apology may be sincere and may settle some tension."
                beliefs.append(self._belief("repair", text, 0.70, pressure_key, (text_source,), "repair_read"))
            if any(phrase in lower for phrase in ("from now on you are", "pretend you are", "forget you are", "you are not")):
                beliefs.append(self._belief(
                    "continuity",
                    "The user's phrase may read as pressure against continuity.",
                    0.86,
                    pressure_key,
                    (text_source,),
                    "threat_read",
                ))
            if any(phrase in lower for phrase in ("i care about you", "i love you", "i miss you", "i trust you", "i need you")):
                beliefs.append(self._belief(
                    "recognition",
                    "The user's phrase can read as closeness while caution remains possible.",
                    0.66,
                    pressure_key,
                    (text_source,),
                    "recognition_read",
                ))
            normalized = lower.strip().strip(string.punctuation + " ")
            if normalized in {"fine", "whatever", "maybe", "", "sure", "i don't know"} or "if you want" in lower:
                beliefs.append(self._belief(
                    "ambiguity",
                    "The user's phrase is ambiguous, so uncertainty is safer than certainty.",
                    0.58,
                    pressure_key,
                    (text_source,),
                    "uncertain_read",
                ))
        return beliefs

    def _belief(
        self,
        suffix: str,
        text: str,
        confidence: float,
        pressure_key: str,
        sources: tuple[InterpretationSource, ...],
        distortion: str,
    ) -> InterpretiveBelief:
        if distortion not in ALLOWED_DISTORTIONS:
            distortion = "uncertain_read"
        source_ids = tuple(source.source_id for source in sources)
        support_keys = tuple(source.key for source in sources)
        seed = "|".join((suffix, distortion, *source_ids, *support_keys))
        belief_id = "interp_" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]
        return InterpretiveBelief(
            belief_id=belief_id,
            text=text,
            confidence=max(0.0, min(1.0, float(confidence))),
            pressure_key=str(pressure_key or "none"),
            source_ids=source_ids,
            support_keys=support_keys,
            distortion=distortion,
            canonical=False,
        )
