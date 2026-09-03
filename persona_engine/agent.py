"""Public character-agent API over the deterministic interior engine."""

from .core.identity import CoreIdentity
from .core.emotion import EmotionalPressure
from .core.engine import InteriorEngine
from .core.symbols import SharedSymbol
from .core.audio_sensor import AudioObservation
from .core.vision_sensor import VisionObservation
from .core.persistence import Persistence, DEFAULT_RUNTIME_DIAGNOSTIC_EVENT_LIMIT
from .core.ensemble_renderer import EnsembleLLMRenderer
from .core.memory import KnowledgeSource, MemoryUnit
from .core.delivery import (
    DeliveryStatus,
    SpeechDeliveryReceipt,
    first_person_delivery_experience,
)
from .core.subject_appraisal import (
    SemanticEventAnnotation,
    SubjectAppraisalContext,
    appraise_subjectively,
)
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

    def prepare_disconnected_transfer(self, target_host_id: str) -> dict:
        return self.engine.prepare_disconnected_transfer(target_host_id)

    @classmethod
    def stage_disconnected_transfer(
        cls,
        bundle: dict,
        *,
        db_path: str,
        host_id: str,
        diagnostic_event_limit: int | None = DEFAULT_RUNTIME_DIAGNOSTIC_EVENT_LIMIT,
    ) -> dict:
        """Stage a whole-subject bundle before constructing the target agent."""
        persistence = Persistence(
            db_path,
            diagnostic_event_limit=diagnostic_event_limit,
            host_id=host_id,
        )
        return persistence.stage_disconnected_transfer(bundle)

    def cancel_disconnected_transfer(self, transfer_uuid: str) -> dict:
        return self.engine.cancel_disconnected_transfer(transfer_uuid)

    def finalize_disconnected_transfer(self, stage_receipt: dict) -> dict:
        return self.engine.finalize_disconnected_transfer(stage_receipt)

    def activate_disconnected_transfer(self, final_receipt: dict) -> dict:
        return self.engine.activate_disconnected_transfer(final_receipt)

    def set_renderer(self, renderer) -> dict:
        """Install an explicit host-selected renderer without changing subject state."""
        self.engine.set_renderer(renderer)
        return self.engine.renderer_status()

    def use_ensemble_renderer(
        self,
        model_name: str,
        *,
        candidate_count: int = 3,
        thinking_mode: str = "off",
        host: str = "http://localhost:11434",
        timeout_seconds: float = 60.0,
        token_budget: int = 256,
        prevalidate_candidates: bool = True,
        include_authored_landmarks: bool = True,
    ) -> dict:
        """Enable Project Ensemble's broadened Ollama realization path.

        Renderer selection is host/runtime policy. It does not alter the
        character cartridge, identity, canonical history, relationships or
        commitments. The returned status makes the active realization mode
        inspectable to callers and evaluation harnesses.
        """
        renderer = EnsembleLLMRenderer(
            model_name=model_name,
            host=host,
            provider="ollama",
            thinking_mode=thinking_mode,
            timeout_seconds=timeout_seconds,
            token_budget=token_budget,
            candidate_count=candidate_count,
            prevalidate_candidates=prevalidate_candidates,
            include_authored_landmarks=include_authored_landmarks,
        )
        self.engine.set_renderer(renderer)
        return self.engine.renderer_status()

    def record_delivery_receipt(
        self,
        receipt: SpeechDeliveryReceipt | dict,
        *,
        record_event: bool = True,
    ) -> dict:
        """Record what actually happened to one intended speech action.

        The engine's renderer output is noncanonical speech evidence. A delivery
        receipt comes from the host/world boundary and tells the subject whether
        that intended speech was fully delivered, interrupted, or not delivered.
        This method turns that actual consequence into lived episodic evidence.
        """
        if isinstance(receipt, dict):
            receipt = SpeechDeliveryReceipt.from_dict(receipt)
        if not isinstance(receipt, SpeechDeliveryReceipt):
            raise TypeError("receipt must be SpeechDeliveryReceipt or dict")

        with self.engine.state_transaction():
            self.engine._require_writer()
            if receipt.status == DeliveryStatus.DELIVERED:
                intensity = 0.05
                valence = 0.0
                unresolved = False
            elif receipt.status == DeliveryStatus.PARTIAL:
                intensity = 0.45
                valence = -0.25
                unresolved = True
            else:
                intensity = 0.35
                valence = -0.20
                unresolved = True

            memory = MemoryUnit(
                content=first_person_delivery_experience(receipt),
                created_at=float(receipt.created_at),
                emotional_valence=valence,
                emotional_intensity=intensity,
                relationship_relevance=0.20,
                identity_relevance=0.05,
                unresolved=unresolved,
                source=KnowledgeSource.OBSERVED,
                tags={
                    "speech_delivery",
                    f"delivery:{receipt.status.value}",
                    f"channel:{receipt.channel}",
                },
            )
            self.engine.memory.add(memory)
            if receipt.status != DeliveryStatus.DELIVERED:
                self.engine.pressures._bump("startle", 0.12 if receipt.status == DeliveryStatus.PARTIAL else 0.08)

            payload = {
                "receipt": receipt.to_dict(),
                "memory_id": memory.id,
                "lived_experience": memory.content,
                "memory_types": ["speech_delivery", "episodic"],
            }
            if record_event:
                self.engine.persistence.log_event(
                    self.engine.identity.name,
                    self.engine.user_id,
                    self.engine.timestep,
                    "speech_delivery_receipt",
                    payload,
                )
            self.engine._persist()
            return payload

    def observe_semantic_event(
        self,
        annotation: SemanticEventAnnotation | dict,
        observed_text: str,
        *,
        goal_preference: float = 0.0,
        identity_sensitivity: float = 0.5,
        perceived_control: float = 0.5,
        record_event: bool = True,
    ) -> dict:
        """Let one typed event leave a subject-relative lived trace.

        The host supplies bounded event semantics rather than free-form authority.
        Existing relationship state and explicit current goal preference determine
        what the event means to this subject. The resulting appraisal then affects
        memory salience and a small set of existing pressure vessels.

        This is a causal consumer for ``SubjectRelativeAppraisal``. It does not
        rewrite the source event, relationship state, identity, or world truth.
        """
        if isinstance(annotation, dict):
            annotation = SemanticEventAnnotation(**annotation)
        if not isinstance(annotation, SemanticEventAnnotation):
            raise TypeError("annotation must be SemanticEventAnnotation or dict")

        with self.engine.state_transaction():
            self.engine._require_writer()
            relationship = self.engine.relationship
            context = SubjectAppraisalContext(
                relationship_importance=max(
                    float(getattr(relationship, "familiarity", 0.0) or 0.0),
                    float(getattr(relationship, "attachment", 0.0) or 0.0),
                ),
                trust=float(getattr(relationship, "trust", 0.5) or 0.0),
                attachment=float(getattr(relationship, "attachment", 0.0) or 0.0),
                guardedness=float(getattr(relationship, "guardedness", 0.0) or 0.0),
                goal_preference=float(goal_preference),
                identity_sensitivity=float(identity_sensitivity),
                perceived_control=float(perceived_control),
            )
            appraisal = appraise_subjectively(annotation, context)
            now = time.time()
            detail = str(observed_text or annotation.topic or annotation.event_type).strip()
            memory = MemoryUnit(
                content=f"I experienced: {detail}",
                created_at=now,
                emotional_valence=appraisal.threat_opportunity,
                emotional_intensity=appraisal.salience,
                relationship_relevance=appraisal.relationship_relevance,
                identity_relevance=appraisal.identity_relevance,
                unresolved=(appraisal.threat_opportunity <= -0.35 and appraisal.salience >= 0.45),
                source=KnowledgeSource.OBSERVED,
                tags={
                    "semantic_event",
                    f"event:{annotation.event_type}",
                    f"meaning:{appraisal.social_meaning}",
                },
            )
            self.engine.memory.add(memory)

            pressure_before = {
                name: pressure.magnitude
                for name, pressure in self.engine.pressures.pressures.items()
            }
            if appraisal.threat_opportunity <= -0.20:
                self.engine.pressures._bump("fear", min(0.30, abs(appraisal.threat_opportunity) * 0.25))
            if annotation.boundary_pressure >= 0.50:
                self.engine.pressures._bump("anger", min(0.22, annotation.boundary_pressure * 0.18))
            if appraisal.social_meaning in {"betrayal", "opposition"}:
                self.engine.pressures._bump("trust_wound", min(0.25, appraisal.salience * 0.20))
            if appraisal.threat_opportunity >= 0.20:
                self.engine.pressures._bump("curiosity", min(0.18, appraisal.threat_opportunity * 0.15))
            if appraisal.social_meaning in {"cooperation", "repair"} and appraisal.relationship_relevance > 0.0:
                self.engine.pressures._bump("attachment", min(0.12, appraisal.relationship_relevance * 0.08))

            payload = {
                "annotation": annotation.to_dict(),
                "appraisal": appraisal.to_dict(),
                "memory_id": memory.id,
                "memory_salience": {
                    "emotional_valence": memory.emotional_valence,
                    "emotional_intensity": memory.emotional_intensity,
                    "relationship_relevance": memory.relationship_relevance,
                    "identity_relevance": memory.identity_relevance,
                    "unresolved": memory.unresolved,
                },
                "pressure_before": pressure_before,
                "pressure_after": {
                    name: pressure.magnitude
                    for name, pressure in self.engine.pressures.pressures.items()
                },
                "memory_types": ["semantic_event", "subject_appraisal", "episodic"],
            }
            if record_event:
                self.engine.persistence.log_event(
                    self.engine.identity.name,
                    self.engine.user_id,
                    self.engine.timestep,
                    "subject_semantic_event",
                    payload,
                )
            self.engine._persist()
            return payload

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
