"""Avatar-state projection for semi-embodiment hosts.

Avatar projection consumes public organism state and cartridge profile data. It
never reads private raw pressures and never authors memory, belief, or emotion.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class AvatarProfile:
    default_face: str = "neutral"
    guarded_face: str = "guarded"
    tired_face: str = "tired"
    attention_style: str = "still"
    overloaded_face: str = "overloaded"
    restless_motion: str = "subtle_shift"

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "AvatarProfile":
        data = dict(data or {})
        allowed = {field for field in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in allowed})


@dataclass(frozen=True)
class AvatarState:
    face_state: str
    gaze_state: str
    posture_state: str
    attention_state: str
    motion_state: str

    def to_dict(self) -> dict:
        return asdict(self)


class AvatarProjector:
    def __init__(self, profile: AvatarProfile | None = None):
        self.profile = profile or AvatarProfile()

    def project(self, public_status: dict[str, str]) -> AvatarState:
        avatar = public_status.get("avatar_state", self.profile.default_face)
        if avatar == "tired":
            face = self.profile.tired_face
        elif avatar in {"guarded", "tense"}:
            face = self.profile.guarded_face
        elif avatar == "overloaded":
            face = self.profile.overloaded_face
        else:
            face = self.profile.default_face if avatar == "neutral" else avatar
        attention = public_status.get("attention", "none")
        gaze = "toward_user" if attention == "user" else "averted" if avatar in {"guarded", "tense"} else "soft_focus"
        motion = self.profile.restless_motion if public_status.get("movement_need") == "high" else "still"
        return AvatarState(face, gaze, public_status.get("posture", "settled"), attention, motion)


class AvatarEngineAdapter:
    """Host avatar interface. Platform code may implement render()."""

    def render(self, state: AvatarState):
        raise NotImplementedError


class MockAvatarEngine(AvatarEngineAdapter):
    def __init__(self):
        self.rendered: list[AvatarState] = []

    def render(self, state: AvatarState):
        self.rendered.append(state)
        return {"rendered": True, "state": state.to_dict()}
