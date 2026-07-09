"""Second-thought fragment selection for streaming interfaces.

Fragments are selected only from already-computed workspace content. The UI must
not invent these fragments.
"""

from __future__ import annotations


def derive_second_thoughts(frame, max_items: int = 2) -> list[str]:
    env = frame.expression_envelope
    fragments: list[str] = []
    if getattr(env, "guardedness", 0.0) > 0.65 and frame.interpretive_beliefs:
        fragments.append(frame.interpretive_beliefs[0])
    if frame.open_loop and getattr(env, "warmth", 0.0) < 0.45:
        fragments.append(frame.open_loop)
    if frame.secondary_pressure and getattr(env, "guardedness", 0.0) > 0.75:
        fragments.append(f"{frame.secondary_pressure} remains in the background")
    return fragments[:max_items]
