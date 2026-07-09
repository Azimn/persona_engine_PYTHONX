"""Layer 1: situated interface state.

This is deliberately not a "body" requirement. For a text-only character it
tracks channel, observable facts, available actions, timing, and access rules so
expression stays perspective-locked instead of narrator-like.
"""

from dataclasses import dataclass, field
from typing import List
import time


@dataclass
class InterfaceEvent:
    kind: str
    content: str
    observed_at: float


@dataclass
class SituatedInterfaceState:
    channel: str = "text"
    action_affordances: List[str] = field(default_factory=lambda: ["reply_text", "remain_silent", "ask_question"])
    visible_context: List[str] = field(default_factory=list)
    observed_events: List[InterfaceEvent] = field(default_factory=list)
    last_input_at: float = 0.0
    last_output_at: float = 0.0

    def observe_text(self, text: str, now: float | None = None):
        now = now or time.time()
        self.last_input_at = now
        self.observed_events.append(InterfaceEvent("user_text", text[:240], now))
        self.observed_events = self.observed_events[-40:]

    def mark_output(self, now: float | None = None):
        self.last_output_at = now or time.time()

    def summary(self, now: float | None = None) -> str:
        now = now or time.time()
        silence = max(0.0, now - max(self.last_input_at, self.last_output_at, 0.0))
        if silence > 3600:
            silence_text = "A long silence has passed."
        elif silence > 300:
            silence_text = "Several minutes of silence have passed."
        elif silence > 30:
            silence_text = "A short silence has passed."
        else:
            silence_text = "The exchange is immediate."
        afford = ", ".join(self.action_affordances)
        return f"Channel is {self.channel}. Available actions: {afford}. {silence_text}"

    def access_rules(self) -> str:
        return (
            "Only use the current user text, retrieved memories, shared symbols, "
            "open loops, and interface observations. Do not claim unseen events, "
            "private user thoughts, hidden motives, or memories outside the frame."
        )
