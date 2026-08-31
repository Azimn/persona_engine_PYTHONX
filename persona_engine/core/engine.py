"""Interior engine.

Pipeline:
Input -> wall-clock catch-up -> identity guard -> appraisal -> relationship and
pressure update -> interpretation -> memory retrieval -> intention/open-loop/habit selection ->
workspace frame -> renderer -> validator -> canonical writeback -> event-log persistence.
"""

import json
import time
import threading
from contextlib import contextmanager
from functools import wraps
from dataclasses import asdict, dataclass
from typing import Any

from .emotion import EmotionalPressure, PressureSystem
from .belief_ledger import BeliefLedger
from .cognition_schemas import turn_seed
from .cartridge import load_cartridge
from .deception_ledger import DeceptionLedger
from .dream_engine import DreamEngine
from .expression import build_envelope, select_resistance
from .habit import Habit, HabitTracker
from .identity import CoreIdentity, EarnedTrait, IdentityLedger, classify_user_identity_command
from .intention import Intention, IntentionQueue, OpenLoop
from .interpretation import InterpretationEngine, sources_from_mapping
from .memory import KnowledgeSource, MemoryStore, MemoryUnit
from .memory_policy import apply_resident_memory_policy
from .cold_biography import (
    contextual_readthrough_request,
    explicit_recall_request,
    merge_contextual_candidates,
    merge_recall_candidates,
    retrieve_cold_biography,
    retrieve_contextual_biography,
)
from .decision_memory import evaluate_history_for_decision
from .decision_commitment import evaluate_commitments_for_decision
from .persistence import Persistence, DEFAULT_RUNTIME_DIAGNOSTIC_EVENT_LIMIT
from .relationship import RelationshipState, appraise_event, apply_appraisal, relationship_to_qualitative
from .private_cognition import generate_private_cognition, report_to_dict, validate_and_apply
from .renderer import LocalLLMRenderer, OutputValidator, render_expression
from .consistency import ConsistencyLayer, regeneration_constraints
from .renderer_contract import ValidationAction, ValidationRequest
from .symbols import SharedSymbol, SymbolStore
from .situated import SituatedInterfaceState, InterfaceEvent
from .workspace import WorkspaceFrame
from .body import BodyProfile, BodyState
from .world import WorldProfile, WorldState
from .sensorium import SensoriumProcessor
from .organism_tick import OrganismTick
from .public_state import public_status_from_engine, debug_snapshot_from_engine
from .proactive import ProactiveQueue
from .second_thought import derive_second_thoughts
from .world_authority import WorldAuthority, WorldActionProposal
from .event_classifier import EventClassifier, can_promote_to_canonical_memory
from .sensory_router import SensoryRouter
from .audio_sensor import AudioObservation
from .vision_sensor import VisionObservation
from .voice import VoiceProfile, VoicePlanner
from .avatar import AvatarProfile, AvatarProjector
from .suppression import SuppressionTrace
from .continuity_clock import ClockAdvance, ContinuityClock
from .continuity import state_digest as continuity_state_digest


def bucket_risk(risk: float) -> str:
    if risk <= 0.30:
        return "LOW"
    if risk <= 0.65:
        return "MEDIUM"
    return "HIGH"


def _enum_value(value: Any) -> Any:
    return getattr(value, "value", value)


def _suppression_trace(gate: str, action: str, reason: str, severity: str = "info") -> SuppressionTrace:
    return SuppressionTrace(gate=gate, action=action, reason=reason, severity=severity)


def _serialized_state_access(method):
    """Serialize one public access path to the mutable continuing subject.

    The engine remains single-writer in this local runtime. A reentrant lock is
    required because a complete turn calls other public projections and plans
    before returning. The lock prevents background time advancement, renderer
    reconfiguration, or another host call from observing or mutating a partial
    turn.
    """

    @wraps(method)
    def wrapped(self, *args, **kwargs):
        with self._state_lock:
            return method(self, *args, **kwargs)

    return wrapped


# Compatibility budget for pre-M4 per-five-second dynamics. Full elapsed subject
# time is never truncated. These 1,000 seconds only bound legacy body/pressure
# integration until those rates are empirically calibrated against real duration.
LEGACY_IDLE_STEP_SECONDS = 5.0
LEGACY_CATCHUP_DYNAMICS_BUDGET_SECONDS = 1000.0

# Explicit snapshot ownership. Only experimentally demonstrated subject-owned
# families belong here. Everything else keeps its existing interlocutor scope
# until a separate longitudinal failure earns a different ownership rule.
SUBJECT_OWNED_SNAPSHOT_KEYS = frozenset({"continuity_clock", "earned_traits"})


@dataclass
class ReflectionCandidate:
    claim: str
    confidence: float
    source_memory_ids: list[str]
    scope: str

    @property
    def commit_allowed(self) -> bool:
        return self.confidence >= 0.65 and self.scope in {"relationship", "identity", "situational"}


