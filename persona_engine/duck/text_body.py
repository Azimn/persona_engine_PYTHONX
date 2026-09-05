"""Reference text-channel embodiment for DUCK.

A text interface is treated as one body, not as the cognitive architecture. It
owns a text-input sensor and communication effector, records exactly what was
delivered, and can later be replaced by a game, XR, desktop, voice, or robot
body without replacing the subject.
"""

from __future__ import annotations

from collections import deque
from typing import Any

from persona_engine.core.delivery import make_text_delivery_receipt

from .embodiment_port import Affordance, BodySnapshot, EmbodimentOutcome


class TextChannelEmbodimentPort:
    def __init__(self, body_id: str = "text-channel", *, channel: str = "text", host_ref: str = "local"):
        self.body_id = str(body_id)
        self.channel = str(channel)
        self.host_ref = str(host_ref)
        self._inbox: deque[dict[str, Any]] = deque()
        self.outbox: list[dict[str, Any]] = []

    def snapshot(self) -> BodySnapshot:
        return BodySnapshot(
            body_id=self.body_id,
            location="conversation_interface",
            orientation="toward_interlocutor",
            sensors=("text_input",),
            effectors=("communicate", "wait"),
            state={"channel": self.channel, "pending_inputs": len(self._inbox)},
        )

    def push_user_message(self, text: str, *, utc_epoch: float | None = None, source: str = "user") -> None:
        payload = {
            "kind": "user_message",
            "source": str(source),
            "payload": {
                "description": str(text),
                "observed_text": str(text),
                "salience": 0.90,
                "self_relevance": 0.70,
            },
        }
        if utc_epoch is not None:
            payload["utc_epoch"] = float(utc_epoch)
        self._inbox.append(payload)

    def observe(self, *, tick: int) -> list[dict[str, Any]]:
        del tick
        values = list(self._inbox)
        self._inbox.clear()
        return values

    def affordances(self) -> list[Affordance]:
        return [
            Affordance(
                "communicate",
                confidence=1.0,
                cost=0.02,
                risk=0.04,
                uncertainty=0.08,
                expected_world_effects={"social_contact": 0.25, "conversation_progress": 0.25},
                expected_self_effects={"drive:affiliation": 0.12},
            ),
            Affordance("wait", confidence=1.0, cost=0.0, risk=0.0, uncertainty=0.0),
        ]

    def supports(self, action_type: str) -> bool:
        return action_type in {"communicate", "wait"}

    def execute(self, action, simulation, context):
        if action.action_type == "wait":
            return EmbodimentOutcome(True, "waited", dict(simulation.predicted_world_effects), dict(simulation.predicted_self_effects))
        if action.action_type != "communicate":
            return EmbodimentOutcome(False, "unsupported_effector", {"execution_rejected": 1.0}, {})
        text = str(action.parameters.get("utterance", "")).strip()
        if not text:
            return EmbodimentOutcome(False, "empty_utterance", {"execution_rejected": 1.0}, {})
        speech_id = str(action.parameters.get("speech_id") or f"speech:{context.get('tick', 0)}:{action.action_id}")
        trigger = context.get("trigger", {}) if isinstance(context, dict) else {}
        created_at = float(trigger.get("timestamp", context.get("tick", 0.0)) if isinstance(trigger, dict) else context.get("tick", 0.0))
        receipt = make_text_delivery_receipt(
            receipt_id=f"receipt:{speech_id}",
            speech_id=speech_id,
            intended_text=text,
            delivered_text=text,
            created_at=created_at,
            channel=self.channel,
            host_ref=self.host_ref,
        )
        record = {
            "speech_id": speech_id,
            "text": text,
            "tick": int(context.get("tick", 0)),
            "receipt": receipt.to_dict(),
        }
        self.outbox.append(record)
        world = dict(simulation.predicted_world_effects)
        world.setdefault("social_contact", 0.25)
        self_effects = dict(simulation.predicted_self_effects)
        self_effects.setdefault("drive:affiliation", 0.12)
        return EmbodimentOutcome(
            True,
            "delivered_text",
            world,
            self_effects,
            metadata={"speech_delivery_receipt": receipt.to_dict(), "rendered_text": text, "speech_id": speech_id},
        )

    def latest_output(self) -> dict[str, Any] | None:
        return dict(self.outbox[-1]) if self.outbox else None
