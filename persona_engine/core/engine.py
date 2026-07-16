"""Interior engine.

Pipeline:
Input -> wall-clock catch-up -> identity guard -> appraisal -> relationship and
pressure update -> interpretation -> memory retrieval -> intention/open-loop/habit selection ->
workspace frame -> renderer -> validator -> canonical writeback -> event-log persistence.
"""

import json
import time
import threading
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
from .persistence import Persistence
from .relationship import RelationshipState, appraise_event, apply_appraisal, relationship_to_qualitative
from .private_cognition import execute_private_cognition, report_to_dict, validate_and_apply
from .renderer import LocalLLMRenderer, OutputValidator, render_expression
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
from .lived_experience import ExperienceStore, WorldEvent, WorldEventLedger
from .embedding import NoEmbeddingProvider
from .capability_artifacts import CapabilityArtifactStore
from .imperfect_action import ImperfectActionEngine
from .action import ActionDecision, CommunicativeCandidate, resolve_action_decision
from .intrinsic import IntrinsicMotivationEngine, IntrinsicProposal, IntrinsicState
from .performance import PerformancePlan, PerformancePlanner, PerformanceProfile
from .vitality import LifeState, VitalityEventEngine
from .synthesis import (
    ActionCompletion,
    SynthesisInfluence,
    SynthesisResult,
    derive_integration_capacity,
    synthesize,
)
from .event_classifier import EventClassifier, can_promote_to_canonical_memory
from .sensory_router import SensoryRouter
from .audio_sensor import AudioObservation
from .vision_sensor import VisionObservation
from .voice import VoiceProfile, VoicePlanner
from .avatar import AvatarProfile, AvatarProjector
from .suppression import SuppressionTrace
from .semantic_substrate import SemanticActivationFrame, load_default_substrate
from .self_monitor import SelfMonitor, SelfMonitorProfile, SelfMonitorResult


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
    def __init__(self, identity: CoreIdentity | None = None, user_id: str = "default_user", db_path: str = "persona_state.db", cartridge_path: str | None = None):
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
        self.memory = MemoryStore(embedding_provider=NoEmbeddingProvider())
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
        self.world_events = WorldEventLedger()
        self.experiences = ExperienceStore()
        self.capability_artifacts = CapabilityArtifactStore()
        life_seed = turn_seed(f"{identity.name}:{user_id}", 0, "vitality")
        self.life_state = LifeState()
        self.vitality = VitalityEventEngine(life_seed)
        self.imperfect_actions = ImperfectActionEngine(turn_seed(f"{identity.name}:{user_id}", 0, "action"))
        self.intrinsic = IntrinsicMotivationEngine.from_cartridge(profile_source.get("intrinsic"))
        self.intrinsic_state = IntrinsicState()
        self._last_intrinsic_proposal: IntrinsicProposal | None = None
        self._last_action_decision: ActionDecision | None = None
        self.performance_planner = PerformancePlanner()
        self._last_performance_plan: PerformancePlan | None = None
        self._last_model_call_metrics: dict[str, Any] = {
            "private_cognition_renderer_called": False,
            "expression_renderer_called": False,
            "total_model_calls": 0,
        }
        cognition_config = dict(profile_source.get("private_cognition", {}))
        self.private_cognition_mode = str(cognition_config.get("mode", "deterministic"))
        self.private_cognition_optional_threshold = float(cognition_config.get("optional_threshold", 0.65))
        self.self_monitor_profile = SelfMonitorProfile.from_dict(profile_source.get("self_monitor"))
        self.self_monitor = SelfMonitor(self.self_monitor_profile)
        self._last_self_monitor: SelfMonitorResult | None = None
        self.last_catch_up_summary: dict[str, Any] = {"elapsed_seconds": 0.0, "tide_steps": 0, "life_steps": 0, "life_events": []}
        self._last_synthesis: SynthesisResult | None = None
        self._last_action_completion: ActionCompletion | None = None
        self.semantic_substrate = load_default_substrate()
        self._last_semantic_activation: SemanticActivationFrame | None = None
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
        self.renderer = LocalLLMRenderer(model_name=identity.model_name)
        self.validator = OutputValidator()
        self.persistence = Persistence(db_path)
        self.deception_ledger = DeceptionLedger()
        self.dream_engine = DreamEngine(self.persistence, self.belief_ledger)

        self.energy = 0.8
        self.restlessness = 0.2
        self.timestep = 0
        self.last_wall_time = time.time()
        self.last_reflection_time = 0.0

        self._load_state()

    def set_renderer(self, renderer) -> None:
        """Replace only the surface renderer through an approved host channel."""

        self.renderer = renderer

    def set_private_cognition_mode(self, mode: str, optional_threshold: float | None = None) -> None:
        """Configure this session's bounded private-cognition capability."""

        if mode not in {"deterministic", "model_optional", "model_required"}:
            raise ValueError(f"unsupported private cognition mode: {mode}")
        self.private_cognition_mode = mode
        if optional_threshold is not None:
            threshold = float(optional_threshold)
            if not 0.0 <= threshold <= 1.0:
                raise ValueError("private cognition threshold must be within [0, 1]")
            self.private_cognition_optional_threshold = threshold

    def renderer_status(self) -> dict:
        status = getattr(self.renderer, "runtime_status", None)
        if callable(status):
            return status()
        return {"requested_provider": "custom", "actual_provider": "custom", "model_name": type(self.renderer).__name__}

    # ---------------- persistence ----------------
    def _load_state(self):
        cid, uid = self.identity.name, self.user_id
        meta = self.persistence.load(cid, uid, "meta", {})
        self.energy = meta.get("energy", self.energy)
        self.restlessness = meta.get("restlessness", self.restlessness)
        self.timestep = meta.get("timestep", self.timestep)
        self.last_wall_time = meta.get("last_wall_time", self.last_wall_time)
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
                confidence=m.get("confidence", 1.0),
                salience=m.get("salience", 0.5),
                provenance=dict(m.get("provenance", {})),
                source_tier=m.get("source_tier", 0),
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
        for t in self.persistence.load(cid, uid, "earned_traits", []):
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
        self.world_events = WorldEventLedger.from_list(self.persistence.load(cid, uid, "world_events", []))
        self.experiences = ExperienceStore.from_list(self.persistence.load(cid, uid, "subjective_experiences", []))
        self.capability_artifacts = CapabilityArtifactStore.from_list(self.persistence.load(cid, uid, "capability_artifacts", []))
        self.life_state = LifeState.from_dict(self.persistence.load(cid, uid, "life_state"))
        self.intrinsic_state = IntrinsicState.from_dict(self.persistence.load(cid, uid, "intrinsic_state"))
        last_proposal = self.persistence.load(cid, uid, "last_intrinsic_proposal")
        last_decision = self.persistence.load(cid, uid, "last_action_decision")
        if last_proposal:
            self._last_intrinsic_proposal = IntrinsicProposal.from_dict(last_proposal)
        elif last_decision and "schema_version" not in last_decision:
            # v12 migration: the old key held an intrinsic selection, not a
            # canonical situated action.
            migrated = dict(last_decision)
            migrated["proposal_id"] = migrated.pop("decision_id")
            migrated["proposed_action_kind"] = migrated.pop("action_type")
            migrated["performance_tendency_id"] = None
            migrated.pop("performance_cue", None)
            migrated.pop("requires_renderer", None)
            self._last_intrinsic_proposal = IntrinsicProposal.from_dict(migrated)
        self._last_action_decision = (
            ActionDecision.from_dict(last_decision)
            if last_decision and "schema_version" in last_decision else None
        )
        last_performance = self.persistence.load(cid, uid, "last_performance_plan")
        self._last_performance_plan = PerformancePlan.from_dict(last_performance) if last_performance else None
        self._last_model_call_metrics = self.persistence.load(
            cid, uid, "last_model_call_metrics", self._last_model_call_metrics,
        )
        last_monitor = self.persistence.load(cid, uid, "last_self_monitor")
        self._last_self_monitor = SelfMonitorResult.from_dict(last_monitor) if last_monitor else None
        action_meta = self.persistence.load(cid, uid, "imperfect_action", {})
        self.imperfect_actions.counter = int(action_meta.get("counter", 0))

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
                "confidence": m.confidence,
                "salience": m.salience,
                "provenance": m.provenance,
                "source_tier": m.source_tier,
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
            "sensorium": self.sensorium.to_dict(),
            "belief_ledger": self.belief_ledger.to_state(),
            "world_authority": self.world_authority.to_list(),
            "world_events": self.world_events.to_list(),
            "subjective_experiences": self.experiences.to_list(),
            "capability_artifacts": self.capability_artifacts.to_list(),
            "life_state": self.life_state.to_dict(),
            "intrinsic_state": self.intrinsic_state.to_dict(),
            "last_intrinsic_proposal": self._last_intrinsic_proposal.to_dict() if self._last_intrinsic_proposal else None,
            "last_action_decision": self._last_action_decision.to_dict() if self._last_action_decision else None,
            "last_performance_plan": self._last_performance_plan.to_dict() if self._last_performance_plan else None,
            "last_model_call_metrics": dict(self._last_model_call_metrics),
            "last_self_monitor": self._last_self_monitor.to_dict() if self._last_self_monitor else None,
            "imperfect_action": {"counter": self.imperfect_actions.counter},
            "deception_ledger": self.deception_ledger.to_state(),
        }

    def _persist(self):
        self.persistence.save_many(self.identity.name, self.user_id, self._serialize_state())

    # ---------------- idle and silent processing ----------------
    def _catch_up_idle(self):
        now = time.time()
        elapsed = max(0.0, now - self.last_wall_time)
        self.last_wall_time = now
        steps = min(int(elapsed / 5.0), 200)
        for _ in range(steps):
            self._run_single_idle_cycle(elapsed_seconds=5.0, include_vitality=False)
        life_events = self.vitality.catch_up(
            self.life_state,
            self.timestep,
            elapsed,
            max_steps=12,
            whim_weights=self._whim_weights(),
        )
        self.experiences.decay(now)
        self.last_catch_up_summary = {
            "elapsed_seconds": round(elapsed, 3),
            "tide_steps": steps,
            "life_steps": self.life_state.last_catch_up_steps,
            "life_events": [event.to_dict() for event in life_events],
        }
        self.timestep += steps

    def run_idle_cycle(self):
        self._run_single_idle_cycle(elapsed_seconds=5.0)
        self.timestep += 1
        self.last_wall_time = time.time()
        self._persist()

    def _run_single_idle_cycle(self, elapsed_seconds: float = 5.0, include_vitality: bool = True):
        now = time.time()
        total_pressure = sum(p.magnitude for p in self.pressures.pressures.values())
        self.energy = max(0.1, self.energy - total_pressure * 0.01)
        self.restlessness = min(1.0, self.restlessness + 0.02)
        self.pressures.decay_all()
        self.organism_tick.idle(
            elapsed_seconds=elapsed_seconds,
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
        proposal = self._advance_intrinsic_motivation()
        if proposal is not None:
            self._resolve_idle_intrinsic_proposal(proposal, now)
        if include_vitality:
            self.experiences.decay(now)
            life_events = self.vitality.tick(self.life_state, self.timestep, elapsed_seconds, self._whim_weights())
            for event in life_events:
                self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "life_event", event.to_dict())
        if (self.energy < 0.3 or self.relationship.unresolved_conflict > 0.6) and (now - self.last_reflection_time > 300):
            self._trigger_reflection(now)

    def _trigger_reflection(self, now: float):
        top_mems = self.memory.retrieve("reflection on recent unresolved events", now, top_k=3)
        if not top_mems:
            return
        unresolved = [m for m in top_mems if m.unresolved]
        ids = [m.id for m in top_mems]
        confidence = min(0.9, 0.45 + 0.15 * len(unresolved) + sum(m.identity_relevance for m in top_mems) / 10.0)
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
                self.run_idle_cycle()

        self._idle_thread = threading.Thread(target=_loop, daemon=True)
        self._idle_thread.start()

    def stop_background_idle(self):
        self._idle_stop.set()
        if self._idle_thread and self._idle_thread.is_alive():
            self._idle_thread.join(timeout=1.0)

    def _whim_weights(self) -> dict[str, float]:
        vitality = (self.cartridge_data or {}).get("vitality", {})
        weights = vitality.get("whim_weights", {}) if isinstance(vitality, dict) else {}
        return {str(key): float(value) for key, value in weights.items()} if isinstance(weights, dict) else {}

    def _advance_intrinsic_motivation(self, force: bool = False) -> IntrinsicProposal | None:
        proposal = self.intrinsic.select(
            self.intrinsic_state,
            companion_id=str((self.cartridge_data or {}).get("metadata", {}).get("entity_id", self.identity.name)),
            tick=self.timestep,
            energy=self.energy,
            restlessness=self.restlessness,
            pressures={name: pressure.magnitude for name, pressure in self.pressures.pressures.items()},
            force=force,
        )
        if proposal is None:
            return None
        self._last_intrinsic_proposal = proposal
        self.intentions.add_intention(Intention(
            name=proposal.intention,
            priority=max(0.0, min(1.0, proposal.utility / 2.0)),
            source=f"intrinsic:{proposal.proposal_id}",
            created_at=time.time(),
            expires_at=None,
            requires_user_context=False,
        ))
        self.persistence.log_event(
            self.identity.name,
            self.user_id,
            self.timestep,
            "intrinsic_proposal",
            {**proposal.to_dict(), "memory_types": ["intrinsic_proposal"]},
        )
        return proposal

    def _accept_action_decision(
        self,
        decision: ActionDecision,
        proposal: IntrinsicProposal | None = None,
    ) -> None:
        self._last_action_decision = decision
        if proposal is not None and decision.source == f"intrinsic:{proposal.proposal_id}":
            if decision.action_kind in {"continue_activity", "observe", "gesture", "silence", "world_action"}:
                self.life_state.current_activity = proposal.activity_description[:120]
                self.life_state.current_intention = proposal.intention[:120]
                self.life_state.attention_target = proposal.target[:120]
                self.life_state.activity_status = "active"
        self.persistence.log_event(
            self.identity.name,
            self.user_id,
            self.timestep,
            "action_decision",
            {
                **decision.to_dict(),
                "record_authority": "canonical_cognitive_record",
                "memory_types": ["action_decision"],
            },
        )

    def _resolve_idle_intrinsic_proposal(self, proposal: IntrinsicProposal, now: float) -> ActionDecision:
        influences = self._build_synthesis_influences(
            "", (), None, (), now, None, proposal,
        )
        synthesis = synthesize(influences, self.integration_capacity())
        selected_intention = next(
            (item for item in self.intentions.intentions if item.name == proposal.intention),
            None,
        )
        decision = resolve_action_decision(
            tick=self.timestep,
            synthesis=synthesis,
            selected_intention=selected_intention,
            selected_habit=None,
            intrinsic_proposal=proposal,
            dialogue_act="none",
            resistance=None,
            current_activity=self.life_state.current_activity,
            interruption={},
            current_pressure=self.pressures.top().magnitude if self.pressures.top() else 0.0,
        )
        self._last_synthesis = synthesis
        self._accept_action_decision(decision, proposal)
        plan = self.performance_planner.plan(
            decision=decision,
            relationship=self.relationship,
            pressures=self.pressures,
            capacity=synthesis.integration_capacity,
            interruption={},
            performance_profile=PerformanceProfile.from_cartridge_tendency(
                (self.cartridge_data or {}).get("performance_tendencies", {}),
                proposal.performance_tendency_id,
            ),
        )
        self._last_performance_plan = plan
        self.persistence.log_event(
            self.identity.name, self.user_id, self.timestep, "performance_plan",
            {
                **plan.to_dict(),
                "record_authority": "deterministic_performance_record",
                "memory_types": ["performance_plan"],
            },
        )
        return decision

    def select_intrinsic_action(self, force: bool = True) -> dict[str, Any] | None:
        """Generate and persist one cartridge-authored proposal."""

        proposal = self._advance_intrinsic_motivation(force=force)
        self._persist()
        return proposal.to_dict() if proposal else None

    def resolve_intrinsic_proposal(self) -> dict[str, Any]:
        """Resolve the latest proposal through synthesis for explicit hosts/tests."""

        if self._last_intrinsic_proposal is None:
            raise RuntimeError("no intrinsic proposal has been selected")
        decision = self._resolve_idle_intrinsic_proposal(self._last_intrinsic_proposal, time.time())
        self._persist()
        return decision.to_dict()

    def complete_intrinsic_action(
        self,
        *,
        observed_outcome: str,
        objective_cause: str,
        expected_outcome: str = "success",
        objectively_reasonable: bool = True,
        skill: float = 0.65,
        distraction: float = 0.0,
        force_execution_failure: bool = False,
        force_wrong_learning: bool = False,
        now: float | None = None,
    ) -> dict[str, Any]:
        """Resolve the selected action through existing outcome and memory channels."""

        decision = self._last_action_decision
        proposal = self._last_intrinsic_proposal
        if decision is None or proposal is None or decision.source != f"intrinsic:{proposal.proposal_id}":
            raise RuntimeError("no intrinsic proposal has become the canonical action")
        result = self.attempt_imperfect_action(
            decision=proposal.activity_description,
            objectively_reasonable=objectively_reasonable,
            skill=skill,
            distraction=distraction,
            fatigue=max(0.0, 1.0 - self.energy),
            observed_outcome=observed_outcome,
            objective_cause=objective_cause,
            now=time.time() if now is None else float(now),
            expected_outcome=expected_outcome,
            intention_id=decision.intention_id,
            supporting_event_ids=(),
            force_execution_failure=force_execution_failure,
            force_wrong_learning=force_wrong_learning,
        )
        self.habits.add_evidence(
            name=f"intrinsic:{proposal.activity_id}",
            trigger=proposal.want_id,
            response_pattern=proposal.activity_description,
            source="expressed_action",
        )
        completion = result["completion"]
        satisfaction = self.intrinsic.apply_completion(
            self.intrinsic_state,
            proposal,
            succeeded=completion["outcome_status"] == "succeeded",
            execution_quality=float(completion["execution_quality"]),
        )
        result["intrinsic_satisfaction_applied"] = satisfaction
        self._persist()
        return result

    def force_life_event(self, category: str) -> list[dict[str, Any]]:
        events = self.vitality.tick(self.life_state, self.timestep, 5.0, self._whim_weights(), force_category=category)
        for event in events:
            self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "life_event", event.to_dict())
        self._persist()
        return [event.to_dict() for event in events]

    def record_world_event(self, *, event_type: str, actors=(), location="unknown", action="observed",
                           targets=(), outcome="", source="host", payload=None, timestamp: float | None = None) -> WorldEvent:
        event = self.world_events.create(
            tick=self.timestep, timestamp=time.time() if timestamp is None else timestamp, event_type=event_type,
            actors=actors, location=location, action=action, targets=targets, outcome=outcome,
            source=source, payload=payload,
        )
        self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "objective_world_event", event.to_dict())
        return event

    def _record_resolved_experience(self, *, event_type: str, action: str, outcome: str, source: str,
                                    targets=(), timestamp: float | None = None, confidence: float = 0.8,
                                    salience: float = 0.45) -> tuple[WorldEvent, Any]:
        event = self.record_world_event(
            event_type=event_type,
            actors=(self.identity.name,),
            location=str(self.world.zone),
            action=action,
            targets=targets,
            outcome=outcome,
            source=source,
            timestamp=timestamp,
        )
        experience = self.experiences.perceive(
            event, self.identity.name, attention=confidence, confidence=confidence,
            salience=salience, emotional_residue="neutral", interpretation="bounded observation",
        )
        if experience:
            self.experiences.consolidate(experience, self.memory, event.timestamp)
            self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "subjective_experience", experience.to_dict())
        return event, experience

    def perceive_world_event(self, event_id: str, *, attention: float = 0.8, confidence: float = 0.8,
                             salience: float = 0.5, emotional_residue: str = "neutral",
                             interpretation: str = "ordinary", source_tier: int = 0,
                             distortion: dict[str, Any] | None = None, consolidate: bool = True):
        event = self.world_events.fetch(event_id)
        if event is None:
            raise KeyError(event_id)
        experience = self.experiences.perceive(
            event, self.identity.name, attention=attention, confidence=confidence, salience=salience,
            emotional_residue=emotional_residue, interpretation=interpretation,
            source_tier=source_tier, distortion=distortion,
        )
        if experience and consolidate:
            self.experiences.consolidate(experience, self.memory, event.timestamp)
        if experience:
            self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "subjective_experience", experience.to_dict())
        self._persist()
        return experience

    def attempt_imperfect_action(self, **kwargs) -> dict[str, Any]:
        expected_outcome = str(kwargs.pop("expected_outcome", "success"))
        intention_id = kwargs.pop("intention_id", None)
        synthesis_reference = kwargs.pop("synthesis_reference", None)
        attempt = self.imperfect_actions.attempt(artifacts=self.capability_artifacts, **kwargs)
        self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "action_attempt", attempt.to_dict())
        self.world_authority.apply_host_event(
            {"action_outcome": attempt.observed_outcome},
            source="action_resolution",
            visible=True,
        )
        world_event = self.record_world_event(
            event_type="action_completion",
            actors=(self.identity.name,),
            location=str(self.world.zone),
            action=attempt.decision,
            outcome=attempt.observed_outcome,
            source="world_authority",
            payload={"objective_cause": attempt.objective_cause, "succeeded": attempt.succeeded},
            timestamp=float(kwargs.get("now", time.time())),
        )
        artifact = next(
            (item for item in self.capability_artifacts.artifacts if item.artifact_id == attempt.learned_artifact_id),
            None,
        )
        interpretation = artifact.content if artifact else (
            "the outcome matched my attempt" if attempt.succeeded else "the attempt did not produce the expected result"
        )
        experience = self.experiences.perceive(
            world_event,
            self.identity.name,
            attention=max(0.2, 1.0 - float(kwargs.get("distraction", 0.0))),
            confidence=0.62 if artifact else 0.78,
            salience=0.72 if not attempt.succeeded else 0.58,
            emotional_residue="frustration" if not attempt.succeeded else "relief",
            interpretation=interpretation,
            distortion={"learned_artifact_id": attempt.learned_artifact_id} if artifact else {},
        )
        if experience:
            self.experiences.consolidate(experience, self.memory, world_event.timestamp, force=True)
            self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "subjective_experience", experience.to_dict())
        burden = (float(kwargs.get("distraction", 0.0)) + float(kwargs.get("fatigue", 0.0))) / 2.0
        execution_quality = max(0.0, min(1.0, float(kwargs.get("skill", 0.0)) * (1.0 - max(0.0, min(1.0, burden)) * 0.65)))
        discrepancy = "none" if expected_outcome.strip().lower() == attempt.observed_outcome.strip().lower() else "expected_and_actual_differ"
        completion = ActionCompletion(
            intention_id=str(intention_id) if intention_id is not None else (self._last_synthesis.selected_intention_id if self._last_synthesis else None),
            attempted_action=attempt.decision,
            world_event_id=world_event.event_id,
            outcome_status="succeeded" if attempt.succeeded else "failed",
            execution_quality=round(execution_quality, 6),
            expected_outcome=expected_outcome,
            actual_outcome=attempt.observed_outcome,
            discrepancy=discrepancy,
            synthesis_reference=str(synthesis_reference) if synthesis_reference is not None else (self._last_synthesis.synthesis_id if self._last_synthesis else None),
            subjective_interpretation_reference=experience.experience_id if experience else None,
        )
        self._last_action_completion = completion
        self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "action_completion", {
            **completion.to_dict(),
            "memory_types": ["action_completion"],
        })
        self._persist()
        return {**attempt.to_dict(), "completion": completion.to_dict()}

    def add_capability_artifact(self, **kwargs):
        artifact = self.capability_artifacts.add(**kwargs)
        self._persist()
        return artifact

    def begin_activity(self, activity: str, intention: str, attention_target: str) -> dict[str, Any]:
        self.life_state.current_activity = str(activity)[:120]
        self.life_state.current_intention = str(intention)[:120]
        self.life_state.attention_target = str(attention_target)[:120]
        self.life_state.activity_status = "active"
        self._persist()
        return self.life_state.to_dict()

    def reinforce_habit(self, name: str, trigger: str, response_pattern: str, repetitions: int = 1) -> dict[str, Any]:
        for _ in range(max(1, min(20, int(repetitions)))):
            self.habits.add_or_strengthen(str(name), str(trigger), str(response_pattern), delta=0.08)
        self._persist()
        return asdict(self.habits.habits[str(name)])

    def decay_pressures_for_elapsed_time(self, dt_steps: int) -> float:
        self.pressures.decay_all(dt_steps=max(0, min(1000, int(dt_steps))))
        self._persist()
        return self.integration_capacity()

    def integration_capacity(self) -> float:
        top = self.pressures.top()
        recent_failure = 1.0 if self._last_action_completion and self._last_action_completion.outcome_status == "failed" else 0.0
        interruption_load = 1.0 if self.life_state.activity_status == "interrupted" else 0.0
        energy = (float(self.energy) + float(self.body.energy)) / 2.0
        return derive_integration_capacity(
            energy=energy,
            fatigue=self.body.fatigue,
            sensory_load=self.body.sensory_load,
            dominant_pressure=top.magnitude if top else 0.0,
            unresolved_conflict=self.relationship.unresolved_conflict,
            open_loop_count=len(self.intentions.open_loops),
            interruption_load=interruption_load,
            recent_failure=recent_failure,
        )

    def _build_synthesis_influences(
        self, user_text: str, retrievals, habit, artifacts, now: float,
        semantic_frame: SemanticActivationFrame | None = None,
        intrinsic_proposal: IntrinsicProposal | None = None,
    ) -> list[SynthesisInfluence]:
        influences = [SynthesisInfluence(
            "evidence:current_input", "evidence", str(user_text)[:120], 0.58,
            immediate=True, reality_support=1.0,
        )]
        if semantic_frame is not None:
            for concept in semantic_frame.concepts[:3]:
                influences.append(SynthesisInfluence(
                    f"semantic:{concept.concept_id}", "semantic_candidate", concept.name,
                    min(0.52, 0.18 + concept.activation / 300.0),
                    reality_support=0.0,
                ))
        if intrinsic_proposal is not None:
            normalized_utility = max(0.10, min(0.90, 0.25 + intrinsic_proposal.utility * 0.35))
            influences.append(SynthesisInfluence(
                f"intrinsic:{intrinsic_proposal.proposal_id}",
                "intrinsic_proposal",
                intrinsic_proposal.intention,
                normalized_utility,
                immediate=not intrinsic_proposal.interruptible,
            ))
        for pressure in sorted(self.pressures.pressures.values(), key=lambda item: (-item.magnitude, item.name))[:3]:
            if pressure.magnitude > 0.001:
                influences.append(SynthesisInfluence(
                    f"pressure:{pressure.name}", "pressure", pressure.accessible_name(), pressure.magnitude,
                    immediate=pressure.magnitude >= 0.55,
                ))
        for item in retrievals[:6]:
            memory = item.memory
            contradiction = bool({"contradictory", "contradictory_evidence", "counterevidence"} & memory.tags)
            reality = 0.9 if any(tag.startswith("world_event:") for tag in memory.tags) else 0.75 if "canonical_user_statement" in memory.tags else 0.35
            influences.append(SynthesisInfluence(
                f"memory:{memory.id}", "memory", memory.content[:120],
                min(1.0, 0.30 + memory.salience * 0.35 + memory.emotional_intensity * 0.25),
                emotional_congruence=memory.emotional_intensity,
                contradictory=contradiction,
                reality_support=reality,
            ))
        for artifact in artifacts[:4]:
            reality = 1.0 if artifact.canonicality == "objective" else 0.75 if artifact.verification_state == "verified" else 0.5
            influences.append(SynthesisInfluence(
                f"artifact:{artifact.artifact_id}", "evidence", artifact.content[:120],
                min(1.0, 0.25 + artifact.confidence * 0.55),
                contradictory=artifact.verification_state == "challenged",
                reality_support=reality,
            ))
        for intention in sorted(self.intentions.intentions, key=lambda item: (-item.priority, item.name))[:3]:
            if intention.expires_at is None or intention.expires_at > now:
                influences.append(SynthesisInfluence(
                    f"intention:{intention.name}", "intention", intention.name, intention.priority,
                    immediate=intention.priority >= 0.85,
                ))
        for loop in sorted(self.intentions.open_loops, key=lambda item: (-item.urgency, item.topic))[:2]:
            influences.append(SynthesisInfluence(
                f"open_loop:{loop.topic}", "open_loop", loop.topic[:120],
                min(1.0, (loop.urgency + loop.emotional_charge) / 2.0),
                immediate=loop.urgency >= 0.75,
            ))
        if habit is not None:
            influences.append(SynthesisInfluence(
                f"habit:{habit.name}", "habit", habit.response_pattern,
                min(1.0, habit.strength + min(0.2, habit.uses * 0.01)),
            ))
        relationship_load = max(self.relationship.tension, self.relationship.unresolved_conflict, self.relationship.guardedness * 0.5)
        if relationship_load > 0.05:
            influences.append(SynthesisInfluence(
                "relationship:current", "relationship_conflict", "current relationship concern",
                relationship_load, immediate=self.relationship.tension >= 0.65,
            ))
        influences.append(SynthesisInfluence(
            "activity:current", "activity", self.life_state.current_activity,
            0.50, immediate=True,
        ))
        if self.life_state.current_intention:
            influences.append(SynthesisInfluence(
                "intention:life", "intention", self.life_state.current_intention,
                0.45,
            ))
        for key, value in (
            ("fatigue", self.body.fatigue),
            ("sensory_load", self.body.sensory_load),
            ("movement_need", self.body.need_for_movement),
        ):
            if value >= 0.25:
                influences.append(SynthesisInfluence(
                    f"need:{key}", "need", key, value, immediate=value >= 0.70,
                ))
        return influences


    # ---------------- public interface projection ----------------
    def public_status(self, affect_bucket: str | None = None, dominant_pressure: str | None = None) -> dict[str, str]:
        """Return categorical public organism status for UI renderers."""

        return public_status_from_engine(self, affect_bucket=affect_bucket, dominant_pressure=dominant_pressure).to_dict()

    def debug_snapshot(self) -> dict:
        """Return private debug state for developer inspection only."""

        return debug_snapshot_from_engine(self)

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
    def dream(self, min_interval_seconds: int = 3600) -> list[str]:
        changed = self.dream_engine.run_idle_pass(self.identity.name, self.user_id, self.belief_rules, min_interval_seconds)
        self._persist()
        return changed

    def export_session_snapshot(self):
        from .session import export_snapshot
        return export_snapshot(self.pressures, self.belief_ledger, self.identity.name)

    def import_session_snapshot(self, snap):
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

    def _resolve_communicative_candidate(
        self, triggers: list[str], risk: float, resistance: str | None = None,
    ) -> CommunicativeCandidate:
        suspicion = self.pressures.pressures.get("suspicion")
        suspicion_value = suspicion.magnitude if suspicion else 0.0
        dialogue_act = "challenge" if suspicion_value >= 0.60 else "respond"
        if resistance == "challenge":
            dialogue_act = "challenge"
        if risk > 0.8:
            dialogue_act = "protect_boundary"
        return CommunicativeCandidate(
            dialogue_act=dialogue_act,
            communicative_function=dialogue_act,
            concealment_mode="none",
            suspicion=round(suspicion_value, 3),
            trigger_ids=tuple(triggers),
        )

    # ---------------- v10 sensory and embodiment plumbing ----------------
    def ingest_audio_observation(self, observation: AudioObservation) -> dict:
        """Route a bounded audio observation through world authority.

        Audio modules cannot mutate pressure or relationship state directly.
        """
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
        self._record_resolved_experience(
            event_type="audio_observation", action="heard", outcome=routed.resolution.reason,
            source="audio_sensor", targets=tuple(fact.key for fact in routed.resolution.facts_created),
            timestamp=observation.created_at, confidence=observation.confidence,
            salience=0.65 if observation.sudden_onset else 0.35,
        )
        self._persist()
        return {"accepted": routed.resolution.accepted, "facts": [f.to_dict() for f in routed.resolution.facts_created], "pressure_unchanged": before_pressures == {name: p.magnitude for name, p in self.pressures.pressures.items()}}

    def ingest_vision_observation(self, observation: VisionObservation) -> dict:
        """Route a bounded vision observation through world authority."""
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
        self._record_resolved_experience(
            event_type="vision_observation", action="saw", outcome=routed.resolution.reason,
            source="vision_sensor", targets=tuple(fact.key for fact in routed.resolution.facts_created),
            timestamp=observation.created_at, confidence=observation.confidence,
            salience=0.6 if observation.scene_change else 0.35,
        )
        self._persist()
        return {"accepted": routed.resolution.accepted, "facts": [f.to_dict() for f in routed.resolution.facts_created], "relationship_unchanged": before_relationship == dict(vars(self.relationship))}

    def propose_world_action(self, action_type: str, payload: dict | None = None, event_time: float | None = None) -> dict:
        proposal = WorldActionProposal(self.identity.name, action_type, dict(payload or {}), float(event_time) if event_time is not None else time.time())
        resolution = self.world_authority.resolve_action(proposal)
        visible = {fact.key: fact.value for fact in resolution.facts_created if fact.visible_to_character}
        self.world.apply_host_facts(visible, visible, now=proposal.created_at)
        self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "world_action_resolution", {
            "action_type": action_type,
            "payload": payload or {},
            "accepted": resolution.accepted,
            "reason": resolution.reason,
            "facts": [f.to_dict() for f in resolution.facts_created],
            "event_time": proposal.created_at,
            "memory_types": ["world_fact", "action_resolution"],
        })
        self._record_resolved_experience(
            event_type="action_resolution", action=action_type, outcome=resolution.reason,
            source="world_authority", targets=tuple(fact.key for fact in resolution.facts_created),
            timestamp=proposal.created_at, confidence=proposal.confidence,
            salience=0.55 if resolution.accepted else 0.45,
        )
        self._persist()
        return {"accepted": resolution.accepted, "reason": resolution.reason, "facts": [f.to_dict() for f in resolution.facts_created]}

    def plan_voice(self, text: str, envelope=None, performance_plan: PerformancePlan | None = None) -> dict:
        if envelope is None:
            top = self.pressures.top()
            risk = bucket_risk(self.compute_leak_risk(""))
            envelope = build_envelope(risk, self.relationship, top.name if top else "calm")
        plan = self.voice_planner.plan(text, performance_plan, envelope)
        self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "voice_plan", {"plan": plan.to_dict(), "memory_types": ["voice_plan"]})
        return plan.to_dict()

    def avatar_projection(
        self,
        affect_bucket: str | None = None,
        dominant_pressure: str | None = None,
        performance_plan: PerformancePlan | None = None,
    ) -> dict:
        status = self.public_status(affect_bucket, dominant_pressure)
        state = self.avatar_projector.project(status, performance_plan)
        self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "avatar_state", {"state": state.to_dict(), "memory_types": ["avatar_state"]})
        return state.to_dict()

    def classify_event_for_memory(self, event_type: str, payload: dict, event_id=None) -> dict:
        classification = self.event_classifier.classify(event_type, payload, event_id=event_id)
        return classification.__dict__

    # ---------------- main turn ----------------
    def receive_input(self, user_text: str, server_truth: dict | None = None, visible_context: dict | None = None,
                      event_time: float | None = None) -> dict:
        self._catch_up_idle()
        self.timestep += 1
        now = float(event_time) if event_time is not None else time.time()
        prior_proposal = self._last_intrinsic_proposal
        prior_interruptible = prior_proposal.interruptible if prior_proposal else True
        submitted_interaction = visible_context if isinstance(visible_context, dict) else {}
        interruption = self.vitality.interrupt(
            self.life_state,
            user_text,
            previous_activity_interruptible=prior_interruptible,
            interruption_sensitivity=float(
                (self.cartridge_data or {}).get("sensory_profile", {}).get("interruption_sensitivity", 0.5)
            ),
            direct_address=submitted_interaction.get("interaction_type") == "character_to_character",
        ).to_dict()
        server_truth = dict(server_truth or {})
        submitted_server_truth = dict(server_truth)
        visible_context = dict(visible_context or {})
        submitted_visible_context = dict(visible_context)
        input_world_event = self.record_world_event(
            event_type="player_interruption",
            actors=(self.user_id,),
            location=str(self.world.zone),
            action="interrupted",
            targets=(self.identity.name,),
            outcome="a player message arrived",
            source="user_input",
            payload={"text": user_text[:500]},
            timestamp=now,
        )
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
        raw_concepts = visible_context.get("concept_ids", ())
        if isinstance(raw_concepts, (str, int)):
            raw_concepts = (raw_concepts,)
        elif not isinstance(raw_concepts, (list, tuple)):
            raw_concepts = ()
        semantic_frame = self.semantic_substrate.activate(raw_concepts)
        self._last_semantic_activation = semantic_frame
        input_payload = {
            "user_text": user_text,
            "server_truth": server_truth,
            "submitted_server_truth": submitted_server_truth,
            "submitted_visible_context": submitted_visible_context,
            "visible_context": visible_context,
            "event_time": now,
            "memory_types": ["user_input"],
        }
        input_classification = self.event_classifier.classify("input", input_payload, event_id=f"turn_{self.timestep}_input")
        input_payload["classification"] = input_classification.__dict__
        input_payload["canonical_truth"] = can_promote_to_canonical_memory("input", input_payload)
        self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "input", input_payload)
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

        top_after_appraisal = self.pressures.top()
        experience = self.experiences.perceive(
            input_world_event,
            self.identity.name,
            attention=0.9 if self.life_state.attention_target != "uncertain" else 0.45,
            confidence=0.82,
            salience=max(0.35, min(1.0, appraisal.accusation + appraisal.intimacy_bid + appraisal.repair_attempt + 0.25)),
            emotional_residue=top_after_appraisal.accessible_name() if top_after_appraisal else "neutral",
            interpretation=interpretive_beliefs[0].text if interpretive_beliefs else "ordinary interruption",
            source_tier=0,
            distortion={"belief_ids": [belief.belief_id for belief in interpretive_beliefs]},
        )
        if experience:
            self.experiences.consolidate(experience, self.memory, now)
            self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "subjective_experience", experience.to_dict())

        state_packet = {
            "turn_id": self.timestep,
            "relationship": dict(vars(self.relationship)),
            "pressures": {name: p.magnitude for name, p in self.pressures.pressures.items()},
            "visible_context": visible_context,
            "interpretive_beliefs": [b.to_dict() for b in interpretive_beliefs],
            "life_context": self.life_state.to_dict(),
            "interruption": interruption,
        }
        cognition_seed = turn_seed(self.user_id, self.timestep, "private_cognition")
        ambiguity_need = 0.75 if any(
            belief.distortion == "uncertain_read" for belief in interpretive_beliefs
        ) else 0.0
        pressure_need = top_after_appraisal.magnitude if top_after_appraisal else 0.0
        cognition_need = max(
            ambiguity_need,
            pressure_need,
            float(self.relationship.unresolved_conflict),
            0.9 if forced_rewrite else 0.0,
        )
        cognition_execution = execute_private_cognition(
            self.renderer,
            state_packet,
            self.cartridge_data or {},
            mode=self.private_cognition_mode,
            need_score=cognition_need,
            optional_threshold=self.private_cognition_optional_threshold,
            seed=cognition_seed,
        )
        private_proposal = cognition_execution.proposal
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
            "execution": cognition_execution.to_dict(),
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
        retrievals = self.memory.retrieve_explained(
            user_text, now, top_k=4, emotional_state_match=affect_match,
            relationship_tags={"canonical_user_statement", "subjective_experience"},
        )
        retrieved = [item.memory for item in retrievals]
        retrieved_memory_trace = [
            {
                "memory_id": item.memory.id,
                "source": item.memory.source.value,
                "tags": sorted(item.memory.tags),
                "created_at": item.memory.created_at,
                "content": item.memory.content,
                "confidence": item.memory.confidence,
                "salience": item.memory.salience,
                "source_tier": item.memory.source_tier,
                "reasons": item.reasons,
            }
            for item in retrievals
        ]
        self._last_retrieved_memory_trace = retrieved_memory_trace

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
        habit_trigger = triggers[0] if triggers else "default"
        habit = self.habits.most_relevant(habit_trigger)
        available_artifacts = self.capability_artifacts.available(0)[:4]
        base_influences = self._build_synthesis_influences(
            user_text, retrievals, habit, available_artifacts, now, semantic_frame,
            self._last_intrinsic_proposal,
        )
        actual_capacity = self.integration_capacity()
        self_monitor = self.self_monitor.evaluate(
            tick=self.timestep,
            actual_capacity=actual_capacity,
            fatigue=self.body.fatigue,
            dominant_pressure=top_for_match.magnitude if top_for_match else 0.0,
            identity_threat=(
                1.0 if forced_rewrite else max(appraisal.disrespect, appraisal.boundary_violation)
            ),
            recent_failure=bool(
                self._last_action_completion
                and self._last_action_completion.outcome_status == "failed"
            ),
            retrieval_confidences=[item.memory.confidence for item in retrievals],
            influences=base_influences,
            stable_seed=turn_seed(self.user_id, self.timestep, "self_monitor"),
        )
        self._last_self_monitor = self_monitor
        regulation_influences = [SynthesisInfluence(
            influence_id=f"regulation:{candidate.candidate_id}",
            kind="regulation",
            label=candidate.kind,
            strength=candidate.strength,
            immediate=candidate.kind in {"pause", "withdraw"},
        ) for candidate in self_monitor.regulation_candidates]
        synthesis = synthesize([*base_influences, *regulation_influences], actual_capacity)
        self._last_synthesis = synthesis
        self.persistence.log_event(
            self.identity.name, self.user_id, self.timestep, "self_monitor",
            {**self_monitor.to_dict(), "memory_types": ["self_monitor"]},
        )
        considered_ids = {item.influence_id for item in synthesis.considered_influences}
        selected_intention = next(
            (item for item in self.intentions.intentions if item.name == synthesis.selected_intention_id),
            None,
        )
        if habit is None or habit.name != synthesis.selected_habit_id:
            habit = None
        if open_loop is not None and f"open_loop:{open_loop.topic}" not in considered_ids:
            open_loop = None
        retrieved = [item.memory for item in retrievals if f"memory:{item.memory.id}" in considered_ids]
        available_artifacts = [
            item for item in available_artifacts
            if f"artifact:{item.artifact_id}" in considered_ids
        ]
        for trace in retrieved_memory_trace:
            trace["considered_in_synthesis"] = f"memory:{trace['memory_id']}" in considered_ids
        synthesis_payload = synthesis.to_dict()
        self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "synthesis", {
            **synthesis_payload,
            "memory_types": ["synthesis"],
        })
        selected_proposal = (
            self._last_intrinsic_proposal
            if self._last_intrinsic_proposal
            and synthesis.selected_intrinsic_proposal_id == self._last_intrinsic_proposal.proposal_id
            else None
        )
        communicative = self._resolve_communicative_candidate(triggers, risk, resistance)
        selected_regulation = self_monitor.candidate(synthesis.selected_regulation_candidate_id)
        action_decision = resolve_action_decision(
            tick=self.timestep,
            synthesis=synthesis,
            selected_intention=selected_intention,
            selected_habit=habit,
            intrinsic_proposal=selected_proposal,
            dialogue_act=communicative.dialogue_act,
            resistance=resistance,
            current_activity=self.life_state.current_activity,
            interruption=interruption,
            current_pressure=top_after_appraisal.magnitude if top_after_appraisal else 0.0,
            selected_regulation=selected_regulation,
        )
        self._accept_action_decision(action_decision, selected_proposal)
        decision_payload = {
            **communicative.to_dict(),
            "challenge_threshold": 0.60,
            "synthesis_reference": synthesis.synthesis_id,
            "integration_capacity": synthesis.integration_capacity,
            "field_width": synthesis.field_width,
            "selected_intention_id": synthesis.selected_intention_id,
            "selected_habit_id": synthesis.selected_habit_id,
            "selected_intrinsic_proposal_id": synthesis.selected_intrinsic_proposal_id,
            "selected_regulation_candidate_id": synthesis.selected_regulation_candidate_id,
            "action_decision": action_decision.to_dict(),
        }
        if resistance:
            suppression_traces.append(_suppression_trace(
                "resistance_selector",
                "constrained",
                f"selected refusal mode {resistance}",
                "warning",
            ))
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
        performance_plan = self.performance_planner.plan(
            decision=action_decision,
            relationship=self.relationship,
            pressures=self.pressures,
            capacity=synthesis.integration_capacity,
            concealment_mode=communicative.concealment_mode,
            interruption=interruption,
            performance_profile=PerformanceProfile.from_cartridge_tendency(
                (self.cartridge_data or {}).get("performance_tendencies", {}),
                selected_proposal.performance_tendency_id if selected_proposal else None,
            ),
            self_monitor=self_monitor,
        )
        self._last_performance_plan = performance_plan
        performance_payload = performance_plan.to_dict()
        decision_payload["performance_plan"] = performance_payload
        self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "performance_plan", {
            **performance_payload,
            "record_authority": "deterministic_performance_record",
            "memory_types": ["performance_plan"],
        })

        frame = None
        second_thoughts: list[str] = []
        system_prompt = ""
        if performance_plan.requires_language_renderer:
            frame = WorkspaceFrame(
                core_identity_summary=self.ledger.summary() + (f" | beliefs: {self.belief_ledger.values}" if self.belief_ledger.values else ""),
                relationship_summary=relationship_to_qualitative(self.relationship),
                current_affect_bucket=bucket,
                dominant_pressure=dominant_name,
                secondary_pressure=secondary_name,
                selected_intention=selected_intention.name if selected_intention else None,
                retrieved_memories=[m.content for m in retrieved] + [f"Validated knowledge: {item.content}" for item in available_artifacts],
                open_loop=open_loop.topic if open_loop else None,
                shared_symbol=symbol.name if symbol else None,
                active_habit=habit.response_pattern if habit else None,
                situated_summary=self.interface.summary(now),
                world_summary=(
                    f"{self.world.summary()} | before interruption: {interruption['previous_activity']} | "
                    f"attention: {self.life_state.attention_target} | intention: {self.life_state.current_intention}"
                ),
                body_summary=self.body.summary(),
                sensorium_summary=self.sensorium.summary(),
                access_rules=self.interface.access_rules(),
                expression_envelope=envelope,
                interpretive_beliefs=[b.text for b in interpretive_beliefs],
                interpretive_belief_trace=[b.to_dict() for b in interpretive_beliefs],
                forbidden_claims=["being an AI", "having no feelings", "memories not listed in the relevant memory field", "private thoughts from the user"],
                action_decision=action_decision.to_dict(),
                performance_plan=performance_payload,
                self_monitor_summary=self_monitor.renderer_summary(
                    action_decision.selected_regulation_id
                ),
                style_constraints=(
                    list(self.identity.speech_constraints)
                    + [str((self.cartridge_data or {}).get("voice", {}).get("speaking_style", ""))]
                ),
                semantic_candidates=[
                    f"concept:{item.name}" for item in semantic_frame.concepts[:3]
                ] + [
                    f"affordance_candidate:{item.action}:{item.target_name}"
                    for item in semantic_frame.affordances[:3]
                ],
            )
            second_thoughts = derive_second_thoughts(frame)
            system_prompt = frame.to_system_prompt(self.identity.name, self.identity.temperament)
        seed = turn_seed(self.user_id, self.timestep, "expression")
        response = ""
        violations: list[str] = []
        expression_renderer_called = False
        if performance_plan.requires_language_renderer:
            expression_renderer_called = True
            response = render_expression(
                self.renderer,
                ledger_digest={"identity": self.identity.name, "beliefs": self.belief_ledger.values},
                resolved_state={"system_prompt": system_prompt, "user_text": user_text, "life_context": self.life_state.to_dict()},
                arc_context={},
                evidence=[
                    {"type": "input", "text": user_text},
                    {"type": "interpretation", "beliefs": [b.to_dict() for b in interpretive_beliefs]},
                    {"type": "capability_artifacts", "artifacts": [item.to_dict() for item in available_artifacts]},
                    {"type": "synthesis", "result": synthesis_payload},
                ],
                retrieved_memories=retrieved,
                private_thought_context="",
                decision_payload=decision_payload,
                expression_constraints={
                    "max_chars": envelope.max_chars,
                    "offline_realization": dict((self.cartridge_data or {}).get("offline_expression", {})),
                    "action_decision": action_decision.to_dict(),
                    "performance_plan": performance_payload,
                },
                deception_obligations=[],
                seed=seed,
            )

        violations = self.validator.check(response, retrieved, deception_ledger=self.deception_ledger, decision_payload=decision_payload)
        if violations:
            suppression_traces.append(_suppression_trace(
                "output_validator",
                "blocked",
                "; ".join(violations),
                "warning",
            ))
            original_response = response
            response = self.validator.sanitize(response)
            if response != original_response:
                suppression_traces.append(_suppression_trace(
                    "renderer_sanitizer",
                    "sanitized",
                    "renderer output changed after validator violation",
                    "warning",
                ))
            self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "validation", {
                "violations": violations,
                "original_response": original_response,
                "sanitized_response": response,
                "suppression_trace": [trace.to_dict() for trace in suppression_traces],
                "memory_types": ["validation"],
            })

        model_call_metrics = {
            "private_cognition_renderer_called": cognition_execution.renderer_called,
            "expression_renderer_called": expression_renderer_called,
            "total_model_calls": int(cognition_execution.renderer_called) + int(expression_renderer_called),
            "private_cognition_mode": cognition_execution.mode,
            "private_cognition_reason": cognition_execution.reason,
            "private_cognition_fallback_used": cognition_execution.fallback_used,
        }
        self._last_model_call_metrics = model_call_metrics
        self._apply_action_expression_effect(action_decision, performance_plan, risk)
        self.interface.mark_output(now)

        limitation_active = bool(self.life_state.events and self.life_state.events[-1].category == "limitation" and self.life_state.events[-1].tick >= self.timestep - 1)
        if selected_proposal is not None and action_decision.action_kind != "speak":
            activity_outcome = "continued_selected_action"
        else:
            activity_outcome = self.vitality.resolve_interruption(self.life_state, risk, limitation=limitation_active)

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
            "action_decision": action_decision.to_dict(),
            "cognitive_application_report": cognition_report_payload,
            "appraisal": vars(appraisal),
            "violations": violations,
            "server_truth": server_truth,
            "visible_context": visible_context,
            "suppression_trace": suppression_payload,
            "retrieved_memory_trace": retrieved_memory_trace,
            "turn_seeds": {
                "private_cognition": cognition_seed,
                "self_monitor": turn_seed(self.user_id, self.timestep, "self_monitor"),
                "expression": seed,
            },
            "synthesis": synthesis_payload,
            "performance_plan": performance_payload,
            "model_calls": model_call_metrics,
            "self_monitor": self_monitor.to_dict(),
            "semantic_activation": semantic_frame.to_dict(),
            "life_context": self.life_state.to_dict(),
            "interruption": {**interruption, "outcome": activity_outcome},
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
            "action_decision": action_decision.to_dict(),
            "cognitive_application_report": cognition_report_payload,
            "retrieved_memory_trace": retrieved_memory_trace,
            "turn_seeds": {
                "private_cognition": cognition_seed,
                "self_monitor": turn_seed(self.user_id, self.timestep, "self_monitor"),
                "expression": seed,
            },
            "synthesis": synthesis_payload,
            "performance_plan": performance_payload,
            "model_calls": model_call_metrics,
            "self_monitor": self_monitor.to_dict(),
            "semantic_activation": semantic_frame.to_dict(),
            "life_context": self.life_state.to_dict(),
            "interruption": {**interruption, "outcome": activity_outcome},
            "world_event_id": input_world_event.event_id,
            "subjective_experience_id": experience.experience_id if experience else None,
            "catch_up_summary": dict(self.last_catch_up_summary),
            "public_status": self.public_status(bucket, dominant_name),
            "avatar_state": self.public_status(bucket, dominant_name)["avatar_state"],
            "avatar_projection": self.avatar_projection(bucket, dominant_name, performance_plan),
            "voice_plan": self.plan_voice(response, envelope, performance_plan) if performance_plan.requires_language_renderer else None,
            "observable_action": performance_plan.to_public_dict(),
            "second_thoughts": second_thoughts,
            "proactive_events": self.poll_proactive_events(),
            "stream_plan": {
                "source": "core_engine",
                "response_text_ready": performance_plan.requires_language_renderer,
                "second_thoughts_from_workspace": bool(second_thoughts),
            },
        }

    def _apply_action_expression_effect(
        self,
        decision: ActionDecision,
        performance_plan: PerformancePlan,
        risk: float,
    ) -> None:
        """Apply bounded consequences from canonical action, never prose."""

        if decision.communicative_function in {"protect_boundary", "challenge"} and risk > 0.6:
            top = self.pressures.top()
            if top:
                top.magnitude = max(0.0, top.magnitude - 0.08)
            self.relationship.tension = min(1.0, self.relationship.tension + 0.02)
        if decision.communicative_function == "ask_question" and self.relationship.tension < 0.5:
            curiosity = self.pressures.ensure("curiosity")
            curiosity.magnitude = min(1.0, curiosity.magnitude + 0.03)
        if decision.action_kind in {"silence", "withdraw"}:
            self.relationship.unresolved_conflict = min(1.0, self.relationship.unresolved_conflict + 0.01)

    def _post_speech_update(self, user_text, response, risk, appraisal, now, identity_violation: bool, suppression_traces: list[SuppressionTrace] | None = None):
        # Memory firewall: generated wording is logged as speech evidence, not
        # promoted as objective truth. Canonical memory records the user input
        # and appraisal. The response is event-log data only.
        if suppression_traces is not None:
            suppression_traces.append(_suppression_trace(
                "memory_firewall",
                "logged_only",
                "renderer speech logged as noncanonical evidence" if response else "nonverbal performance logged without invented speech",
            ))
        memory_tags = {"identity", "canonical_user_statement"} if identity_violation else {"canonical_user_statement"}
        if appraisal.contradiction > 0.4:
            memory_tags.add("contradictory_evidence")
        mem = MemoryUnit(
            content=f"I heard you say: {user_text[:120]}",
            created_at=now,
            emotional_valence=-0.3 if risk > 0.6 else 0.2,
            emotional_intensity=max(risk, appraisal.accusation, appraisal.threat, appraisal.boundary_violation),
            relationship_relevance=0.6,
            identity_relevance=0.7 if identity_violation else 0.2,
            unresolved=appraisal.accusation > 0.5 or appraisal.boundary_violation > 0.5 or identity_violation,
            source=KnowledgeSource.USER_TOLD,
            tags=memory_tags,
        )
        self.memory.add(mem)
        event_type = "speech" if response else "nonverbal_performance"
        self.persistence.log_event(self.identity.name, self.user_id, self.timestep, event_type, {
            "response": response,
            "response_is_canonical_truth": False,
            "record_authority": (
                "noncanonical_renderer_output" if response
                else "deterministic_performance_record"
            ),
            "suppression_trace": [trace.to_dict() for trace in (suppression_traces or [])],
            "memory_types": [event_type],
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