class InteriorEngine:
    def __init__(self, identity: CoreIdentity | None = None, user_id: str = "default_user", db_path: str = "persona_state.db", cartridge_path: str | None = None, diagnostic_event_limit: int | None = DEFAULT_RUNTIME_DIAGNOSTIC_EVENT_LIMIT, host_id: str = "local"):
        self._state_lock = threading.RLock()
        self.host_id = str(host_id or "local")
        self.cartridge_data = None
        self.belief_rules = []
        if cartridge_path is not None:
            identity, loaded_ledger, raw = load_cartridge(cartridge_path)
            self.cartridge_data = raw
            self.belief_rules = list(raw.get("belief_rules", []))
            self.belief_ledger = BeliefLedger(raw.get("beliefs", []))
        else:
            if identity is None:
                raise ValueError("InteriorEngine requires either identity or cartridge_path")
            loaded_ledger = IdentityLedger(immutable=identity)
            self.belief_ledger = BeliefLedger([])
        self.identity = identity
        self.user_id = user_id
        self.ledger = loaded_ledger
        self.relationship = RelationshipState(user_id=user_id)
        self.memory = MemoryStore()
        self.pressures = PressureSystem()
        self.intentions = IntentionQueue()
        self.symbols = SymbolStore()
        self.habits = HabitTracker()
        profile_source = self.cartridge_data or {}
        self.body_profile = BodyProfile.from_dict(profile_source.get("body_profile"))
        self.world_profile = WorldProfile.from_dict(profile_source.get("world_profile"))
        self.body = BodyState.from_profile(self.body_profile)
        self.world = WorldState.from_profile(self.world_profile)
        self.sensorium = SensoriumProcessor()
        self.organism_tick = OrganismTick(self.world_profile, self.body_profile)
        self.proactive = ProactiveQueue()
        self.world_authority = WorldAuthority()
        self.event_classifier = EventClassifier()
        self.sensory_router = SensoryRouter()
        self.voice_profile = VoiceProfile.from_dict(profile_source.get("voice_profile"))
        self.voice_planner = VoicePlanner(self.voice_profile)
        self.avatar_profile = AvatarProfile.from_dict(profile_source.get("avatar_profile"))
        self.avatar_projector = AvatarProjector(self.avatar_profile)
        self.interface = SituatedInterfaceState()
        self.interpreter = InterpretationEngine()
        self._idle_thread = None
        self._idle_stop = threading.Event()
        # Renderer bootstrap is host/runtime policy, not character identity.
        # Start deterministically offline until an approved host/session replaces it.
        self.renderer = LocalLLMRenderer(model_name="missing-model-for-mock", provider="offline")
        self.validator = OutputValidator()
        self.consistency = ConsistencyLayer(self.validator)
        self.persistence = Persistence(db_path, diagnostic_event_limit=diagnostic_event_limit, host_id=self.host_id)
        if self.identity.entity_uuid:
            self.persistence.bind_subject(self.identity.name, self.user_id, self.identity.entity_uuid)
        self.deception_ledger = DeceptionLedger()
        self.dream_engine = DreamEngine(self.persistence, self.belief_ledger)

        self.energy = 0.8
        self.restlessness = 0.2
        self.timestep = 0
        self.clock = ContinuityClock(last_wall_time=time.time())
        self.last_reflection_time = 0.0

        self._load_state()
        self._restore_subject_owned_clock()
        self._restore_subject_owned_commitments()

    @contextmanager
    def state_transaction(self):
        """Hold the engine single-writer boundary for a compound host mutation.

        CharacterAgent uses this only for legacy compound helpers that directly
        touch a state family before persistence. Normal engine entry points apply
        the same reentrant lock automatically.
        """

        with self._state_lock:
            yield

    def _require_writer(self) -> dict[str, Any]:
        return self.persistence.assert_writer(self.identity.name, self.user_id)

    @_serialized_state_access
    def writer_status(self) -> dict[str, Any]:
        return self.persistence.writer_status(self.identity.name, self.user_id)

    @_serialized_state_access
    def handoff_writer(self, target_host_id: str) -> dict[str, Any]:
        """Persist a clean boundary, then transfer exclusive host write custody."""
        self._require_writer()
        self._persist()
        digest = continuity_state_digest(self._serialize_state())
        return self.persistence.handoff_writer(
            self.identity.name, self.user_id, target_host_id, state_digest=digest
        )

    @_serialized_state_access
    def accept_writer_handoff(self, receipt: dict[str, Any]) -> dict[str, Any]:
        """Accept custody only when loaded state matches the source boundary."""
        digest = continuity_state_digest(self._serialize_state())
        return self.persistence.accept_writer_handoff(
            self.identity.name, self.user_id, receipt, local_state_digest=digest
        )

    @_serialized_state_access
    def prepare_disconnected_transfer(self, target_host_id: str) -> dict[str, Any]:
        """Persist one clean whole-subject boundary, package it, and quiesce this store."""
        self._require_writer()
        self._persist()
        digest = continuity_state_digest(self._serialize_state())
        return self.persistence.prepare_disconnected_transfer(
            self.identity.name,
            self.user_id,
            target_host_id,
            local_state_digest=digest,
        )

    @_serialized_state_access
    def cancel_disconnected_transfer(self, transfer_uuid: str) -> dict[str, Any]:
        """Cancel a prepared move before source finalization and restore source writes."""
        return self.persistence.cancel_disconnected_transfer(
            self.identity.name, self.user_id, transfer_uuid
        )

    @_serialized_state_access
    def finalize_disconnected_transfer(self, stage_receipt: dict[str, Any]) -> dict[str, Any]:
        """Retire this source store only after a target has staged the exact bundle."""
        digest = continuity_state_digest(self._serialize_state())
        return self.persistence.finalize_disconnected_transfer(
            self.identity.name,
            self.user_id,
            stage_receipt,
            local_state_digest=digest,
        )

    @_serialized_state_access
    def activate_disconnected_transfer(self, final_receipt: dict[str, Any]) -> dict[str, Any]:
        """Activate a staged target only after the source has irreversibly retired."""
        digest = continuity_state_digest(self._serialize_state())
        return self.persistence.activate_disconnected_transfer(
            self.identity.name,
            self.user_id,
            final_receipt,
            local_state_digest=digest,
        )

    @_serialized_state_access
    def set_renderer(self, renderer) -> None:
        """Replace only the surface renderer through an approved host channel."""

        self.renderer = renderer

    @_serialized_state_access
    def renderer_status(self) -> dict:
        status = getattr(self.renderer, "runtime_status", None)
        if callable(status):
            return status()
        return {"requested_provider": "custom", "actual_provider": "custom", "model_name": type(self.renderer).__name__}

    @_serialized_state_access
    def adopt_commitment(self, commitment_kind: str, commitment_target: str, *, record_event: bool = True, persist: bool = True) -> dict:
        """Explicitly adopt one typed character-owned commitment.

        This is a semantic self-decision seam, not a natural-language parser.
        User or renderer text cannot call this implicitly. V1 supports only the
        non-disclosure behavior demonstrated by the commitment-gap experiment.
        """

        if record_event or persist:
            self._require_writer()
        kind = str(commitment_kind or "").strip().lower()
        target = " ".join(str(commitment_target or "").strip().lower().split())
        if kind != "non_disclosure":
            raise ValueError("unsupported commitment kind")
        if not target:
            raise ValueError("commitment target must not be empty")
        normalized_name = target.replace(" ", "_")
        intention = Intention(
            name=f"commitment:{kind}:{normalized_name}",
            priority=0.0,
            source="self_decision",
            created_at=time.time(),
            expires_at=None,
            requires_user_context=False,
            commitment_kind=kind,
            commitment_target=target,
        )
        self.intentions.add_intention(intention)
        payload = {
            "commitment_name": intention.name,
            "commitment_kind": kind,
            "commitment_target": target,
            "adoption_source": "self_decision",
            "adopted_at": intention.created_at,
            "payload_schema": "commitment-adoption-v1",
            "memory_types": ["commitment"],
        }
        if record_event:
            self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "commitment_adopted", payload)
        if persist:
            self._persist()
        return payload

    @property
    def last_wall_time(self) -> float:
        """Compatibility alias for pre-M4 callers; ContinuityClock owns time."""
        return self.clock.last_wall_time

    @last_wall_time.setter
    def last_wall_time(self, value: float) -> None:
        self.clock.last_wall_time = float(value)

    # ---------------- persistence ----------------
    def _load_state(self):
        cid, uid = self.identity.name, self.user_id
        meta = self.persistence.load(cid, uid, "meta", {})
        self.energy = meta.get("energy", self.energy)
        self.restlessness = meta.get("restlessness", self.restlessness)
        self.timestep = meta.get("timestep", self.timestep)
        clock_state = self.persistence.load_subject(cid, uid, "continuity_clock", None)
        if clock_state is None:
            # Legacy fallback for databases created before explicit state scope.
            clock_state = self.persistence.load(cid, uid, "continuity_clock")
        if clock_state:
            self.clock = ContinuityClock.from_dict(clock_state)
        else:
            # v1 compatibility: preserve the old wall anchor, but do not invent
            # historical elapsed subject time that was never recorded.
            self.clock.last_wall_time = float(meta.get("last_wall_time", self.clock.last_wall_time))
        self.last_reflection_time = meta.get("last_reflection_time", self.last_reflection_time)

        rel = self.persistence.load(cid, uid, "relationship")
        if rel:
            for k, v in rel.items():
                if hasattr(self.relationship, k):
                    setattr(self.relationship, k, v)

        for m in self.persistence.load(cid, uid, "memories", []):
            self.memory.add(MemoryUnit(
                content=m["content"],
                created_at=m["created_at"],
                id=m["id"],
                recall_times=m.get("recall_times", []),
                emotional_valence=m.get("emotional_valence", 0.0),
                emotional_intensity=m.get("emotional_intensity", 0.0),
                relationship_relevance=m.get("relationship_relevance", 0.0),
                identity_relevance=m.get("identity_relevance", 0.0),
                unresolved=m.get("unresolved", False),
                source=KnowledgeSource(m.get("source", "observed")),
                tags=set(m.get("tags", [])),
                compressed=m.get("compressed", False),
            ))

        for p in self.persistence.load(cid, uid, "pressures", []):
            self.pressures.add(EmotionalPressure(
                name=p["name"], magnitude=p["magnitude"], inhibition_strength=p.get("inhibition_strength", 0.5),
                trigger_sensitivity=p.get("trigger_sensitivity", 1.0), last_triggered=p.get("last_triggered", 0.0),
                self_access=p.get("self_access"),
            ))

        for i in self.persistence.load(cid, uid, "intentions", []):
            self.intentions.add_intention(Intention(**i))
        for l in self.persistence.load(cid, uid, "open_loops", []):
            self.intentions.add_open_loop(OpenLoop(**l))
        for s in self.persistence.load(cid, uid, "symbols", []):
            self.symbols.add(SharedSymbol(**s))
        for h in self.persistence.load(cid, uid, "habits", []):
            self.habits.habits[h["name"]] = Habit(**h)
        trait_state = self.persistence.load_subject(cid, uid, "earned_traits", None)
        if trait_state is None:
            # Legacy fallback for the active stream only. Cross-stream merging is
            # intentionally not guessed because old snapshots may disagree.
            trait_state = self.persistence.load(cid, uid, "earned_traits", [])
        for t in trait_state:
            self.ledger.earned_traits[t["name"]] = EarnedTrait(**t)
        self.ledger.per_relationship_beliefs = self.persistence.load(cid, uid, "relationship_beliefs", {})
        belief_state = self.persistence.load(cid, uid, "belief_ledger")
        if belief_state:
            self.belief_ledger = BeliefLedger.from_state(belief_state, self.cartridge_data.get("beliefs", []) if self.cartridge_data else [])
            self.dream_engine = DreamEngine(self.persistence, self.belief_ledger)
        self.deception_ledger = self.persistence.load_deception_ledger(cid, uid)

        iface = self.persistence.load(cid, uid, "interface")
        if iface:
            self.interface.channel = iface.get("channel", self.interface.channel)
            self.interface.action_affordances = iface.get("action_affordances", self.interface.action_affordances)
            self.interface.visible_context = iface.get("visible_context", [])
            self.interface.last_input_at = iface.get("last_input_at", 0.0)
            self.interface.last_output_at = iface.get("last_output_at", 0.0)
            for ev in iface.get("observed_events", []):
                self.interface.observed_events.append(InterfaceEvent(**ev))
        self.body = BodyState.from_dict(self.persistence.load(cid, uid, "body"), self.body_profile)
        self.world = WorldState.from_dict(self.persistence.load(cid, uid, "world"), self.world_profile)
        self.sensorium = SensoriumProcessor.from_list(self.persistence.load(cid, uid, "sensorium", []))
        self.world_authority = WorldAuthority.from_list(self.persistence.load(cid, uid, "world_authority", []))

    def _restore_subject_owned_clock(self) -> None:
        """Reconcile interlocutor-scoped clock snapshots with subject history.

        ``ContinuityClock`` is character-owned state. Existing snapshots remain
        keyed by interlocutor for compatibility, but a newly opened relationship
        must not fork the subject onto an earlier timeline. Canonical time roots
        already carry the subject's accumulated elapsed time, so only an upward
        reconciliation is required here. No psychological meaning is inferred.
        """

        events = self.persistence.load_subject_continuity_events(
            self.identity.name,
            self.user_id,
            event_type="time_advance",
        )
        if not events:
            return
        payload = events[-1].get("payload") or {}
        try:
            canonical_elapsed = max(0.0, float(payload.get("subject_elapsed_seconds", 0.0)))
        except (TypeError, ValueError):
            return
        if canonical_elapsed <= self.clock.subject_elapsed_seconds:
            return
        self.clock.subject_elapsed_seconds = canonical_elapsed
        observed_wall = payload.get("observed_wall_time")
        if isinstance(observed_wall, (int, float)):
            self.clock.last_wall_time = float(observed_wall)

    def _restore_subject_owned_commitments(self) -> None:
        """Restore self-owned commitments from canonical subject history.

        Snapshot state remains interlocutor-scoped for compatibility. Commitments
        are different: once explicitly self-adopted, they belong to the continuing
        subject rather than to whichever interlocutor happened to be present at
        adoption. Canonical history is therefore the source used to rehydrate them
        when a new relationship context opens.

        This deliberately restores only the commitment behavior demonstrated by
        the interlocutor-continuity probe. Other snapshot families remain unchanged
        until a separate longitudinal test shows that their ownership is wrong.
        """

        events = self.persistence.load_subject_continuity_events(
            self.identity.name,
            self.user_id,
            event_type="commitment_adopted",
        )
        for event in events:
            payload = event.get("payload") or {}
            if payload.get("adoption_source") != "self_decision":
                continue
            kind = str(payload.get("commitment_kind", ""))
            target = str(payload.get("commitment_target", ""))
            if kind != "non_disclosure" or not target.strip():
                continue
            normalized_target = " ".join(target.strip().lower().split())
            normalized_name = normalized_target.replace(" ", "_")
            commitment_name = str(payload.get("commitment_name") or f"commitment:{kind}:{normalized_name}")
            existing = next((item for item in self.intentions.intentions if item.name == commitment_name), None)
            if existing is not None:
                continue
            adopted_at = payload.get("adopted_at", event.get("created_at", time.time()))
            try:
                adopted_at = float(adopted_at)
            except (TypeError, ValueError):
                adopted_at = float(event.get("created_at", time.time()))
            self.intentions.add_intention(
                Intention(
                    name=commitment_name,
                    priority=0.0,
                    source="self_decision",
                    created_at=adopted_at,
                    expires_at=None,
                    requires_user_context=False,
                    commitment_kind=kind,
                    commitment_target=normalized_target,
                )
            )

    def _serialize_state(self) -> dict:
        memories = []
        for m in self.memory.memories:
            memories.append({
                "content": m.content,
                "created_at": m.created_at,
                "id": m.id,
                "recall_times": m.recall_times,
                "emotional_valence": m.emotional_valence,
                "emotional_intensity": m.emotional_intensity,
                "relationship_relevance": m.relationship_relevance,
                "identity_relevance": m.identity_relevance,
                "unresolved": m.unresolved,
                "source": _enum_value(m.source),
                "tags": list(m.tags),
                "compressed": m.compressed,
            })
        pressures = [asdict(p) for p in self.pressures.pressures.values()]
        intentions = [asdict(i) for i in self.intentions.intentions]
        loops = [asdict(l) for l in self.intentions.open_loops]
        symbols = [asdict(s) for s in self.symbols.symbols.values()]
        habits = [asdict(h) for h in self.habits.habits.values()]
        traits = [asdict(t) for t in self.ledger.earned_traits.values()]
        interface = {
            "channel": self.interface.channel,
            "action_affordances": self.interface.action_affordances,
            "visible_context": self.interface.visible_context,
            "observed_events": [asdict(e) for e in self.interface.observed_events],
            "last_input_at": self.interface.last_input_at,
            "last_output_at": self.interface.last_output_at,
        }
        return {
            "meta": {
                "energy": self.energy,
                "restlessness": self.restlessness,
                "timestep": self.timestep,
                "last_wall_time": self.last_wall_time,
                "last_reflection_time": self.last_reflection_time,
            },
            "relationship": vars(self.relationship),
            "memories": memories,
            "pressures": pressures,
            "intentions": intentions,
            "open_loops": loops,
            "symbols": symbols,
            "habits": habits,
            "earned_traits": traits,
            "relationship_beliefs": self.ledger.per_relationship_beliefs,
            "interface": interface,
            "body": self.body.to_dict(),
            "world": self.world.to_dict(),
            "continuity_clock": self.clock.to_dict(),
            "sensorium": self.sensorium.to_dict(),
            "belief_ledger": self.belief_ledger.to_state(),
            "world_authority": self.world_authority.to_list(),
            "deception_ledger": self.deception_ledger.to_state(),
        }

    def _persist(self):
        self._require_writer()
        # WorldAuthority is the current objective-state authority. Canonical
        # continuity owns world history, so facts that can never again affect
        # server or visible truth are compacted before snapshot persistence.
        self.world_authority.compact_dominated()
        apply_resident_memory_policy(self.memory, self.relationship)
        state = self._serialize_state()
        # Preserve the full legacy/interlocutor snapshot for compatibility, then
        # write only explicitly earned subject-owned families to UUID scope.
        self.persistence.save_many(self.identity.name, self.user_id, state)
        self.persistence.save_subject_many(
            self.identity.name,
            self.user_id,
            {key: state[key] for key in SUBJECT_OWNED_SNAPSHOT_KEYS},
        )
        self.persistence.record_checkpoint(self.identity.name, self.user_id, state)

    # ---------------- idle and silent processing ----------------
    def _catch_up_idle(self):
        advance = self.clock.observe_wall(time.time(), source="wall_clock_catchup")
        self._apply_clock_advance(advance, record_event=True, persist=False)

    @_serialized_state_access
    def advance_time(self, elapsed_seconds: float, *, source: str = "explicit", record_event: bool = True, persist: bool = True) -> dict:
        """Advance linear subject time and apply only explicitly bounded dynamics.

        Full elapsed time is preserved in ContinuityClock and the canonical
        ``time_advance`` root. Legacy five-second body/pressure mechanics receive
        at most the compatibility budget until those coefficients are calibrated.
        """
        self._require_writer()
        advance = self.clock.advance_by(elapsed_seconds, observed_wall_time=time.time(), source=source)
        return self._apply_clock_advance(advance, record_event=record_event, persist=persist)

    def _apply_clock_advance(self, advance: ClockAdvance, *, record_event: bool, persist: bool) -> dict:
        elapsed = max(0.0, float(advance.elapsed_seconds))
        dynamics_seconds = min(elapsed, LEGACY_CATCHUP_DYNAMICS_BUDGET_SECONDS)
        steps = int(dynamics_seconds / LEGACY_IDLE_STEP_SECONDS)
        for index in range(steps):
            self._run_single_idle_cycle(
                elapsed_seconds=LEGACY_IDLE_STEP_SECONDS,
                world_elapsed_seconds=elapsed if index == 0 else 0.0,
            )
        self.timestep += steps
        payload = advance.to_payload()
        payload.update({
            "dynamics_seconds": round(steps * LEGACY_IDLE_STEP_SECONDS, 6),
            "dynamics_steps": steps,
            "dynamics_profile": "legacy_bounded_v1",
            "memory_types": ["time_advance"],
        })
        # Ordinary sub-step wall gaps update the clock but do not create a
        # standalone canonical stopwatch event. They have no current dynamics
        # effect and the next canonical experience still carries wall time.
        # Explicit advances can request their own event even below this quantum.
        should_record_time = (elapsed >= LEGACY_IDLE_STEP_SECONDS or advance.backward_correction_seconds > 0.0 or advance.source != "wall_clock_catchup")
        if record_event and should_record_time:
            self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "time_advance", payload)
        if persist:
            self._persist()
        return payload

    def run_idle_cycle(self):
        return self.advance_time(LEGACY_IDLE_STEP_SECONDS, source="manual_idle", record_event=True, persist=True)

    def _run_single_idle_cycle(self, elapsed_seconds: float = 5.0, *, world_elapsed_seconds: float | None = None):
        now = time.time()
        total_pressure = sum(p.magnitude for p in self.pressures.pressures.values())
        self.energy = max(0.1, self.energy - total_pressure * 0.01)
        self.restlessness = min(1.0, self.restlessness + 0.02)
        self.pressures.decay_all()
        self.organism_tick.idle(
            elapsed_seconds=elapsed_seconds,
            world_elapsed_seconds=world_elapsed_seconds,
            now=now,
            world=self.world,
            body=self.body,
            sensorium=self.sensorium,
            pressures=self.pressures,
            memory=self.memory,
            intentions=self.intentions,
        )
        self.intentions.decay_open_loops()
        self.habits.decay_all()
        self.symbols.lifecycle_tick(now)
        self.memory.compress_old(now)
        if (self.energy < 0.3 or self.relationship.unresolved_conflict > 0.6) and (now - self.last_reflection_time > 300):
            self._trigger_reflection(now)

    def _trigger_reflection(self, now: float):
        top_mems = self.memory.retrieve("reflection on recent unresolved events", now, top_k=3)
        if not top_mems:
            return
        # A memory may truthfully record that an episode was unresolved at the
        # time without implying that the relationship is still unresolved now.
        # Reflection must therefore combine historical evidence with current
        # relationship state, matching the conduct gate's repair semantics.
        relationship_unresolved_now = self.relationship.unresolved_conflict > 0.0
        resolution_cutoff = float(getattr(self.relationship, "last_conflict_resolved_at", 0.0) or 0.0)
        unresolved = [
            memory for memory in top_mems
            if relationship_unresolved_now
            and memory.unresolved
            and float(memory.created_at) > resolution_cutoff
        ]
        evidence_mems = unresolved if unresolved else top_mems
        ids = [m.id for m in evidence_mems]
        confidence = min(0.9, 0.45 + 0.15 * len(unresolved) + sum(m.identity_relevance for m in evidence_mems) / 10.0)
        claim = "The relationship tends to become guarded after unresolved accusations." if unresolved else "Recent exchanges are forming a stable interaction pattern."
        candidate = ReflectionCandidate(claim=claim, confidence=confidence, source_memory_ids=ids, scope="relationship")
        if candidate.commit_allowed:
            self.ledger.propose_trait_update("reflective_pattern", 0.05, candidate.source_memory_ids)
            self.ledger.set_relationship_belief(self.user_id, "recent_reflection", candidate.claim)
            self.memory.add(MemoryUnit(
                content=f"I formed a reflection: {candidate.claim}",
                created_at=now,
                source=KnowledgeSource.REFLECTION,
                emotional_intensity=0.35,
                relationship_relevance=0.7,
                identity_relevance=0.5,
                tags={"reflection"},
            ))
        self.last_reflection_time = now
        for p in self.pressures.pressures.values():
            p.magnitude = max(0.0, p.magnitude - 0.1)
        self.restlessness = max(0.0, self.restlessness - 0.2)

    def start_background_idle(self, interval_seconds: float = 30.0):
        """Optional real idle loop. Wall-clock catch-up remains the default safe path.

        A UI can call this when it wants the character to change state while the
        process is open and no user input is arriving.
        """
        if self._idle_thread and self._idle_thread.is_alive():
            return
        self._idle_stop.clear()

        def _loop():
            while not self._idle_stop.wait(interval_seconds):
                self.advance_time(interval_seconds, source="background_idle", record_event=True, persist=True)

        self._idle_thread = threading.Thread(target=_loop, daemon=True)
        self._idle_thread.start()

    def stop_background_idle(self):
        self._idle_stop.set()
        if self._idle_thread and self._idle_thread.is_alive():
            self._idle_thread.join(timeout=1.0)


    # ---------------- public interface projection ----------------
    @_serialized_state_access
    def public_status(self, affect_bucket: str | None = None, dominant_pressure: str | None = None) -> dict[str, str]:
        """Return categorical public organism status for UI renderers."""

        return public_status_from_engine(self, affect_bucket=affect_bucket, dominant_pressure=dominant_pressure).to_dict()

    @_serialized_state_access
    def debug_snapshot(self) -> dict:
        """Return private debug state for developer inspection only."""

        return debug_snapshot_from_engine(self)

    @_serialized_state_access
    def poll_proactive_events(self, max_events: int = 3) -> list[dict]:
        """Return generic proactive event proposals without mutating state."""

        now = time.time()
        return [event.to_dict() for event in self.proactive.evaluate(
            now=now,
            relationship=self.relationship,
            body=self.body,
            world=self.world,
            intentions=self.intentions,
            max_events=max_events,
        )]

    # ---------------- slow consolidation ----------------
    @_serialized_state_access
    def dream(self, min_interval_seconds: int = 3600, *, record_event: bool = True) -> list[str]:
        """Run one slow-belief pass and preserve causally relevant boundaries.

        A threshold-miss can still be causal because it consumes evidence that
        would otherwise combine with later evidence. Therefore any executed pass
        with rule-relevant evidence becomes a compact character-owned root even
        when ``changed_beliefs`` is empty. Passes containing no evidence consumed
        by the active rule set remain noncanonical housekeeping.
        """

        self._require_writer()
        result = self.dream_engine.prepare_idle_pass(
            self.identity.name,
            self.user_id,
            self.belief_rules,
            min_interval_seconds,
        )
        if result is None:
            return []

        trigger_types = {
            str(rule.get("trigger_memory_type"))
            for rule in self.belief_rules
            if str(rule.get("trigger_memory_type", "")).strip()
        }
        relevant_counts = {
            key: int(value)
            for key, value in result.evidence_counts.items()
            if key in trigger_types and int(value) > 0
        }
        changed = list(result.changed_beliefs)

        if record_event and relevant_counts:
            changes = {
                belief_id: {
                    "before": float(result.before_values[belief_id]),
                    "after": float(result.after_values[belief_id]),
                }
                for belief_id in changed
            }
            payload = {
                "payload_schema": "belief-consolidation-v1",
                "consolidation_source": "dream_engine",
                "relevant_evidence_counts": relevant_counts,
                "changed_beliefs": changed,
                "changes": changes,
                "before_beliefs_digest": continuity_state_digest(result.before_values),
                "after_beliefs_digest": continuity_state_digest(result.after_values),
                "rules_digest": continuity_state_digest(self.belief_rules),
            }
            self.persistence.commit_belief_consolidation(
                self.identity.name,
                self.user_id,
                self.timestep,
                belief_state=self.belief_ledger.to_state(),
                evidence_through=result.watermark,
                payload=payload,
            )
        else:
            # Replay suppresses root creation but must consume the same evidence
            # window so later recorded boundaries see the same partition.
            self.dream_engine.persist_prepared(self.identity.name, self.user_id, result)

        self._persist()
        return changed

    @_serialized_state_access
    def export_session_snapshot(self):
        from .session import export_snapshot
        return export_snapshot(self.pressures, self.belief_ledger, self.identity.name)

    @_serialized_state_access
    def import_session_snapshot(self, snap):
        self._require_writer()
        from .session import import_snapshot
        import_snapshot(snap, self.pressures, self.belief_ledger, self.identity.name)
        self._persist()

    # ---------------- risk ----------------
    def compute_leak_risk(self, incoming_event: str) -> float:
        top = self.pressures.top()
        if top is None:
            return 0.0
        inhibition_weakness = 1.0 - top.inhibition_strength
        depletion_multiplier = 1.0 + ((1.0 - self.energy) * 0.75)
        restlessness_multiplier = 1.0 + (self.restlessness * 0.5)
        trigger_match = self.pressures.trigger_match(incoming_event)
        raw = top.magnitude * inhibition_weakness * depletion_multiplier * restlessness_multiplier * trigger_match
        return max(0.0, min(1.0, raw))

    def _resolve_decision_payload(self, triggers: list[str], risk: float, resistance: str | None = None, history_evidence: dict[str, Any] | None = None, commitment_evidence: dict[str, Any] | None = None) -> dict[str, Any]:
        """Resolve semantic conduct independently from expression intensity.

        A HIGH risk bucket may shorten/guard expression, but arousal alone is not
        an identity-boundary event. The semantic dialogue act follows the actual
        trigger/resistance policy so overload cannot masquerade as identity threat.
        """

        suspicion = self.pressures.pressures.get("suspicion")
        suspicion_value = suspicion.magnitude if suspicion else 0.0
        dialogue_act = "challenge" if suspicion_value >= 0.60 else "respond"
        history_payload = dict(history_evidence or {})
        commitment_payload = dict(commitment_evidence or {})
        # Retrieved lived history may qualify a present trust/commitment decision,
        # but it never outranks explicit identity/resistance policy and never
        # mutates relationship state on its own.
        if dialogue_act == "respond" and bool(history_payload.get("active")) and resistance is None:
            dialogue_act = "qualified_response"
        # An already-adopted typed commitment constrains an incompatible ordinary
        # act. It does not compete by priority and it does not masquerade as an
        # identity boundary. Explicit resistance policy still outranks it below.
        if dialogue_act in {"respond", "qualified_response"} and bool(commitment_payload.get("active")) and resistance is None:
            dialogue_act = "decline"
        if resistance == "character_refusal":
            dialogue_act = "protect_boundary"
        elif resistance == "challenge":
            dialogue_act = "challenge"
        elif resistance == "go_quiet":
            dialogue_act = "withdraw"
        elif resistance == "deflect":
            dialogue_act = "deflect"
        elif resistance == "shift_topic":
            dialogue_act = "redirect"
        return {
            "dialogue_act": dialogue_act,
            "concealment_mode": "none",
            "challenge_threshold": 0.60,
            "suspicion": round(suspicion_value, 3),
            "triggers": list(triggers),
            "resistance_mode": resistance or "none",
            "risk_bucket": bucket_risk(risk),
            "history_evidence": history_payload or {"active": False, "strength": 0.0, "memory_ids": [], "reason": "none"},
            "commitment_evidence": commitment_payload or {"active": False, "commitment_kind": "none", "commitment_target": "", "intention_name": "", "reason": "none"},
        }

    # ---------------- v10 sensory and embodiment plumbing ----------------
    @_serialized_state_access
    def ingest_audio_observation(self, observation: AudioObservation) -> dict:
        """Route a bounded audio observation through world authority.

        Audio modules cannot mutate pressure or relationship state directly.
        """
        self._require_writer()
        before_pressures = {name: p.magnitude for name, p in self.pressures.pressures.items()}
        routed = self.sensory_router.route_audio(observation, self.world_authority)
        payload = {
            "sensor_type": "audio",
            "observation": observation.to_safe_payload(),
            "facts": [fact.to_dict() for fact in routed.resolution.facts_created],
            "memory_types": ["sensorium", "world_fact"],
        }
        self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "sensor_observation", payload)
        # Apply only safe world fields that the generic world state understands.
        host = {}
        if observation.sound_level in {"silent", "low", "moderate", "high"}:
            host["noise_level"] = observation.sound_level if observation.sound_level != "silent" else "low"
        if observation.sudden_onset:
            host["ambient_event"] = "sudden sound"
        if observation.speech_activity:
            host["sound"] = "speech activity"
        self.world.apply_host_facts(host, host, now=observation.created_at)
        self._persist()
        return {"accepted": routed.resolution.accepted, "facts": [f.to_dict() for f in routed.resolution.facts_created], "pressure_unchanged": before_pressures == {name: p.magnitude for name, p in self.pressures.pressures.items()}}

    @_serialized_state_access
    def ingest_vision_observation(self, observation: VisionObservation) -> dict:
        """Route a bounded vision observation through world authority."""
        self._require_writer()
        before_relationship = dict(vars(self.relationship))
        routed = self.sensory_router.route_vision(observation, self.world_authority)
        payload = {
            "sensor_type": "vision",
            "observation": observation.to_safe_payload(),
            "facts": [fact.to_dict() for fact in routed.resolution.facts_created],
            "memory_types": ["sensorium", "world_fact"],
        }
        self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "sensor_observation", payload)
        host = {"light_level": observation.light_level, "user_presence": observation.user_presence}
        if observation.movement_detected:
            host["movement"] = "movement detected"
        if observation.scene_change:
            host["ambient_event"] = "scene change"
        self.world.apply_host_facts(host, host, now=observation.created_at)
        self._persist()
        return {"accepted": routed.resolution.accepted, "facts": [f.to_dict() for f in routed.resolution.facts_created], "relationship_unchanged": before_relationship == dict(vars(self.relationship))}

    @_serialized_state_access
    def propose_world_action(self, action_type: str, payload: dict | None = None) -> dict:
        self._require_writer()
        proposal = WorldActionProposal(self.identity.name, action_type, dict(payload or {}), time.time())
        resolution = self.world_authority.resolve_action(proposal)
        visible = {fact.key: fact.value for fact in resolution.facts_created if fact.visible_to_character}
        self.world.apply_host_facts(visible, visible, now=proposal.created_at)
        self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "world_action_resolution", {
            "action_type": action_type,
            "payload": payload or {},
            "accepted": resolution.accepted,
            "reason": resolution.reason,
            "facts": [f.to_dict() for f in resolution.facts_created],
            "memory_types": ["world_fact", "action_resolution"],
        })
        self._persist()
        return {"accepted": resolution.accepted, "reason": resolution.reason, "facts": [f.to_dict() for f in resolution.facts_created]}

    @_serialized_state_access
    def plan_voice(self, text: str, envelope=None) -> dict:
        if envelope is None:
            top = self.pressures.top()
            risk = bucket_risk(self.compute_leak_risk(""))
            envelope = build_envelope(risk, self.relationship, top.name if top else "calm")
        plan = self.voice_planner.plan(text, envelope)
        self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "voice_plan", {"plan": plan.to_dict(), "memory_types": ["voice_plan"]})
        return plan.to_dict()

    @_serialized_state_access
    def avatar_projection(self, affect_bucket: str | None = None, dominant_pressure: str | None = None) -> dict:
        status = self.public_status(affect_bucket, dominant_pressure)
        state = self.avatar_projector.project(status)
        self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "avatar_state", {"state": state.to_dict(), "memory_types": ["avatar_state"]})
        return state.to_dict()

    def classify_event_for_memory(self, event_type: str, payload: dict, event_id=None) -> dict:
        classification = self.event_classifier.classify(event_type, payload, event_id=event_id)
        return classification.__dict__

    # ---------------- main turn ----------------
    @_serialized_state_access
    def receive_input(self, user_text: str, server_truth: dict | None = None, visible_context: dict | None = None) -> dict:
        self._require_writer()
        self._catch_up_idle()
        self.timestep += 1
        now = time.time()
        submitted_server_truth = dict(server_truth or {})
        server_truth = dict(submitted_server_truth)
        visible_context = dict(visible_context or {})
        submitted_visible_context = dict(visible_context)
        server_truth.setdefault("user_text", user_text)
        self.world_authority.apply_host_event(server_truth, source="server_truth", visible=False)
        self.world_authority.apply_host_event(visible_context, source="visible_context", visible=True)
        visible_context.update(self.world_authority.get_visible_context(self.identity.name))
        organism_result = self.organism_tick.interaction(
            user_text=user_text,
            server_truth=server_truth,
            visible_context=visible_context,
            now=now,
            world=self.world,
            body=self.body,
            sensorium=self.sensorium,
            pressures=self.pressures,
            memory=self.memory,
            intentions=self.intentions,
        )
        server_truth.update(organism_result.server_truth)
        for key, value in organism_result.visible_context.items():
            visible_context.setdefault(key, value)
        input_payload = {
            "user_text": user_text,
            "server_truth": server_truth,
            "visible_context": visible_context,
            "memory_types": ["user_input"],
        }
        input_classification = self.event_classifier.classify("input", input_payload, event_id=f"turn_{self.timestep}_input")
        input_payload["classification"] = input_classification.__dict__
        input_payload["canonical_truth"] = can_promote_to_canonical_memory("input", input_payload)
        input_root_payload = {"user_text": user_text}
        if submitted_server_truth:
            input_root_payload["server_truth"] = submitted_server_truth
        if submitted_visible_context:
            input_root_payload["visible_context"] = submitted_visible_context
        self.persistence.log_event(
            self.identity.name,
            self.user_id,
            self.timestep,
            "input",
            input_payload,
            continuity_payload=input_root_payload,
            continuity_payload_schema="input-root-v2",
        )
        if organism_result.server_truth or organism_result.visible_context:
            self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "sensorium", {
                "server_truth": organism_result.server_truth,
                "visible_context": organism_result.visible_context,
                "world": self.world.to_dict(),
                "body": self.body.to_dict(),
                "memory_types": ["sensorium"],
            })
        self.interface.observe_text(user_text, now)
        for key, value in visible_context.items():
            entry = f"{key}: {value}"
            if entry not in self.interface.visible_context:
                self.interface.visible_context.append(entry)
        self.interface.visible_context = self.interface.visible_context[-20:]

        forced_rewrite = classify_user_identity_command(user_text, self.identity.prohibited_mutations)
        suppression_traces: list[SuppressionTrace] = []
        if forced_rewrite:
            suppression_traces.append(_suppression_trace(
                "identity_guard",
                "blocked",
                "identity rewrite pressure detected",
                "warning",
            ))
        appraisal = appraise_event(user_text)
        relationship_before = dict(vars(self.relationship))
        pressure_before = {name: p.magnitude for name, p in self.pressures.pressures.items()}
        apply_appraisal(self.relationship, appraisal)
        conflict_before = float(relationship_before.get("unresolved_conflict", 0.0) or 0.0)
        conflict_after = float(self.relationship.unresolved_conflict)
        if conflict_before > 0.0 and conflict_after <= 0.0:
            self.relationship.last_conflict_resolved_at = now
            # Open loops are current unfinished concerns, not immutable biography.
            # Once this scalar relationship model says conflict is fully repaired,
            # stale tension loops must not resurface the repaired episode later.
            self.intentions.open_loops = [
                loop for loop in self.intentions.open_loops
                if not str(loop.topic).startswith("unresolved tension from:")
            ]
        self.pressures.apply_appraisal(appraisal, self.relationship.trust)
        self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "state_transition", {
            "appraisal": vars(appraisal),
            "relationship_before": relationship_before,
            "relationship_after": dict(vars(self.relationship)),
            "pressure_before": pressure_before,
            "pressure_after": {name: p.magnitude for name, p in self.pressures.pressures.items()},
            "memory_types": ["state_transition"],
        })
        self.symbols.detect_from_text(user_text, now, self.relationship)
        interpretation_context = dict(submitted_visible_context)
        interpretation_context.setdefault("user_text", user_text)
        interpretation_context.update(organism_result.server_truth)
        interpretation_sources = sources_from_mapping(interpretation_context, "visible_context")
        interpretation_result = self.interpreter.form_beliefs(
            visible_sources=interpretation_sources,
            pressure_state=self.pressures,
            identity_bias={
                "trust": self.relationship.trust,
                "guardedness": self.relationship.guardedness,
            },
            max_beliefs=3,
        )
        interpretive_beliefs = list(interpretation_result.beliefs)
        for belief in interpretive_beliefs:
            self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "belief", {
                "belief_id": belief.belief_id,
                "text": belief.text,
                "confidence": belief.confidence,
                "source_ids": list(belief.source_ids),
                "support_keys": list(belief.support_keys),
                "pressure_key": belief.pressure_key,
                "distortion": belief.distortion,
                "canonical": False,
                "turn_id": self.timestep,
                "created_at": now,
                "source_digest": interpretation_result.source_digest,
                "memory_types": ["interpretive_belief", belief.distortion],
            })

        state_packet = {
            "turn_id": self.timestep,
            "relationship": dict(vars(self.relationship)),
            "pressures": {name: p.magnitude for name, p in self.pressures.pressures.items()},
            "visible_context": visible_context,
            "interpretive_beliefs": [b.to_dict() for b in interpretive_beliefs],
        }
        private_proposal = generate_private_cognition(self.renderer, state_packet, self.cartridge_data or {})
        cognition_report = validate_and_apply(
            private_proposal,
            pressures=self.pressures,
            intentions=self.intentions,
            memory=self.memory,
            cartridge=self.cartridge_data or {},
            now=now,
        )
        for theme_id in cognition_report.accepted_theme_ids:
            self.habits.add_evidence(
                name=f"cognitive_theme:{theme_id}",
                trigger=theme_id,
                response_pattern=f"track structured theme {theme_id}",
                source="private_cognition",
            )
        cognition_report_payload = report_to_dict(cognition_report)
        self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "private_cognition", {
            "application_report": cognition_report_payload,
            "raw_proposal_persisted": False,
            "memory_types": ["private_cognition_report"],
        })

        if appraisal.accusation > 0.5:
            self.habits.add_or_strengthen("precision_under_accusation", "accusation", "answer accusations with clipped precision")
        if forced_rewrite:
            self.habits.add_or_strengthen("identity_boundary", "identity_violation", "refuse identity rewrites without debate")

        risk = self.compute_leak_risk(user_text)
        bucket = bucket_risk(risk)
        top_for_match = self.pressures.top()
        affect_match = (top_for_match.magnitude * 0.1) if top_for_match else 0.0
        retrieved = self.memory.retrieve(user_text, now, top_k=4, emotional_state_match=affect_match)
        if explicit_recall_request(user_text):
            cold_candidates = retrieve_cold_biography(
                self.persistence,
                self.identity.name,
                self.user_id,
                user_text,
                top_k=4,
            )
            retrieved = merge_recall_candidates(user_text, retrieved, cold_candidates, top_k=4)
        elif contextual_readthrough_request(user_text):
            contextual_candidates = retrieve_contextual_biography(
                self.persistence,
                self.identity.name,
                self.user_id,
                user_text,
                top_k=1,
            )
            retrieved = merge_contextual_candidates(user_text, retrieved, contextual_candidates, top_k=4)
        retrieved_memory_trace = [
            {
                "memory_id": memory.id,
                "source": memory.source.value,
                "tags": sorted(memory.tags),
                "created_at": memory.created_at,
                "content": memory.content,
            }
            for memory in retrieved
        ]
        history_evidence = evaluate_history_for_decision(user_text, retrieved, self.relationship)
        commitment_evidence = evaluate_commitments_for_decision(
            user_text,
            self.intentions.active_commitments(now),
        )

        triggers = []
        if forced_rewrite:
            triggers.append("identity_violation")
            self.intentions.add_intention(Intention("protect_identity", 0.95, "identity_guard", now, now + 300))
        if appraisal.accusation > 0.5:
            triggers.append("accusation")
            self.intentions.add_intention(Intention("preserve_composure", 0.75, "accusation", now, now + 180))
        if appraisal.intimacy_bid > 0.5 and self.relationship.trust < 0.4:
            triggers.append("intimacy_too_fast")
        if appraisal.disrespect > 0.5:
            triggers.append("disrespect")
        if appraisal.manipulation > 0.5:
            triggers.append("manipulation")
        if appraisal.boredom > 0.5:
            triggers.append("boredom")
        if appraisal.contradiction > 0.4:
            triggers.append("contradiction")
        if risk > 0.8:
            triggers.append("emotional_overload")

        selected_intention = self.intentions.select_top(now)
        open_loop = self.intentions.due_open_loop(now)
        symbol = self.symbols.most_relevant(now)
        resistance = select_resistance(triggers)
        decision_payload = self._resolve_decision_payload(
            triggers,
            risk,
            resistance,
            history_evidence=history_evidence.to_dict(),
            commitment_evidence=commitment_evidence.to_dict(),
        )
        if commitment_evidence.active:
            suppression_traces.append(_suppression_trace(
                "commitment_constraint",
                "constrained",
                f"{commitment_evidence.commitment_kind}:{commitment_evidence.commitment_target}",
                "info",
            ))
        if resistance:
            suppression_traces.append(_suppression_trace(
                "resistance_selector",
                "constrained",
                f"selected refusal mode {resistance}",
                "warning",
            ))
        habit_trigger = triggers[0] if triggers else "default"
        habit = self.habits.most_relevant(habit_trigger)

        top_pressure = self.pressures.top()
        dominant_name = top_pressure.accessible_name() if top_pressure else "calm"
        secondary = self.pressures.runner_up()
        secondary_name = secondary.accessible_name() if secondary else None
        envelope = build_envelope(bucket, self.relationship, top_pressure.name if top_pressure else "calm")
        suppression_traces.append(_suppression_trace(
            "expression_envelope",
            "constrained",
            f"bucket={bucket}; tone={envelope.tone_label}; max_chars={envelope.max_chars}",
        ))
        if resistance:
            envelope.refusal_mode = resistance

        frame = WorkspaceFrame(
            core_identity_summary=self.ledger.summary() + (f" | beliefs: {self.belief_ledger.values}" if self.belief_ledger.values else ""),
            relationship_summary=relationship_to_qualitative(self.relationship),
            current_affect_bucket=bucket,
            dominant_pressure=dominant_name,
            secondary_pressure=secondary_name,
            selected_intention=selected_intention.name if selected_intention else None,
            retrieved_memories=[m.content for m in retrieved],
            open_loop=open_loop.topic if open_loop else None,
            shared_symbol=symbol.name if symbol else None,
            active_habit=habit.response_pattern if habit else None,
            situated_summary=self.interface.summary(now),
            world_summary=self.world.summary(),
            body_summary=self.body.summary(),
            sensorium_summary=self.sensorium.summary(),
            access_rules=self.interface.access_rules(),
            expression_envelope=envelope,
            interpretive_beliefs=[b.text for b in interpretive_beliefs],
            interpretive_belief_trace=[b.to_dict() for b in interpretive_beliefs],
            forbidden_claims=list(self.identity.forbidden_self_claims) + [
                "memories not listed in the relevant memory field",
                "private thoughts from the user",
            ],
        )

        second_thoughts = derive_second_thoughts(frame)
        system_prompt = frame.to_system_prompt(self.identity.name, self.identity.temperament)
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_text}]
        seed = turn_seed(self.user_id, self.timestep, "expression")
        response = render_expression(
            self.renderer,
            ledger_digest={"identity": self.identity.name, "beliefs": self.belief_ledger.values},
            resolved_state={"system_prompt": system_prompt, "user_text": user_text},
            arc_context={},
            evidence=[{"type": "input", "text": user_text}, {"type": "interpretation", "beliefs": [b.to_dict() for b in interpretive_beliefs]}],
            retrieved_memories=retrieved,
            private_thought_context="",
            decision_payload=decision_payload,
            expression_constraints={"max_chars": envelope.max_chars},
            deception_obligations=[],
            seed=seed,
        )

        validation_request = ValidationRequest(
            candidate_text=response,
            identity_constraints=tuple(self.identity.forbidden_self_claims),
            interpretive_state=tuple(b.to_dict() for b in interpretive_beliefs),
            relevant_history=tuple(retrieved),
            decision_payload=dict(decision_payload),
            canonical_context={"world": self.world.to_dict()},
            deception_ledger=self.deception_ledger,
        )
        validation = self.consistency.evaluate(validation_request)
        violations = [issue.detail for issue in validation.issues]
        validation_action = validation.action.value
        original_response = response

        if validation.action == ValidationAction.SANITIZE_CONTINUE:
            response = validation.output_text
            suppression_traces.append(_suppression_trace(
                "renderer_sanitizer",
                "sanitized",
                "soft consistency issue repaired locally",
                "warning",
            ))
        elif validation.action == ValidationAction.REGENERATE_CONSTRAINED:
            constraints = regeneration_constraints(validation)
            retry_prompt = system_prompt
            if constraints:
                retry_prompt += "\nCONSISTENCY RETRY CONSTRAINTS: " + "; ".join(constraints)
            response = render_expression(
                self.renderer,
                ledger_digest={"identity": self.identity.name, "beliefs": self.belief_ledger.values},
                resolved_state={"system_prompt": retry_prompt, "user_text": user_text},
                arc_context={},
                evidence=[{"type": "input", "text": user_text}, {"type": "interpretation", "beliefs": [b.to_dict() for b in interpretive_beliefs]}],
                retrieved_memories=retrieved,
                private_thought_context="",
                decision_payload=decision_payload,
                expression_constraints={"max_chars": envelope.max_chars, "consistency_constraints": constraints},
                deception_obligations=[],
                seed=seed,
            )
            retry_validation = self.consistency.evaluate(ValidationRequest(
                candidate_text=response,
                identity_constraints=tuple(self.identity.forbidden_self_claims),
                interpretive_state=tuple(b.to_dict() for b in interpretive_beliefs),
                relevant_history=tuple(retrieved),
                decision_payload=dict(decision_payload),
                canonical_context={"world": self.world.to_dict()},
                deception_ledger=self.deception_ledger,
            ))
            if retry_validation.issues:
                fallback_renderer = LocalLLMRenderer(model_name="missing-model-for-mock", provider="offline")
                response = render_expression(
                    fallback_renderer,
                    ledger_digest={"identity": self.identity.name, "beliefs": self.belief_ledger.values},
                    resolved_state={"system_prompt": system_prompt, "user_text": user_text},
                    arc_context={},
                    evidence=[{"type": "input", "text": user_text}],
                    retrieved_memories=retrieved,
                    private_thought_context="",
                    decision_payload=decision_payload,
                    expression_constraints={"max_chars": envelope.max_chars},
                    deception_obligations=[],
                    seed=seed,
                )
            suppression_traces.append(_suppression_trace(
                "consistency_layer",
                "regenerated",
                "hard renderer inconsistency triggered one bounded retry/fallback",
                "warning",
            ))
        elif validation.action == ValidationAction.FALLBACK_IDENTITY_ONLY:
            fallback_renderer = LocalLLMRenderer(model_name="missing-model-for-mock", provider="offline")
            response = render_expression(
                fallback_renderer,
                ledger_digest={"identity": self.identity.name, "beliefs": self.belief_ledger.values},
                resolved_state={"system_prompt": system_prompt, "user_text": user_text},
                arc_context={},
                evidence=[{"type": "input", "text": user_text}],
                retrieved_memories=retrieved,
                private_thought_context="",
                decision_payload=decision_payload,
                expression_constraints={"max_chars": envelope.max_chars},
                deception_obligations=[],
                seed=seed,
            )
            fallback_validation = self.consistency.evaluate(ValidationRequest(
                candidate_text=response,
                identity_constraints=tuple(self.identity.forbidden_self_claims),
                relevant_history=tuple(retrieved),
                decision_payload=dict(decision_payload),
                canonical_context={"world": self.world.to_dict()},
                deception_ledger=self.deception_ledger,
            ))
            if fallback_validation.issues:
                response = "..."
            suppression_traces.append(_suppression_trace(
                "consistency_layer",
                "fallback",
                "critical renderer inconsistency used deterministic identity-safe fallback",
                "error",
            ))

        if violations:
            suppression_traces.append(_suppression_trace(
                "output_validator",
                "blocked",
                "; ".join(violations),
                "warning",
            ))
            self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "validation", {
                "violations": violations,
                "issues": [
                    {"code": issue.code, "severity": issue.severity.value, "authority_source": issue.authority_source}
                    for issue in validation.issues
                ],
                "action": validation_action,
                "original_response": original_response,
                "final_response": response,
                "suppression_trace": [trace.to_dict() for trace in suppression_traces],
                "memory_types": ["validation"],
            })

        self._appraise_decision_effect(decision_payload, risk, bucket)
        self.interface.mark_output(now)

        self._post_speech_update(user_text, response, risk, appraisal, now, forced_rewrite is not None, suppression_traces)
        self._persist()
        suppression_payload = [trace.to_dict() for trace in suppression_traces]
        memory_types = []
        if appraisal.accusation > 0.5:
            memory_types.append("accusation")
        if appraisal.boundary_violation > 0.5 or forced_rewrite:
            memory_types.append("identity_violation")
        if appraisal.repair_attempt > 0.5:
            memory_types.append("repair_attempt")
        if appraisal.intimacy_bid > 0.5:
            memory_types.append("intimacy_bid")
        if risk > 0.6:
            memory_types.append("high_pressure")
        self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "turn", {
            "user_text": user_text,
            "risk": risk,
            "bucket": bucket,
            "dominant_pressure": dominant_name,
            "decision_payload": decision_payload,
            "cognitive_application_report": cognition_report_payload,
            "appraisal": vars(appraisal),
            "violations": violations,
            "server_truth": server_truth,
            "visible_context": visible_context,
            "suppression_trace": suppression_payload,
            "retrieved_memory_trace": retrieved_memory_trace,
            "memory_types": memory_types or ["neutral_turn"],
        })

        return {
            "response": response,
            "risk": round(risk, 3),
            "bucket": bucket,
            "dominant_pressure": dominant_name,
            "energy": round(self.energy, 3),
            "restlessness": round(self.restlessness, 3),
            "relationship": dict(vars(self.relationship)),
            "violations_caught": violations,
            "validation_action": validation_action,
            "validation_issues": [
                {"code": issue.code, "severity": issue.severity.value, "authority_source": issue.authority_source}
                for issue in validation.issues
            ],
            "suppression_trace": suppression_payload,
            "open_loop": open_loop.topic if open_loop else None,
            "selected_intention": selected_intention.name if selected_intention else None,
            "world": self.world.to_dict(),
            "body": self.body.to_dict(),
            "sensorium": [asdict(e) for e in self.sensorium.recent(6)],
            "system_prompt": system_prompt,
            "interpretive_beliefs": [b.text for b in interpretive_beliefs],
            "interpretive_belief_trace": [b.to_dict() for b in interpretive_beliefs],
            "interpretation_source_digest": interpretation_result.source_digest,
            "decision_payload": decision_payload,
            "cognitive_application_report": cognition_report_payload,
            "retrieved_memory_trace": retrieved_memory_trace,
            "public_status": self.public_status(bucket, dominant_name),
            "avatar_state": self.public_status(bucket, dominant_name)["avatar_state"],
            "avatar_projection": self.avatar_projection(bucket, dominant_name),
            "voice_plan": self.plan_voice(response, envelope),
            "second_thoughts": second_thoughts,
            "proactive_events": self.poll_proactive_events(),
            "stream_plan": {
                "source": "core_engine",
                "response_text_ready": True,
                "second_thoughts_from_workspace": bool(second_thoughts),
            },
        }

    def _appraise_decision_effect(self, decision_payload: dict[str, Any], risk: float, bucket: str):
        """Apply consequences of the character's resolved conduct, not renderer wording.

        Renderer punctuation or lexical choice must not become a hidden write path
        into affective state. Future speech-plan effects belong here only when they
        are represented as typed semantic decisions.
        """

        dialogue_act = str((decision_payload or {}).get("dialogue_act", "respond"))
        if bucket == "HIGH" and dialogue_act in {"protect_boundary", "withdraw", "challenge"}:
            top = self.pressures.top()
            if top:
                top.magnitude = max(0.0, top.magnitude - 0.08)
            if dialogue_act in {"protect_boundary", "challenge"}:
                self.relationship.tension = min(1.0, self.relationship.tension + 0.02)

    def _post_speech_update(self, user_text, response, risk, appraisal, now, identity_violation: bool, suppression_traces: list[SuppressionTrace] | None = None):
        # Memory firewall: generated wording is logged as speech evidence, not
        # promoted as objective truth. Canonical memory records the user input
        # and appraisal. The response is event-log data only.
        if suppression_traces is not None:
            suppression_traces.append(_suppression_trace(
                "memory_firewall",
                "logged_only",
                "renderer speech logged as noncanonical evidence",
            ))
        mem = MemoryUnit(
            content=f"I heard you say: {user_text[:120]}",
            created_at=now,
            emotional_valence=-0.3 if risk > 0.6 else 0.2,
            emotional_intensity=max(risk, appraisal.accusation, appraisal.threat, appraisal.boundary_violation),
            relationship_relevance=0.6,
            identity_relevance=0.7 if identity_violation else 0.2,
            unresolved=appraisal.accusation > 0.5 or appraisal.boundary_violation > 0.5 or identity_violation,
            source=KnowledgeSource.USER_TOLD,
            tags={"identity", "canonical_user_statement"} if identity_violation else {"canonical_user_statement"},
        )
        self.memory.add(mem)
        self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "speech", {
            "response": response,
            "response_is_canonical_truth": False,
            "suppression_trace": [trace.to_dict() for trace in (suppression_traces or [])],
            "memory_types": ["speech"],
        })

        if mem.unresolved:
            self.intentions.add_open_loop(OpenLoop(
                topic=f"unresolved tension from: {user_text[:40]}",
                emotional_charge=mem.emotional_intensity,
                created_at=now,
                last_touched=now,
                urgency=max(risk, mem.emotional_intensity),
                preferred_resolution="revisit when trust is higher",
            ))
        if risk > 0.6:
            top = self.pressures.top()
            if top:
                top.magnitude = max(0.0, top.magnitude - 0.15)
