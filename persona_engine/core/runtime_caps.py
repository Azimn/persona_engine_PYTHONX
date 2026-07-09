"""Runtime capability profiles for PC, mobile, and constrained hosts.

Capabilities are declarative. They do not enable hardware directly. Host apps
use them to decide which adapters to attach.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class RuntimeCapabilities:
    microphone: bool = False
    camera: bool = False
    tts: bool = False
    avatar: bool = False
    network: bool = False
    gpu: bool = False
    mobile_safe: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


def pc_local_profile() -> RuntimeCapabilities:
    return RuntimeCapabilities(microphone=True, camera=True, tts=True, avatar=True, network=False, gpu=False, mobile_safe=False)


def mobile_local_profile() -> RuntimeCapabilities:
    return RuntimeCapabilities(microphone=True, camera=True, tts=True, avatar=True, network=False, gpu=False, mobile_safe=True)


def headless_test_profile() -> RuntimeCapabilities:
    return RuntimeCapabilities(mobile_safe=True)
