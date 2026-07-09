"""Layer 2: affective pressure vessels.

Pressures have different decay rates, trigger maps, and self-access. Self-access
prevents the frame from over-explaining internal state to the renderer.
"""

import time
from dataclasses import dataclass
from typing import Dict, Optional

DECAY_PROFILES = {
    "shame": 0.02,
    "grief": 0.005,
    "startle": 0.25,
    "curiosity": 0.08,
    "anger": 0.04,
    "fear": 0.03,
    "attachment": 0.01,
    "trust_wound": 0.01,
    "default": 0.05,
}
TRIGGER_MAPS = {
    "shame": ["you failed", "you always mess", "not good enough", "disappoint", "mirror", "lied"],
    "grief": ["gone", "lost", "never again", "goodbye"],
    "anger": ["accuse", "blame", "unfair", "betray", "fault"],
    "fear": ["threat", "hurt you", "leave you", "abandon", "delete"],
    "attachment": ["stay", "don't go", "need you", "miss you", "care about you"],
    "curiosity": ["why", "what if", "new", "different"],
}
SELF_ACCESS = {
    "shame": 0.35,
    "fear": 0.45,
    "anger": 0.70,
    "curiosity": 0.85,
    "attachment": 0.40,
    "grief": 0.30,
    "default": 0.60,
}


@dataclass
class EmotionalPressure:
    name: str
    magnitude: float
    inhibition_strength: float = 0.5
    trigger_sensitivity: float = 1.0
    last_triggered: float = 0.0
    self_access: float | None = None

    def decay_rate(self) -> float:
        return DECAY_PROFILES.get(self.name, DECAY_PROFILES["default"])

    def accessible_name(self) -> str:
        access = self.self_access if self.self_access is not None else SELF_ACCESS.get(self.name, SELF_ACCESS["default"])
        if access < 0.4:
            return "vague unease"
        if access < 0.6:
            return f"partly understood {self.name}"
        return self.name


class PressureSystem:
    def __init__(self):
        self.pressures: Dict[str, EmotionalPressure] = {}

    def add(self, p: EmotionalPressure):
        if p.self_access is None:
            p.self_access = SELF_ACCESS.get(p.name, SELF_ACCESS["default"])
        self.pressures[p.name] = p

    def ensure(self, name: str) -> EmotionalPressure:
        p = self.pressures.get(name)
        if p is None:
            p = EmotionalPressure(name=name, magnitude=0.0, self_access=SELF_ACCESS.get(name, SELF_ACCESS["default"]))
            self.add(p)
        return p

    def decay_all(self, dt_steps: int = 1):
        for p in self.pressures.values():
            p.magnitude = max(0.0, p.magnitude - p.decay_rate() * dt_steps)

    def top(self) -> Optional[EmotionalPressure]:
        active = [p for p in self.pressures.values() if p.magnitude > 0.001]
        if not active:
            return None
        return max(active, key=lambda p: p.magnitude)

    def runner_up(self) -> Optional[EmotionalPressure]:
        ordered = sorted([p for p in self.pressures.values() if p.magnitude > 0.001], key=lambda p: p.magnitude, reverse=True)
        return ordered[1] if len(ordered) > 1 else None

    def trigger_match(self, text: str) -> float:
        lowered = text.lower()
        match = 1.0
        for name, words in TRIGGER_MAPS.items():
            pressure = self.pressures.get(name)
            if pressure and any(w in lowered for w in words):
                match = max(match, 1.0 + pressure.trigger_sensitivity * 0.5)
        return match

    def apply_appraisal(self, appraisal, trust: float):
        if appraisal.accusation > 0.5:
            self._bump("shame", appraisal.accusation * 0.45)
            self._bump("anger", appraisal.accusation * 0.30)
            self._bump("trust_wound", appraisal.accusation * 0.20)
        if appraisal.threat > 0.5:
            self._bump("fear", appraisal.threat * 0.60)
            self._bump("anger", appraisal.threat * 0.20)
        if appraisal.repair_attempt > 0.5:
            self._bump("curiosity", 0.10)
            self._bump("shame", -0.12)
            self._bump("fear", -0.08)
        if appraisal.kindness > 0.5:
            self._bump("attachment", appraisal.kindness * 0.08)
            self._bump("curiosity", 0.05)
        if appraisal.intimacy_bid > 0.5:
            self._bump("attachment", appraisal.intimacy_bid * 0.35)
            if trust < 0.4:
                self._bump("fear", 0.20)
        if appraisal.boundary_violation > 0.5:
            self._bump("anger", 0.25)
            self._bump("fear", 0.20)

    def _bump(self, name: str, delta: float):
        p = self.ensure(name)
        p.magnitude = max(0.0, min(1.0, p.magnitude + delta))
        if delta > 0:
            p.last_triggered = time.time()
