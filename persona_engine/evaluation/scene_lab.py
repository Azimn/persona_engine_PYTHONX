"""Bounded situated-interaction host for Project Ensemble.

Scene Lab is a sibling host experiment, not a new character authority. The
character engine remains responsible for identity, memory, decisions and
relationships. Scene Lab owns environmental truth, actor placement, visibility,
turn delivery and interruption so language participates in an ongoing causal
situation instead of an abstract chat transcript.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import itertools
import time
from typing import Any, Callable

from persona_engine.core.delivery import SpeechDeliveryReceipt, make_text_delivery_receipt


SCENE_LAB_SCHEMA = "ensemble-scene-lab-v1"


@dataclass
class SceneActor:
    actor_id: str
    display_name: str
    location: str
    present: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "actor_id": self.actor_id,
            "display_name": self.display_name,
            "location": self.location,
            "present": self.present,
            "metadata": dict(self.metadata),
        }


@dataclass
class SceneFact:
    key: str
    value: Any
    visible_to: tuple[str, ...] | None = None
    source: str = "scene_host"

    def visible_for(self, actor_id: str) -> bool:
        return self.visible_to is None or actor_id in self.visible_to

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "visible_to": list(self.visible_to) if self.visible_to is not None else None,
            "source": self.source,
        }


@dataclass
class SceneEvent:
    event_id: str
    kind: str
    actor_id: str | None
    target_id: str | None
    payload: dict[str, Any]
    created_at: float

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "kind": self.kind,
            "actor_id": self.actor_id,
            "target_id": self.target_id,
            "payload": dict(self.payload),
            "created_at": self.created_at,
        }


class SceneLab:
    """Small deterministic host around one or more existing character agents."""

    def __init__(
        self,
        *,
        scene_id: str = "scene-1",
        location: str = "room",
        clock: Callable[[], float] = time.time,
        recent_event_limit: int = 12,
    ):
        self.scene_id = str(scene_id)
        self.location = str(location)
        self.clock = clock
        self.recent_event_limit = max(1, int(recent_event_limit))
        self.actors: dict[str, SceneActor] = {}
        self.facts: dict[str, SceneFact] = {}
        self.events: list[SceneEvent] = []
        self.delivery_receipts: list[SpeechDeliveryReceipt] = []
        self._counter = itertools.count(1)

    def _id(self, prefix: str) -> str:
        return f"{prefix}-{next(self._counter)}"

    def add_actor(self, actor_id: str, display_name: str | None = None, *, location: str | None = None, **metadata) -> SceneActor:
        actor = SceneActor(
            actor_id=str(actor_id),
            display_name=str(display_name or actor_id),
            location=str(location or self.location),
            metadata=dict(metadata),
        )
        self.actors[actor.actor_id] = actor
        self.record_event("actor_entered", actor_id=actor.actor_id, payload={"location": actor.location})
        return actor

    def set_fact(self, key: str, value: Any, *, visible_to=None, source: str = "scene_host") -> SceneFact:
        viewers = None if visible_to is None else tuple(str(value) for value in visible_to)
        fact = SceneFact(str(key), value, viewers, str(source))
        self.facts[fact.key] = fact
        self.record_event("fact_changed", payload={"key": fact.key, "value": fact.value, "visible_to": viewers})
        return fact

    def move_actor(self, actor_id: str, location: str) -> SceneActor:
        actor = self.actors[str(actor_id)]
        before = actor.location
        actor.location = str(location)
        self.record_event(
            "actor_moved",
            actor_id=actor.actor_id,
            payload={"from": before, "to": actor.location},
        )
        return actor

    def set_presence(self, actor_id: str, present: bool) -> None:
        actor = self.actors[str(actor_id)]
        actor.present = bool(present)
        self.record_event(
            "actor_presence",
            actor_id=actor.actor_id,
            payload={"present": actor.present, "location": actor.location},
        )

    def record_event(
        self,
        kind: str,
        *,
        actor_id: str | None = None,
        target_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> SceneEvent:
        event = SceneEvent(
            event_id=self._id("event"),
            kind=str(kind),
            actor_id=str(actor_id) if actor_id is not None else None,
            target_id=str(target_id) if target_id is not None else None,
            payload=dict(payload or {}),
            created_at=float(self.clock()),
        )
        self.events.append(event)
        return event

    def visible_context_for(self, actor_id: str) -> dict[str, Any]:
        actor_id = str(actor_id)
        viewer = self.actors.get(actor_id)
        location = viewer.location if viewer is not None else self.location
        visible_actors = [
            actor.to_dict()
            for actor in self.actors.values()
            if actor.present and actor.location == location
        ]
        visible_facts = {
            fact.key: fact.value
            for fact in self.facts.values()
            if fact.visible_for(actor_id)
        }
        recent_events = [event.to_dict() for event in self.events[-self.recent_event_limit:]]
        return {
            "scene_schema": SCENE_LAB_SCHEMA,
            "scene_id": self.scene_id,
            "location": location,
            "actors_present": visible_actors,
            "visible_facts": visible_facts,
            "recent_scene_events": recent_events,
        }

    def server_truth(self) -> dict[str, Any]:
        return {
            "scene_schema": SCENE_LAB_SCHEMA,
            "scene_id": self.scene_id,
            "facts": {fact.key: fact.value for fact in self.facts.values()},
            "actor_locations": {actor.actor_id: actor.location for actor in self.actors.values()},
            "actor_presence": {actor.actor_id: actor.present for actor in self.actors.values()},
        }

    def deliver_speech(
        self,
        *,
        speaker_id: str,
        target_id: str,
        intended_text: str,
        delivered_text: str | None = None,
        reason: str = "",
    ) -> SpeechDeliveryReceipt:
        intended = str(intended_text or "")
        delivered = intended if delivered_text is None else str(delivered_text)
        speech_id = self._id("speech")
        receipt = make_text_delivery_receipt(
            receipt_id=self._id("receipt"),
            speech_id=speech_id,
            intended_text=intended,
            delivered_text=delivered,
            created_at=float(self.clock()),
            host_ref=self.scene_id,
            reason=reason,
        )
        self.delivery_receipts.append(receipt)
        self.record_event(
            "speech_delivery",
            actor_id=speaker_id,
            target_id=target_id,
            payload=receipt.to_dict(),
        )
        return receipt

    def interrupt_speech(
        self,
        *,
        speaker_id: str,
        target_id: str,
        intended_text: str,
        delivered_characters: int,
        reason: str = "interrupted",
    ) -> SpeechDeliveryReceipt:
        count = max(0, min(len(str(intended_text or "")), int(delivered_characters)))
        return self.deliver_speech(
            speaker_id=speaker_id,
            target_id=target_id,
            intended_text=intended_text,
            delivered_text=str(intended_text or "")[:count],
            reason=reason,
        )

    def character_turn(
        self,
        agent,
        *,
        character_actor_id: str,
        interlocutor_actor_id: str,
        interlocutor_text: str,
        delivered_characters: int | None = None,
    ) -> dict[str, Any]:
        """Run one character turn through the public agent API and host reality.

        The agent receives only the scene context visible to the character plus
        complete server truth through the already-separated host channel. The
        returned expression is an intention until Scene Lab records delivery.
        """

        if character_actor_id not in self.actors or interlocutor_actor_id not in self.actors:
            raise KeyError("both character and interlocutor must be registered scene actors")

        self.record_event(
            "speech_input",
            actor_id=interlocutor_actor_id,
            target_id=character_actor_id,
            payload={"text": str(interlocutor_text)},
        )
        result = agent.say(
            str(interlocutor_text),
            server_truth=self.server_truth(),
            visible_context=self.visible_context_for(character_actor_id),
        )
        intended = str(result.get("response", ""))
        if delivered_characters is None:
            receipt = self.deliver_speech(
                speaker_id=character_actor_id,
                target_id=interlocutor_actor_id,
                intended_text=intended,
            )
        else:
            receipt = self.interrupt_speech(
                speaker_id=character_actor_id,
                target_id=interlocutor_actor_id,
                intended_text=intended,
                delivered_characters=delivered_characters,
            )
        return {
            "scene_schema": SCENE_LAB_SCHEMA,
            "engine_result": result,
            "intended_response": intended,
            "delivery_receipt": receipt.to_dict(),
            "visible_context": self.visible_context_for(character_actor_id),
        }
