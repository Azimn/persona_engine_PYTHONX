"""Public character-agent API over the deterministic interior engine."""

from .core.identity import CoreIdentity
from .core.emotion import EmotionalPressure
from .core.engine import InteriorEngine
from .core.symbols import SharedSymbol
from .core.audio_sensor import AudioObservation
from .core.vision_sensor import VisionObservation
from .core.persistence import DEFAULT_RUNTIME_DIAGNOSTIC_EVENT_LIMIT
import time


class CharacterAgent:
    """Thin public API. All real mechanics live in InteriorEngine."""

    def __init__(self, identity: CoreIdentity | None = None, user_id: str = "default_user", db_path: str = "persona_state.db", cartridge_path: str | None = None, diagnostic_event_limit: int | None = DEFAULT_RUNTIME_DIAGNOSTIC_EVENT_LIMIT, host_id: str = "local"):
        self.engine = InteriorEngine(identity, user_id=user_id, db_path=db_path, cartridge_path=cartridge_path, diagnostic_event_limit=diagnostic_event_limit, host_id=host_id)

    def writer_status(self) -> dict:
        return self.engine.writer_status()

    def handoff_writer(self, target_host_id: str) -> dict:
        return self.engine.handoff_writer(target_host_id)

    def accept_writer_handoff(self, receipt: dict) -> dict:
        return self.engine.accept_writer_handoff(receipt)

    def add_pressure(self, name: str, magnitude: float, inhibition_strength: float = 0.5, trigger_sensitivity: float = 1.0):
        with self.engine.state_transaction():
            self.engine._require_writer()
            self.engine.pressures.add(EmotionalPressure(name, magnitude, inhibition_strength, trigger_sensitivity))
            self.engine._persist()

    def add_symbol(self, name: str, meaning: str, emotional_charge: float = 0.5, stability: float = 0.5):
        with self.engine.state_transaction():
            self.engine._require_writer()
            now = time.time()
            self.engine.symbols.add(SharedSymbol(name, meaning, now, emotional_charge, now, stability))
            self.engine._persist()

    def adopt_commitment(self, commitment_kind: str, commitment_target: str, *, record_event: bool = True) -> dict:
        """Adopt explicit semantic commitment state through character authority.

        Conversational text does not invoke this method by itself.
        """
        return self.engine.adopt_commitment(
            commitment_kind,
            commitment_target,
            record_event=record_event,
            persist=True,
        )

    def say(self, text: str, server_truth: dict | None = None, visible_context: dict | None = None) -> dict:
        return self.engine.receive_input(text, server_truth=server_truth, visible_context=visible_context)

    def dream(self, min_interval_seconds: int = 3600, *, record_event: bool = True) -> list[str]:
        return self.engine.dream(min_interval_seconds=min_interval_seconds, record_event=record_event)

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
        """Chunk the exact finalized response from one canonical turn.

        The legacy implementation rendered a second time after state writeback,
        so streamed wording could differ from the speech evidence that actually
        caused the turn consequences. This helper now performs one normal turn
        and streams only that validated final text. It never re-enters the
        renderer after the turn commits.
        """
        result = self.engine.receive_input(text)
        response = result["response"]
        chunk_chars = 32
        for start in range(0, len(response), chunk_chars):
            yield response[start:start + chunk_chars]


    def observe_audio(self, observation: AudioObservation | dict) -> dict:
        if isinstance(observation, dict):
            observation = AudioObservation(**observation)
        return self.engine.ingest_audio_observation(observation)

    def observe_vision(self, observation: VisionObservation | dict) -> dict:
        if isinstance(observation, dict):
            observation = VisionObservation(**observation)
        return self.engine.ingest_vision_observation(observation)

    def propose_world_action(self, action_type: str, payload: dict | None = None) -> dict:
        return self.engine.propose_world_action(action_type, payload)

    def plan_voice(self, text: str) -> dict:
        return self.engine.plan_voice(text)

    def avatar_projection(self) -> dict:
        return self.engine.avatar_projection()

    def idle(self):
        self.engine.run_idle_cycle()

    def advance_time(self, elapsed_seconds: float, *, source: str = "explicit", record_event: bool = True) -> dict:
        """Advance canonical subject time without requiring a wall-clock wait."""
        return self.engine.advance_time(elapsed_seconds, source=source, record_event=record_event)

    def start_background_idle(self, interval_seconds: float = 30.0):
        self.engine.start_background_idle(interval_seconds)

    def stop_background_idle(self):
        self.engine.stop_background_idle()
