"""Public character-agent API over the deterministic interior engine."""

from .core.identity import CoreIdentity
from .core.emotion import EmotionalPressure
from .core.engine import InteriorEngine
from .core.symbols import SharedSymbol
from .core.audio_sensor import AudioObservation
from .core.vision_sensor import VisionObservation
import time


class CharacterAgent:
    """Thin public API. All real mechanics live in InteriorEngine."""

    def __init__(self, identity: CoreIdentity | None = None, user_id: str = "default_user", db_path: str = "persona_state.db", cartridge_path: str | None = None):
        self.engine = InteriorEngine(identity, user_id=user_id, db_path=db_path, cartridge_path=cartridge_path)

    def add_pressure(self, name: str, magnitude: float, inhibition_strength: float = 0.5, trigger_sensitivity: float = 1.0):
        self.engine.pressures.add(EmotionalPressure(name, magnitude, inhibition_strength, trigger_sensitivity))
        self.engine._persist()

    def add_symbol(self, name: str, meaning: str, emotional_charge: float = 0.5, stability: float = 0.5):
        now = time.time()
        self.engine.symbols.add(SharedSymbol(name, meaning, now, emotional_charge, now, stability))
        self.engine._persist()

    def say(self, text: str, server_truth: dict | None = None, visible_context: dict | None = None,
            event_time: float | None = None) -> dict:
        return self.engine.receive_input(text, server_truth=server_truth, visible_context=visible_context, event_time=event_time)

    def dream(self, min_interval_seconds: int = 3600) -> list[str]:
        return self.engine.dream(min_interval_seconds=min_interval_seconds)

    def export_snapshot(self):
        return self.engine.export_session_snapshot()

    def import_snapshot(self, snapshot):
        self.engine.import_session_snapshot(snapshot)

    def public_status(self) -> dict:
        return self.engine.public_status()

    def debug_snapshot(self) -> dict:
        return self.engine.debug_snapshot()

    def poll_proactive_events(self) -> list[dict]:
        return self.engine.poll_proactive_events()

    def stream_last_response(self, text: str):
        """Convenience API for UIs that want timed chunk output.

        This builds a normal turn first so all deterministic state transitions
        occur, then streams a renderer response using the resulting envelope.
        For full production use, call InteriorEngine directly so you can stream
        the exact same prompt before post-writeback.
        """
        result = self.engine.receive_input(text)
        for chunk in self.engine.renderer.generate_stream([{"role": "user", "content": text}], max_chars=len(result["response"]) + 8):
            yield chunk


    def observe_audio(self, observation: AudioObservation | dict) -> dict:
        if isinstance(observation, dict):
            observation = AudioObservation(**observation)
        return self.engine.ingest_audio_observation(observation)

    def observe_vision(self, observation: VisionObservation | dict) -> dict:
        if isinstance(observation, dict):
            observation = VisionObservation(**observation)
        return self.engine.ingest_vision_observation(observation)

    def propose_world_action(self, action_type: str, payload: dict | None = None, event_time: float | None = None) -> dict:
        return self.engine.propose_world_action(action_type, payload, event_time=event_time)

    def plan_voice(self, text: str) -> dict:
        return self.engine.plan_voice(text)

    def avatar_projection(self) -> dict:
        return self.engine.avatar_projection()

    def idle(self):
        self.engine.run_idle_cycle()

    def record_world_event(self, **kwargs):
        event = self.engine.record_world_event(**kwargs)
        self.engine._persist()
        return event.to_dict()

    def perceive_world_event(self, event_id: str, **kwargs):
        experience = self.engine.perceive_world_event(event_id, **kwargs)
        return experience.to_dict() if experience else None

    def force_life_event(self, category: str):
        return self.engine.force_life_event(category)

    def attempt_imperfect_action(self, **kwargs):
        return self.engine.attempt_imperfect_action(**kwargs)

    def start_background_idle(self, interval_seconds: float = 30.0):
        self.engine.start_background_idle(interval_seconds)

    def stop_background_idle(self):
        self.engine.stop_background_idle()
