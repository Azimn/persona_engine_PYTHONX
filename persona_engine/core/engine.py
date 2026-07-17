"""Interior engine.

Pipeline:
Input -> wall-clock catch-up -> identity guard -> appraisal -> relationship and
pressure update -> interpretation -> memory retrieval -> intention/open-loop/habit selection ->
workspace frame -> renderer -> validator -> canonical writeback -> event-log persistence.
"""

import json
import hashlib
import time
import threading
from dataclasses import asdict, dataclass, replace
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
from .memory import KnowledgeSource, MemoryRetrieval, MemoryStore, MemoryUnit
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
from .lived_experience import (
    AutobiographicalActivation, AutobiographicalInterpretation,
    AutobiographicalInterpretationStore, DeferredReinterpretation,
    ExperienceStore, InterpretationUseOutcome, ReinterpretationCandidate,
    SubjectiveExperience, WorldEvent, WorldEventLedger,
    interpretation_use_modifier,
)
from .autobiographical_reconsolidation import (
    AutobiographicalReconsolidator, ReconsolidationContext,
)
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
from .autobiographical_evidence import (
    AutobiographicalEvidenceLink, AutobiographicalEvidenceRouter, InterpretationStatusStore,
)
from .memory_connectivity import MemoryConnectionStore
from .skills import SkillStore
from .dyadic_ritual import DyadicRitualStore
from .developmental_learning import (
    DevelopmentEpisodeStore, RelationshipExpectationStore, build_episode,
)
from .genesis import GenesisReplayer
from .journal import PersonalJournal
from .actors import ActorRegistry, ActorRelationshipStore
from .offline_conversation import (
    ConversationCandidate, derive_conversation_candidate, renderer_is_model_backed,
    parse_behavioral_tendencies, classify_input, topic_key,
)
from .conversation_continuity import ConversationContinuityStore
from .conversation_initiative import (
    InitiativeAssessment, assess_conversation_initiative,
    validate_initiative_realization,
)
from .conversation_choreography import (
    ConversationChoreographyPlan, ConversationChoreographyPlanner,
)
from .offline_topic_dialogue import (
    OfflineTopicLibrary, OfflineTopicMatch, OfflineTopicPlan,
    OfflineTopicThreadStore, record_topic_turn,
)


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


def _stable_record_id(prefix: str, *parts: object) -> str:
    payload = json.dumps([str(item) for item in parts], separators=(",", ":")).encode("utf-8")
    return f"{prefix}_{hashlib.blake2b(payload, digest_size=8).hexdigest()}"


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
        self.actor_registry = ActorRegistry()
        self.self_actor = self.actor_registry.resolve(
            stable_key=f"character:{identity.name.casefold()}", display_name=identity.name,
            tick=0, actor_kind="character", source="cartridge", recognition_confidence=1.0,
        )
        self.default_actor = self.actor_registry.resolve(
            stable_key=f"session:{user_id}", display_name=user_id,
            tick=0, actor_kind="human", source="session", recognition_confidence=1.0,
        )
        self.actor_relationships = ActorRelationshipStore()
        self.conversation_continuity = ConversationContinuityStore()
        self.active_actor_id = self.default_actor.actor_id
        self.relationship = self.actor_relationships.for_actor(self.active_actor_id)
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
        self.autobiographical_interpretations = AutobiographicalInterpretationStore()
        self.autobiographical_reconsolidator = AutobiographicalReconsolidator()
        self.deferred_reinterpretations: list[DeferredReinterpretation] = []
        self.interpretation_use_outcomes: list[InterpretationUseOutcome] = []
        self._last_reinterpretation_candidate: ReinterpretationCandidate | None = None
        self._last_autobiographical_interpretation: AutobiographicalInterpretation | None = None
        self._last_autobiographical_activations: tuple[AutobiographicalActivation, ...] = ()
        self.autobiographical_evidence_router = AutobiographicalEvidenceRouter()
        self.autobiographical_evidence_links: list[AutobiographicalEvidenceLink] = []
        self.interpretation_status_events = InterpretationStatusStore()
        self.memory_connections = MemoryConnectionStore()
        self.skills = SkillStore()
        self.relationship_expectations = RelationshipExpectationStore()
        self.dyadic_rituals = DyadicRitualStore()
        self.development_episodes = DevelopmentEpisodeStore()
        self.development_signals: list[dict[str, Any]] = []
        self.genesis_replays: list[dict[str, Any]] = []
        self.genesis_replayer = GenesisReplayer()
        self.journal = PersonalJournal(
            object_name=str(profile_source.get("journal", {}).get("object_name", "personal notebook")),
        )
        if self.journal.object_name not in self.world.objects:
            self.world.objects.append(self.journal.object_name)
        self._pending_skill_id: str | None = None
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
        self.conversation_choreography_planner = ConversationChoreographyPlanner()
        self._last_conversation_choreography: ConversationChoreographyPlan | None = None
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
        self._last_conversation_candidate: ConversationCandidate | None = None
        self._last_initiative_assessment: InitiativeAssessment | None = None
        self.behavioral_tendencies = parse_behavioral_tendencies(
            profile_source.get("behavioral_richness")
        )
        self.offline_topics = OfflineTopicLibrary.from_cartridge(
            profile_source.get("offline_topics")
        )
        self.offline_topic_threads = OfflineTopicThreadStore()
        self._last_offline_topic_match: OfflineTopicMatch | None = None
        self._last_offline_topic_plan: OfflineTopicPlan | None = None
        self._behavior_tendency_history: list[tuple[str, int]] = []
        self._life_callback_history: list[str] = []
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

        previous_state = getattr(getattr(self.renderer, "_offline", None), "to_state", lambda: {})()
        self.renderer = renderer
        offline = getattr(self.renderer, "_offline", None)
        if offline is not None and previous_state:
            offline.load_state(previous_state)
        if renderer_is_model_backed(renderer):
            self.intentions.mark_capability_ready("language_model")
        self._persist()

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

    def _activate_interlocutor(self, visible_context: dict[str, Any]) -> None:
        supplied_id = visible_context.get("speaker_id")
        if supplied_id is None:
            record = self.default_actor
        else:
            speaker_id = str(supplied_id)
            display_name = str(visible_context.get("speaker_name", speaker_id))
            actor_kind = (
                "character" if visible_context.get("interaction_type") == "character_to_character"
                else str(visible_context.get("speaker_kind", "human"))
            )
            if actor_kind not in {"human", "npc", "character", "historical", "unknown"}:
                actor_kind = "unknown"
            record = self.actor_registry.resolve(
                stable_key=f"external:{speaker_id}", display_name=display_name,
                tick=self.timestep, actor_kind=actor_kind, source="interaction",
                aliases=tuple(visible_context.get("speaker_aliases", ()))
                if isinstance(visible_context.get("speaker_aliases", ()), (list, tuple)) else (),
                recognition_confidence=float(visible_context.get("speaker_confidence", 1.0)),
            )
        self.active_actor_id = record.actor_id
        self.relationship = self.actor_relationships.for_actor(record.actor_id)

    def _actorize_event_payload(self, actors, source: str, payload: dict[str, Any]) -> dict[str, Any]:
        actor_ids = []
        for value in actors:
            text = str(value)
            if text.startswith("actor:"):
                try:
                    actor_ids.append(int(text.split(":", 1)[1], 16))
                    continue
                except ValueError:
                    pass
            if text == self.identity.name:
                record = self.self_actor
            elif source == "cartridge_genesis":
                record = self.actor_registry.resolve(
                    stable_key=f"genesis:{text.casefold()}", display_name=text,
                    tick=self.timestep, actor_kind="historical", source="cartridge_genesis",
                    recognition_confidence=0.9,
                )
            else:
                record = self.actor_registry.resolve(
                    stable_key=f"world:{text.casefold()}", display_name=text,
                    tick=self.timestep, actor_kind="unknown", source=source,
                    recognition_confidence=0.6,
                )
            actor_ids.append(record.actor_id)
        return {**payload, "actor_ids": list(dict.fromkeys(actor_ids))}

    # ---------------- persistence ----------------
    def _load_state(self):
        cid, uid = self.identity.name, self.user_id
        meta = self.persistence.load(cid, uid, "meta", {})
        self.energy = meta.get("energy", self.energy)
        self.restlessness = meta.get("restlessness", self.restlessness)
        self.timestep = meta.get("timestep", self.timestep)
        self.last_wall_time = meta.get("last_wall_time", self.last_wall_time)
        self.last_reflection_time = meta.get("last_reflection_time", self.last_reflection_time)

        actor_state = self.persistence.load(cid, uid, "actor_registry", [])
        if actor_state:
            self.actor_registry = ActorRegistry.from_list(actor_state)
        self.self_actor = self.actor_registry.resolve(
            stable_key=f"character:{self.identity.name.casefold()}", display_name=self.identity.name,
            tick=self.timestep, actor_kind="character", source="cartridge", recognition_confidence=1.0,
            observe=False,
        )
        self.default_actor = self.actor_registry.resolve(
            stable_key=f"session:{self.user_id}", display_name=self.user_id,
            tick=self.timestep, actor_kind="human", source="session", recognition_confidence=1.0,
            observe=False,
        )
        relationship_state = self.persistence.load(cid, uid, "actor_relationships", [])
        self.actor_relationships = ActorRelationshipStore.from_list(relationship_state)
        self.conversation_continuity = ConversationContinuityStore.from_list(
            self.persistence.load(cid, uid, "conversation_continuity", [])
        )
        self.offline_topic_threads = OfflineTopicThreadStore.from_list(
            self.persistence.load(cid, uid, "offline_topic_threads", [])
        )
        self.active_actor_id = int(meta.get("active_actor_id", self.default_actor.actor_id))
        if self.actor_registry.fetch(self.active_actor_id) is None:
            self.active_actor_id = self.default_actor.actor_id
        self.relationship = self.actor_relationships.for_actor(self.active_actor_id)
        rel = self.persistence.load(cid, uid, "relationship")
        if rel and not relationship_state:
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
        self.autobiographical_interpretations = AutobiographicalInterpretationStore.from_list(
            self.persistence.load(cid, uid, "autobiographical_interpretations", [])
        )
        self.deferred_reinterpretations = [
            DeferredReinterpretation.from_dict(item) for item in
            self.persistence.load(cid, uid, "deferred_reinterpretations", [])
        ][-64:]
        self.interpretation_use_outcomes = [
            InterpretationUseOutcome.from_dict(item) for item in
            self.persistence.load(cid, uid, "interpretation_use_outcomes", [])
        ][-512:]
        last_candidate = self.persistence.load(cid, uid, "last_reinterpretation_candidate")
        self._last_reinterpretation_candidate = ReinterpretationCandidate.from_dict(last_candidate) if last_candidate else None
        last_interpretation = self.persistence.load(cid, uid, "last_autobiographical_interpretation")
        self._last_autobiographical_interpretation = (
            AutobiographicalInterpretation.from_dict(last_interpretation) if last_interpretation else None
        )
        self.autobiographical_evidence_links = [
            AutobiographicalEvidenceLink.from_dict(item) for item in
            self.persistence.load(cid, uid, "autobiographical_evidence_links", [])
        ][-1024:]
        self.interpretation_status_events = InterpretationStatusStore.from_list(
            self.persistence.load(cid, uid, "interpretation_status_events", [])
        )
        self.memory_connections = MemoryConnectionStore.from_list(
            self.persistence.load(cid, uid, "memory_connections", [])
        )
        self.skills = SkillStore.from_list(self.persistence.load(cid, uid, "skills", []))
        self.relationship_expectations = RelationshipExpectationStore.from_list(
            self.persistence.load(cid, uid, "relationship_expectations", [])
        )
        self.dyadic_rituals = DyadicRitualStore.from_list(
            self.persistence.load(cid, uid, "dyadic_rituals", [])
        )
        self.development_episodes = DevelopmentEpisodeStore.from_list(
            self.persistence.load(cid, uid, "development_episodes", [])
        )
        self.development_signals = list(self.persistence.load(cid, uid, "development_signals", []))[-256:]
        self.genesis_replays = list(self.persistence.load(cid, uid, "genesis_replays", []))[-8:]
        self.journal = PersonalJournal.from_dict(
            self.persistence.load(cid, uid, "journal", {}),
            object_name=str((self.cartridge_data or {}).get("journal", {}).get("object_name", "personal notebook")),
        )
        if self.journal.object_name not in self.world.objects:
            self.world.objects.append(self.journal.object_name)
        self._pending_skill_id = self.persistence.load(cid, uid, "pending_skill_id")
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
        last_choreography = self.persistence.load(cid, uid, "last_conversation_choreography")
        self._last_conversation_choreography = (
            ConversationChoreographyPlan.from_dict(last_choreography)
            if last_choreography else None
        )
        self._last_model_call_metrics = self.persistence.load(
            cid, uid, "last_model_call_metrics", self._last_model_call_metrics,
        )
        last_monitor = self.persistence.load(cid, uid, "last_self_monitor")
        self._last_self_monitor = SelfMonitorResult.from_dict(last_monitor) if last_monitor else None
        last_conversation = self.persistence.load(cid, uid, "last_conversation_candidate")
        self._last_conversation_candidate = (
            ConversationCandidate.from_dict(last_conversation) if last_conversation else None
        )
        self._behavior_tendency_history = [
            (str(item[0]), int(item[1])) for item in
            self.persistence.load(cid, uid, "behavior_tendency_history", [])[-24:]
            if isinstance(item, (list, tuple)) and len(item) == 2
        ]
        self._life_callback_history = [
            str(item)[:160] for item in
            self.persistence.load(cid, uid, "life_callback_history", [])[-16:]
        ]
        offline_state = self.persistence.load(cid, uid, "offline_realization_state", {})
        offline = getattr(self.renderer, "_offline", None)
        if offline is not None and offline_state:
            offline.load_state(offline_state)
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
                "active_actor_id": self.active_actor_id,
            },
            "relationship": vars(self.relationship),
            "actor_registry": self.actor_registry.to_list(),
            "actor_relationships": self.actor_relationships.to_list(),
            "conversation_continuity": self.conversation_continuity.to_list(),
            "offline_topic_threads": self.offline_topic_threads.to_list(),
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
            "autobiographical_interpretations": self.autobiographical_interpretations.to_list(),
            "deferred_reinterpretations": [item.to_dict() for item in self.deferred_reinterpretations],
            "interpretation_use_outcomes": [item.to_dict() for item in self.interpretation_use_outcomes],
            "last_reinterpretation_candidate": self._last_reinterpretation_candidate.to_dict()
            if self._last_reinterpretation_candidate else None,
            "last_autobiographical_interpretation": self._last_autobiographical_interpretation.to_dict()
            if self._last_autobiographical_interpretation else None,
            "autobiographical_evidence_links": [item.to_dict() for item in self.autobiographical_evidence_links],
            "interpretation_status_events": self.interpretation_status_events.to_list(),
            "memory_connections": self.memory_connections.to_list(),
            "skills": self.skills.to_list(),
            "relationship_expectations": self.relationship_expectations.to_list(),
            "dyadic_rituals": self.dyadic_rituals.to_list(),
            "development_episodes": self.development_episodes.to_list(),
            "development_signals": list(self.development_signals),
            "genesis_replays": list(self.genesis_replays),
            "journal": self.journal.to_dict(),
            "pending_skill_id": self._pending_skill_id,
            "capability_artifacts": self.capability_artifacts.to_list(),
            "life_state": self.life_state.to_dict(),
            "intrinsic_state": self.intrinsic_state.to_dict(),
            "last_intrinsic_proposal": self._last_intrinsic_proposal.to_dict() if self._last_intrinsic_proposal else None,
            "last_action_decision": self._last_action_decision.to_dict() if self._last_action_decision else None,
            "last_performance_plan": self._last_performance_plan.to_dict() if self._last_performance_plan else None,
            "last_conversation_choreography": (
                self._last_conversation_choreography.to_dict()
                if self._last_conversation_choreography else None
            ),
            "last_model_call_metrics": dict(self._last_model_call_metrics),
            "last_self_monitor": self._last_self_monitor.to_dict() if self._last_self_monitor else None,
            "last_conversation_candidate": (
                self._last_conversation_candidate.to_dict()
                if self._last_conversation_candidate else None
            ),
            "behavior_tendency_history": [list(item) for item in self._behavior_tendency_history[-24:]],
            "life_callback_history": self._life_callback_history[-16:],
            "offline_realization_state": getattr(
                getattr(self.renderer, "_offline", None), "to_state", lambda: {}
            )(),
            "imperfect_action": {"counter": self.imperfect_actions.counter},
            "deception_ledger": self.deception_ledger.to_state(),
        }

    def _persist(self):
        self.persistence.save_many(self.identity.name, self.user_id, self._serialize_state())

    def replay_genesis(self, *, end_time: float | None = None) -> dict[str, Any]:
        """Replay cartridge-authored history through ordinary lived-state owners."""

        return self.genesis_replayer.replay(
            self, end_time=time.time() if end_time is None else float(end_time),
        ).to_dict()

    def write_journal_entry(
        self, text: str, *, entry_kind: str = "private_note", source: str = "character_action",
        source_event_ids=(), historical_year: int | None = None,
        timestamp: float | None = None, persist: bool = True,
    ) -> dict[str, Any]:
        """Write deliberate character text; the entry is subjective, not world truth."""

        when = time.time() if timestamp is None else float(timestamp)
        entry = self.journal.write(
            tick=self.timestep, timestamp=when, text=text, entry_kind=entry_kind,
            source=source, source_event_ids=source_event_ids, historical_year=historical_year,
        )
        self.persistence.log_event(
            self.identity.name, self.user_id, self.timestep, "journal_entry_written",
            {**entry.to_dict(), "record_authority": "character_authored_artifact"},
        )
        if persist:
            self._persist()
        return entry.to_dict()

    def read_journal(self, query: str = "", *, limit: int = 4, timestamp: float | None = None) -> dict[str, Any]:
        """Read notebook text as a new bounded observation and possible memory."""

        entries = self.journal.search(query, limit)
        excerpt = " ".join(item.text for item in reversed(entries))[:1200]
        if not excerpt:
            return {"object_name": self.journal.object_name, "entries": [], "experience": None}
        event = self.record_world_event(
            event_type="journal_reading",
            actors=(self.identity.name,), location=str(self.world.zone), action="read",
            targets=(self.journal.object_name,),
            outcome=f"The notebook contains: {excerpt}", source="journal_artifact",
            payload={"journal_entry_ids": [item.entry_id for item in entries]},
            timestamp=time.time() if timestamp is None else float(timestamp),
        )
        experience = self.perceive_world_event(
            event.event_id, attention=0.85, confidence=0.75,
            salience=0.6,
            emotional_residue="reflective", interpretation="my written account may support or challenge recollection",
            distortion={"journal_is_evidence_of_writing_not_objective_truth": True},
        )
        return {
            "object_name": self.journal.object_name,
            "entries": [item.to_dict() for item in entries],
            "world_event_id": event.event_id,
            "experience": experience.to_dict() if experience else None,
        }

    def materialize_journal(self, path: str | None = None) -> str:
        target = path or str(self.persistence.path) + ".journal.txt"
        return str(self.journal.materialize(target))

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

    def advance_simulated_time(self, elapsed_seconds: float, now: float | None = None) -> dict[str, Any]:
        """Advance organism time through bounded summary steps for hosts and replay."""

        elapsed = max(0.0, float(elapsed_seconds))
        steps = min(12, max(1, int(elapsed / 21600.0))) if elapsed > 0.0 else 0
        target_time = float(now) if now is not None else time.time()
        for index in range(steps):
            # Catch-up is intentionally summarized. Feeding a full day into a
            # single body tick would model 24 hours of uninterrupted exertion.
            cycle_time = target_time - float(steps - index - 1) * 5.0
            self._run_single_idle_cycle(
                elapsed_seconds=5.0, include_vitality=False, now=cycle_time,
            )
        life_events = self.vitality.catch_up(
            self.life_state,
            self.timestep,
            elapsed,
            max_steps=12,
            whim_weights=self._whim_weights(),
        )
        self.experiences.decay(target_time)
        self.timestep += steps
        self.last_catch_up_summary = {
            "elapsed_seconds": round(elapsed, 3),
            "tide_steps": steps,
            "life_steps": self.life_state.last_catch_up_steps,
            "life_events": [event.to_dict() for event in life_events],
            "clock_source": "simulated",
        }
        self._persist()
        return dict(self.last_catch_up_summary)

    def run_idle_cycle(self):
        self._run_single_idle_cycle(elapsed_seconds=5.0)
        self.timestep += 1
        self.last_wall_time = time.time()
        self._persist()

    def _run_single_idle_cycle(
        self, elapsed_seconds: float = 5.0, include_vitality: bool = True,
        now: float | None = None,
    ):
        now = float(now) if now is not None else time.time()
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
        proposal = self._advance_intrinsic_motivation(now=now)
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

    def _advance_intrinsic_motivation(
        self, force: bool = False, now: float | None = None,
    ) -> IntrinsicProposal | None:
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
            created_at=float(now) if now is not None else time.time(),
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
        payload = self._actorize_event_payload(actors, source, dict(payload or {}))
        event = self.world_events.create(
            tick=self.timestep, timestamp=time.time() if timestamp is None else timestamp, event_type=event_type,
            actors=actors, location=location, action=action, targets=targets, outcome=outcome,
            source=source, payload=payload,
        )
        evidence_links = self.autobiographical_evidence_router.route(
            event=event, interpretations=self.autobiographical_interpretations,
            experiences=self.experiences, tick=self.timestep,
        )
        for link in evidence_links:
            if not any(item.link_id == link.link_id for item in self.autobiographical_evidence_links):
                self.autobiographical_evidence_links = [*self.autobiographical_evidence_links, link][-1024:]
                if link.relation in {"contradicts", "corrects_cause"}:
                    self.interpretation_status_events.add(
                        link.interpretation_id, "challenged", link.link_id, self.timestep,
                    )
                self.persistence.log_event(
                    self.identity.name, self.user_id, self.timestep,
                    "autobiographical_evidence_link", link.to_dict(),
                )
        self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "objective_world_event", event.to_dict())
        return event

    def _register_autobiographical_experience(
        self, experience: SubjectiveExperience | None,
    ) -> AutobiographicalInterpretation | None:
        if experience is None:
            return None
        meaning_kind = (
            "mistaken_attribution"
            if experience.distortion.get("attributed_intent") or experience.distortion.get("missing_cause")
            else "ordinary"
        )
        interpretation = self.autobiographical_interpretations.create_initial(
            experience=experience, tick=self.timestep, meaning_kind=meaning_kind,
        )
        self._last_autobiographical_interpretation = interpretation
        return interpretation

    def reconsider_experience(
        self, experience_id: str, context: ReconsolidationContext,
    ) -> AutobiographicalInterpretation | None:
        """Validate and append later meaning without rewriting original records."""

        experience = next(
            (item for item in self.experiences.experiences if item.experience_id == experience_id), None,
        )
        if experience is None:
            raise KeyError(experience_id)
        current = self.autobiographical_interpretations.current(experience_id)
        if current is None:
            current = self._register_autobiographical_experience(experience)
        linked_corrections = tuple(
            event_id for event_id in context.contradicting_world_event_ids
            if (event := self.world_events.fetch(event_id)) is not None
            and (
                event.payload.get("corrects_world_event_id") == experience.world_event_id
                or event.payload.get("contradicts_interpretation_id") == current.interpretation_id
            )
        )
        if context.trigger_type == "contradictory_evidence" and not linked_corrections:
            context = replace(context, contradicting_world_event_ids=())
        candidate = self.autobiographical_reconsolidator.propose(
            experience=experience, current=current, context=context,
        )
        if candidate is None:
            reason = self.autobiographical_reconsolidator.deferral_reason(context, current)
            evidence_ids = tuple(dict.fromkeys((
                *context.supporting_memory_ids, *context.contradicting_memory_ids,
                *context.supporting_world_event_ids, *context.contradicting_world_event_ids,
            )))
            deferred = DeferredReinterpretation(
                1, _stable_record_id("deferred_reinterpretation", experience_id, current.interpretation_id,
                                     context.tick, context.trigger_type, evidence_ids),
                experience_id, current.interpretation_id, context.trigger_type, evidence_ids,
                max(0.0, min(1.0, context.conflict_strength)), reason, int(context.tick),
                int(context.tick) + self.autobiographical_reconsolidator.MIN_REINTERPRETATION_INTERVAL,
            )
            if not any(item.deferred_id == deferred.deferred_id for item in self.deferred_reinterpretations):
                self.deferred_reinterpretations = [*self.deferred_reinterpretations, deferred][-64:]
            self.persistence.log_event(
                self.identity.name, self.user_id, self.timestep,
                "autobiographical_reinterpretation_deferred", deferred.to_dict(),
            )
            self._persist()
            return None
        self._last_reinterpretation_candidate = candidate
        try:
            revised = self.autobiographical_interpretations.append_revision(
                experience=experience, prior=current, candidate=candidate, tick=context.tick,
            )
        except ValueError as exc:
            if "maximum" not in str(exc):
                raise
            deferred = DeferredReinterpretation(
                1, _stable_record_id("deferred_reinterpretation", candidate.candidate_id, "version_bound"),
                experience_id, current.interpretation_id, context.trigger_type,
                candidate.provenance_ids, candidate.conflict_strength, "version_bound",
                int(context.tick), int(context.tick) + 1,
            )
            self.deferred_reinterpretations = [*self.deferred_reinterpretations, deferred][-64:]
            self._persist()
            return None
        self._last_autobiographical_interpretation = revised
        self.interpretation_status_events.add(
            current.interpretation_id, "superseded", revised.interpretation_id, context.tick,
        )
        self.interpretation_status_events.add(
            revised.interpretation_id, "current", candidate.candidate_id, context.tick,
        )
        self.deferred_reinterpretations = [
            item for item in self.deferred_reinterpretations if item.experience_id != experience_id
        ]
        self.persistence.log_event(
            self.identity.name, self.user_id, self.timestep,
            "autobiographical_reinterpretation", revised.to_dict(),
        )
        self._persist()
        return revised

    def reconsider_with_current_self_monitor(
        self, experience_id: str, correction_event_id: str, *,
        proposed_meaning_kind: str, proposed_meaning: str,
    ) -> AutobiographicalInterpretation | None:
        """Build a correction context from the organism's own perceived diagnostics."""

        if self._last_self_monitor is None:
            raise RuntimeError("self-monitor result required before reconsideration")
        top = self.pressures.top()
        context = ReconsolidationContext(
            tick=self.timestep,
            trigger_type="contradictory_evidence",
            integration_capacity=self.integration_capacity(),
            perceived_capacity=self._last_self_monitor.perceived_capacity,
            conflict_noticed=bool(self._last_self_monitor.noticed_conflict_ids),
            conflict_strength=max(
                (item.strength for item in self._last_synthesis.inhibited_influences if item.contradictory),
                default=0.0,
            ) if self._last_synthesis else 0.0,
            dominant_pressure=top.magnitude if top else 0.0,
            contradicting_world_event_ids=(correction_event_id,),
            proposed_meaning_kind=proposed_meaning_kind,
            proposed_meaning_code=proposed_meaning,
        )
        return self.reconsider_experience(experience_id, context)

    def _reconsider_recent_evidence(
        self, self_monitor: SelfMonitorResult, actual_capacity: float,
    ) -> AutobiographicalInterpretation | None:
        """Try one explicit evidence link; never infer links from prose."""

        for link in reversed(self.autobiographical_evidence_links[-8:]):
            if link.relation not in {"contradicts", "corrects_cause", "clarifies"}:
                continue
            current = self.autobiographical_interpretations.current(link.experience_id)
            if current is None or link.evidence_event_id in current.contradicting_world_event_ids:
                continue
            evidence_influence_id = f"autobiographical_evidence:{link.link_id}"
            noticed = evidence_influence_id in self_monitor.noticed_conflict_ids
            profile = (self.cartridge_data or {}).get("autobiographical_reconsolidation", {})
            templates = dict(profile.get("meaning_templates", {}))
            meaning = templates.get(
                "corrected_accident",
                "I now understand that incomplete information may have caused the earlier failure.",
            )
            context = ReconsolidationContext(
                tick=self.timestep, trigger_type="contradictory_evidence",
                integration_capacity=actual_capacity,
                perceived_capacity=self_monitor.perceived_capacity,
                conflict_noticed=noticed, conflict_strength=link.strength,
                dominant_pressure=self.pressures.top().magnitude if self.pressures.top() else 0.0,
                contradicting_world_event_ids=(link.evidence_event_id,),
                proposed_meaning_kind="reconciled_meaning",
                proposed_meaning_code=str(meaning),
            )
            return self.reconsider_experience(link.experience_id, context)
        return None

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
            self._register_autobiographical_experience(experience)
            self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "subjective_experience", experience.to_dict())
        return event, experience

    def perceive_world_event(self, event_id: str, *, attention: float = 0.8, confidence: float = 0.8,
                             salience: float = 0.5, emotional_residue: str = "neutral",
                             interpretation: str = "ordinary", source_tier: int = 0,
                             distortion: dict[str, Any] | None = None, consolidate: bool = True,
                             perceived_summary: str | None = None):
        event = self.world_events.fetch(event_id)
        if event is None:
            raise KeyError(event_id)
        experience = self.experiences.perceive(
            event, self.identity.name, attention=attention, confidence=confidence, salience=salience,
            emotional_residue=emotional_residue, interpretation=interpretation,
            source_tier=source_tier, distortion=distortion, perceived_summary=perceived_summary,
        )
        if experience and consolidate:
            self.experiences.consolidate(experience, self.memory, event.timestamp)
        if experience:
            self._register_autobiographical_experience(experience)
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
            self._register_autobiographical_experience(experience)
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

    def complete_offline_inquiry(
        self, *, topic_key: str, first_person_note: str, character_position: str,
        confidence: float = 0.72, timestamp: float | None = None,
    ) -> dict[str, Any]:
        """Attach an approved online result to one character-owned offline inquiry."""

        key = str(topic_key).strip()
        note = str(first_person_note).strip()
        position = str(character_position).strip()
        if not key or not note or not position:
            raise ValueError("topic_key, first_person_note, and character_position are required")
        if len(note) > 2000 or len(position) > 1200:
            raise ValueError("completed offline inquiry text exceeds its bound")
        loop = next((
            item for item in self.intentions.open_loops
            if (item.topic_key or item.topic) == key
            and item.required_capability in {"language_model", "external_knowledge"}
            and item.status in {"pending", "ready", "surfaced"}
        ), None)
        if loop is None:
            raise ValueError(f"no unresolved offline inquiry matches topic key: {key}")
        when = time.time() if timestamp is None else float(timestamp)
        artifact = self.capability_artifacts.add(
            kind="research",
            content=position,
            source_tier=1,
            provenance={
                "source": "approved_online_inquiry",
                "topic_key": key,
                "original_question": loop.topic,
                "actor_id": loop.actor_id,
            },
            confidence=max(0.0, min(1.0, float(confidence))),
            verification_state="supported",
            canonicality="subjective",
            created_at=when,
        )
        journal_result = self.propose_world_action(
            "write_journal",
            {"text": note, "entry_kind": "research_note"},
            event_time=when,
        )
        loop.resolution_artifact_id = artifact.artifact_id
        loop.character_position = position
        loop.required_capability = "none"
        loop.status = "ready"
        loop.last_touched = when
        self.persistence.log_event(
            self.identity.name, self.user_id, self.timestep,
            "offline_inquiry_completed",
            {
                "topic_key": key,
                "open_loop_topic": loop.topic,
                "artifact_id": artifact.artifact_id,
                "journal_entry_id": (
                    (journal_result.get("journal_entry") or {}).get("entry_id")
                ),
                "record_authority": "character_authored_artifact",
                "memory_types": ["capability_artifact", "journal", "open_loop"],
            },
        )
        self._persist()
        return {
            "topic_key": key,
            "status": loop.status,
            "artifact": artifact.to_dict(),
            "journal_entry": journal_result.get("journal_entry"),
        }

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
            # Counterevidence must remain cognitively available when an immediate
            # conversational obligation also occupies the bounded synthesis field.
            contradiction_boost = 0.12 if contradiction else 0.0
            influences.append(SynthesisInfluence(
                f"memory:{memory.id}", "memory", memory.content[:120],
                min(
                    1.0,
                    0.30
                    + memory.salience * 0.35
                    + memory.emotional_intensity * 0.25
                    + contradiction_boost,
                ),
                emotional_congruence=memory.emotional_intensity,
                contradictory=contradiction,
                reality_support=reality,
            ))
        for link in self.autobiographical_evidence_links[-4:]:
            influences.append(SynthesisInfluence(
                f"autobiographical_evidence:{link.link_id}", "evidence",
                f"{link.relation}:{link.interpretation_id}", link.strength,
                contradictory=link.relation in {"contradicts", "corrects_cause"},
                reality_support=1.0 if link.evidence_tier == "objective" else .6,
            ))
        context_tags = {"interaction", "interruption" if self.life_state.activity_status == "interrupted" else "ongoing"}
        for skill in sorted(self.skills.skills.values(), key=lambda item: (-item.competence, item.skill_id))[:3]:
            forecast = self.skills.forecast(skill, context_tags, fatigue=self.body.fatigue)
            influences.append(SynthesisInfluence(
                f"skill:{skill.skill_id}", "skill", skill.name,
                min(.75, .25 + forecast.effective_competence * .5),
                immediate=skill.automaticity >= .7,
            ))
        for expectation in sorted(self.relationship_expectations.items.values(), key=lambda item: (-item.confidence, item.key))[:2]:
            if expectation.value in {"usually", "strongly_expected"}:
                influences.append(SynthesisInfluence(
                    f"relationship_expectation:{expectation.key}", "relationship_expectation",
                    f"{expectation.key}:{expectation.value}", min(.65, expectation.confidence),
                ))
        for ritual in sorted(self.dyadic_rituals.rituals, key=lambda item: (-item.strength, item.ritual_id))[:2]:
            if ritual.state == "supported":
                influences.append(SynthesisInfluence(
                    f"dyadic_ritual:{ritual.ritual_id}", "dyadic_ritual",
                    ritual.trigger_pattern, min(.7, ritual.strength),
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

    def _development_summary(self) -> dict[str, Any]:
        return {
            "autobiographical_evidence_link_count": len(self.autobiographical_evidence_links),
            "reinterpretation_count": max(0, len(self.autobiographical_interpretations.interpretations) - len(self.experiences.experiences)),
            "deferred_reinterpretation_count": len(self.deferred_reinterpretations),
            "memory_connection_count": len(self.memory_connections.connections),
            "skills": self.skills.to_list(),
            "relationship_expectations": self.relationship_expectations.to_list(),
            "dyadic_rituals": self.dyadic_rituals.to_list(),
            "development_episode_count": len(self.development_episodes.episodes),
            "development_signal_count": len(self.development_signals),
            "earned_traits": [asdict(item) for item in self.ledger.earned_traits.values()],
        }

    def _record_development_signal(
        self, signal: str, day: int, context: str, confidence: float, now: float,
    ) -> None:
        signal_id = _stable_record_id("development_signal", signal, day, context, self.timestep)
        if not any(item.get("signal_id") == signal_id for item in self.development_signals):
            self.development_signals = [*self.development_signals, {
                "signal_id": signal_id, "signal": signal, "day": int(day),
                "context": str(context), "confidence": max(0.0, min(1.0, float(confidence))),
                "committed": False,
            }][-256:]
        config = dict((self.cartridge_data or {}).get("development", {}))
        for rule in config.get("growth_rules", []):
            if str(rule.get("signal")) != signal:
                continue
            eligible = [item for item in self.development_signals if item["signal"] == signal and not item.get("committed")]
            if len(eligible) < int(config.get("minimum_identity_evidence", 5)):
                continue
            if len({item["day"] for item in eligible}) < int(config.get("minimum_distinct_days", 3)):
                continue
            if len({item["context"] for item in eligible}) < int(config.get("minimum_distinct_contexts", 2)):
                continue
            if sum(item["confidence"] for item in eligible) / len(eligible) < float(config.get("minimum_identity_confidence", .75)):
                continue
            self.ledger.propose_trait_update(
                str(rule["trait"]),
                float(config.get("identity_commit_delta", .015)) * float(rule.get("direction", 1.0)),
                [item["signal_id"] for item in eligible], now=now,
            )
            for item in eligible:
                item["committed"] = True


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
        if resolution.accepted and action_type == "read_journal":
            self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "world_action_resolution", {
                "action_type": action_type, "payload": payload or {}, "accepted": True,
                "reason": resolution.reason, "facts": [f.to_dict() for f in resolution.facts_created],
                "event_time": proposal.created_at, "memory_types": ["world_fact", "action_resolution", "journal"],
            })
            result = self.read_journal(
                str(proposal.payload.get("query", "")),
                limit=int(proposal.payload.get("limit", 4)), timestamp=proposal.created_at,
            )
            return {"accepted": True, "reason": resolution.reason, "facts": [f.to_dict() for f in resolution.facts_created], "journal": result}
        if resolution.accepted and action_type == "write_journal":
            self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "world_action_resolution", {
                "action_type": action_type, "payload": payload or {}, "accepted": True,
                "reason": resolution.reason, "facts": [f.to_dict() for f in resolution.facts_created],
                "event_time": proposal.created_at, "memory_types": ["world_fact", "action_resolution", "journal"],
            })
            event = self.record_world_event(
                event_type="journal_writing", actors=(self.identity.name,), location=str(self.world.zone),
                action="wrote", targets=(self.journal.object_name,),
                outcome="A new entry was written in the personal notebook.",
                source="world_authority", payload={"journal_action": "write"},
                timestamp=proposal.created_at,
            )
            entry = self.write_journal_entry(
                str(proposal.payload["text"]),
                entry_kind=str(proposal.payload.get("entry_kind", "private_note")),
                source="character_world_action", source_event_ids=(event.event_id,),
                timestamp=proposal.created_at, persist=False,
            )
            experience = self.perceive_world_event(
                event.event_id, attention=0.9, confidence=0.95, salience=0.55,
                emotional_residue="deliberate", interpretation="I chose to preserve these words in my notebook.",
                distortion={"journal_text_is_subjective_not_objective_truth": True},
            )
            self._persist()
            return {
                "accepted": True, "reason": resolution.reason,
                "facts": [f.to_dict() for f in resolution.facts_created],
                "journal_entry": entry,
                "subjective_experience_id": experience.experience_id if experience else None,
            }
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
        self._activate_interlocutor(dict(submitted_interaction))
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
            actors=(f"actor:{self.active_actor_id:08x}",),
            location=str(self.world.zone),
            action="interrupted",
            targets=(self.identity.name,),
            outcome="a player message arrived",
            source="user_input",
            payload={"text": user_text[:500], "active_actor_id": self.active_actor_id},
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
        day_index = int(now // 86400)
        if appraisal.repair_attempt > 0.5:
            self._record_development_signal(
                "successful_repair", day_index,
                "after_interruption" if interruption.get("activity_interrupted") else "ordinary_interaction",
                min(1.0, .65 + appraisal.repair_attempt * .25), now,
            )
        if self._pending_skill_id and self.development_episodes.episodes:
            self.skills.update(
                self._pending_skill_id, evidence_tier="supported_subjective",
                succeeded=bool(user_text.strip()), tick=self.timestep,
                episode_id=self.development_episodes.episodes[-1].episode_id,
            )
            self._pending_skill_id = None
        if self.development_episodes.episodes:
            prior_episode = self.development_episodes.episodes[-1].episode_id
            expectation_key = f"actor:{self.active_actor_id:08x}:returns_to_open_loops"
            expectation = self.relationship_expectations.observe(
                expectation_key, prior_episode, day_index, supported=True,
            )
            if expectation and expectation.value in {"usually", "strongly_expected"}:
                self.ledger.set_relationship_belief(f"actor:{self.active_actor_id:08x}", expectation.key, expectation.value)
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
            self._register_autobiographical_experience(experience)
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
        input_act = classify_input(user_text)
        continuity_state = self.conversation_continuity.for_actor(self.active_actor_id)
        offline_topic_match = self.offline_topics.match(user_text)
        if (
            continuity_state.active_topic is not None
            and offline_topic_match.confidence < 0.45
            and any(
                token in {
                    "he", "her", "him", "his", "it", "its", "one", "she",
                    "that", "their", "they", "this",
                }
                for token in user_text.casefold().replace("?", " ").split()
            )
        ):
            offline_topic_match = self.offline_topics.contextual_match(
                continuity_state.active_topic.topic_id,
                offline_topic_match,
            )
        self._last_offline_topic_match = offline_topic_match
        offline_topic_memory_tags = self.offline_topics.memory_tags_for_query(
            offline_topic_match.topic_id, user_text,
        )
        continuity_state.observe_input(
            text=user_text,
            input_act=input_act,
            topic_id=offline_topic_match.topic_id or topic_key(user_text),
            turn=self.timestep,
            emotional_importance=max(
                appraisal.accusation, appraisal.intimacy_bid, appraisal.repair_attempt,
                appraisal.disrespect, appraisal.manipulation,
                top_for_match.magnitude if top_for_match else 0.0,
            ),
        )
        affect_match = (top_for_match.magnitude * 0.1) if top_for_match else 0.0
        active_meaning_ids = tuple(
            item.interpretation_id for item in self.autobiographical_interpretations.interpretations
            if self.autobiographical_interpretations.current(item.experience_id) == item
        )
        association_boosts = self.memory_connections.boosts_for(active_meaning_ids)
        retrievals = self.memory.retrieve_explained(
            user_text, now, top_k=4, emotional_state_match=affect_match,
            relationship_tags={
                "canonical_user_statement", "subjective_experience",
                f"actor:{self.active_actor_id:08x}",
                *{
                    f"actor:{item.actor_id:08x}"
                    for item in self.actor_registry.match_text(user_text)
                },
            },
            association_boosts=association_boosts,
        )
        if input_act == "ask_memory" and offline_topic_memory_tags:
            authored_candidates = sorted(
                (
                    item for item in self.memory.memories
                    if "autobiographical" in item.tags
                    and offline_topic_memory_tags & item.tags
                    and not item.content.casefold().startswith("i heard you say")
                ),
                key=lambda item: (
                    -len(offline_topic_memory_tags & item.tags),
                    -item.salience,
                    -item.created_at,
                    item.id,
                ),
            )
            if authored_candidates:
                preferred = authored_candidates[0]
                retrievals = [
                    MemoryRetrieval(
                        preferred,
                        1.0,
                        {
                            "lexical_match": 0.0,
                            "symbolic_similarity": 0.0,
                            "direct_symbolic_cue": 1.0,
                            "semantic_similarity": 0.0,
                            "recency_boost": 0.0,
                            "salience": preferred.salience,
                            "emotional_relevance": preferred.emotional_intensity,
                            "goal_relevance": 0.0,
                            "relationship_relevance": preferred.relationship_relevance,
                            "direct_link": 0.0,
                            "learned_association": 0.0,
                            "authored_topic_tag": 1.0,
                            "embedding_provider": "topic_tag",
                        },
                    ),
                    *[item for item in retrievals if item.memory.id != preferred.id],
                ][:6]
        retrieved = [item.memory for item in retrievals]
        memory_links = {
            item.experience_id: item.memory_id for item in self.experiences.experiences if item.memory_id
        }
        autobiographical_activations = self.autobiographical_interpretations.activate_for_memories(
            [item.memory.id for item in retrievals],
            relationship_relevance=max(self.relationship.familiarity, self.relationship.tension),
            identity_relevance=max(appraisal.accusation, appraisal.boundary_violation),
            emotional_match=top_for_match.magnitude if top_for_match else 0.0,
            memory_links=memory_links,
            use_modifiers={
                interpretation_id: interpretation_use_modifier([
                    item for item in self.interpretation_use_outcomes
                    if item.interpretation_id == interpretation_id
                ])
                for interpretation_id in {
                    item.interpretation_id for item in self.interpretation_use_outcomes
                }
            },
        )
        self._last_autobiographical_activations = autobiographical_activations
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
        open_loop = self.intentions.due_open_loop(now, actor_id=self.active_actor_id)
        due_open_loop = open_loop
        symbol = self.symbols.most_relevant(now)
        resistance = select_resistance(triggers)
        habit_trigger = triggers[0] if triggers else "default"
        habit = self.habits.most_relevant(habit_trigger)
        available_artifacts = self.capability_artifacts.available(0)[:4]
        base_influences = self._build_synthesis_influences(
            user_text, retrievals, habit, available_artifacts, now, semantic_frame,
            self._last_intrinsic_proposal,
        )
        prior_memory_retrievals = [
            item for item in retrievals
            if item.memory.created_at < now - 0.001
            and "autobiographical" in item.memory.tags
            and not item.memory.content.casefold().startswith("i heard you say")
            and not ({"sensorium", "ambient_event"} & item.memory.tags)
        ]
        topic_memory_retrievals = [
            item for item in prior_memory_retrievals
            if offline_topic_memory_tags & item.memory.tags
        ]
        if topic_memory_retrievals:
            best_tag_overlap = max(
                len(offline_topic_memory_tags & item.memory.tags)
                for item in topic_memory_retrievals
            )
            topic_memory_retrievals = [
                item for item in topic_memory_retrievals
                if len(offline_topic_memory_tags & item.memory.tags) == best_tag_overlap
            ]
        contextual_prior_memory_retrievals = [
            item for item in prior_memory_retrievals
            if continuity_state.memory_context_score(item.memory.content) >= 0.12
            or float(item.reasons.get("direct_symbolic_cue", 0.0)) >= 1.0
        ]
        candidate_memory_retrievals = (
            topic_memory_retrievals or prior_memory_retrievals
            if input_act == "ask_memory" else contextual_prior_memory_retrievals
        )
        raw_direct_memory_cue = any(
            float(item.reasons.get("direct_symbolic_cue", 0.0)) >= 1.0
            for item in candidate_memory_retrievals
        )
        initiative_assessment = assess_conversation_initiative(
            actor_id=self.active_actor_id,
            turn=self.timestep,
            obligation=continuity_state.pending_obligation,
            initiative_budget=continuity_state.initiative_budget,
            contextual_memories=candidate_memory_retrievals,
            open_loop=open_loop,
            intrinsic_proposal=self._last_intrinsic_proposal,
            relationship_expectations=tuple(self.relationship_expectations.items.values()),
            world_changes=tuple([
                *[
                    item.to_dict() for item in self.world_events.recent(8)
                    if item.source not in {"user_input", "renderer_output"}
                    and item.event_type not in {"player_interruption", "shared_speech"}
                ],
                *[item.to_dict() for item in self.life_state.events[-2:]],
            ]),
            recent_source_ids=continuity_state.recent_initiative_source_ids,
        )
        initiative_memory_eligibility = {
            "total_memories_in_store": len(self.memory.memories),
            "retrieved_candidate_count": len(retrievals),
            "pre_topic_autobiographical_count": len(prior_memory_retrievals),
            "relevance_pass_count": len(contextual_prior_memory_retrievals),
            "final_eligible_count": sum(
                item.source_kind == "contextual_memory"
                for item in initiative_assessment.eligible_sources
            ),
            "retrieved_candidate_ids": tuple(item.memory.id for item in retrievals),
            "pre_topic_autobiographical_ids": tuple(
                item.memory.id for item in prior_memory_retrievals
            ),
            "relevance_pass_ids": tuple(
                item.memory.id for item in contextual_prior_memory_retrievals
            ),
        }
        self._last_initiative_assessment = initiative_assessment
        conversation_candidate = derive_conversation_candidate(
            text=user_text,
            actor_id=self.active_actor_id,
            renderer_available=renderer_is_model_backed(self.renderer),
            retrieved=candidate_memory_retrievals,
            direct_memory_cue=raw_direct_memory_cue,
            ready_open_loop=open_loop,
            familiarity=self.relationship.familiarity,
            turn=self.timestep,
            repeated_input_count=sum(
                1 for item in self.memory.memories[-32:]
                if item.created_at < now - 0.001
                and item.content.casefold() == f"I heard you say: {user_text[:120]}".casefold()
            ),
            tendencies=self.behavioral_tendencies,
            tendency_history=self._behavior_tendency_history,
            current_activity=self.life_state.current_activity,
            activity_status=self.life_state.activity_status,
            dominant_pressure=top_for_match.magnitude if top_for_match else 0.0,
            elapsed_since_contact=float(self.last_catch_up_summary.get("elapsed_seconds", 0.0)),
            life_callback_history=self._life_callback_history,
            continuity_state=continuity_state,
            initiative_proposal=(
                initiative_assessment.proposal
                if initiative_assessment.outcome == "proposal_available" else None
            ),
            offline_topic_status=offline_topic_match.status,
            offline_topic_confidence=offline_topic_match.confidence,
        )
        self._last_conversation_candidate = conversation_candidate
        if conversation_candidate.move != "basic_reply":
            base_influences.append(SynthesisInfluence(
                influence_id=f"conversation:{conversation_candidate.candidate_id}",
                kind="conversation_candidate",
                label=conversation_candidate.move,
                strength=conversation_candidate.strength,
                immediate=conversation_candidate.response_value >= 0.80,
                reality_support=0.8 if conversation_candidate.source_memory_id else 0.0,
            ))
        actual_capacity = self.integration_capacity()
        for activation in autobiographical_activations:
            interpretation = self.autobiographical_interpretations.fetch(activation.interpretation_id)
            if interpretation is None:
                continue
            if activation.status == "historical":
                if actual_capacity >= 0.35 or abs(interpretation.emotional_charge) < 0.55:
                    continue
                strength = min(0.25, activation.activation)
                label = f"historical_meaning_intrusion:{interpretation.current_meaning}"
            else:
                strength = activation.activation
                label = interpretation.current_meaning
            base_influences.append(SynthesisInfluence(
                f"autobiographical:{interpretation.interpretation_id}",
                "autobiographical_meaning", label[:160], strength,
                emotional_congruence=abs(interpretation.emotional_charge),
                contradictory=interpretation.status in {"challenged", "unresolved"},
                reality_support=interpretation.confidence if interpretation.supporting_world_event_ids else 0.0,
            ))
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
        self._reconsider_recent_evidence(self_monitor, actual_capacity)
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
        memory_request = any(
            phrase in user_text.lower()
            for phrase in (
                "remember", "what happened", "your memories", "what do you recall",
                "where did we leave",
            )
        )
        groundable_retrievals = [
            item for item in retrievals
            if "autobiographical" in item.memory.tags
            and not item.memory.content.casefold().startswith("i heard you say")
            and not ({"sensorium", "ambient_event"} & item.memory.tags)
        ]
        topic_groundable_retrievals = [
            item for item in groundable_retrievals
            if offline_topic_memory_tags & item.memory.tags
        ]
        if topic_groundable_retrievals:
            best_tag_overlap = max(
                len(offline_topic_memory_tags & item.memory.tags)
                for item in topic_groundable_retrievals
            )
            groundable_retrievals = topic_groundable_retrievals
            groundable_retrievals = [
                item for item in groundable_retrievals
                if len(offline_topic_memory_tags & item.memory.tags) == best_tag_overlap
            ]
        direct_grounding = any(
            (
                f"memory:{item.memory.id}" in considered_ids
                or (
                    synthesis.selected_conversation_candidate_id
                    == conversation_candidate.candidate_id
                    and conversation_candidate.move == "reminisce"
                    and float(item.reasons.get("authored_topic_tag", 0.0)) > 0.0
                )
            )
            and float(item.reasons.get("direct_symbolic_cue", 0.0)) >= 1.0
            for item in groundable_retrievals
        )
        memory_grounding_mode = (
            "required"
            if memory_request and direct_grounding
            else "unavailable"
            if memory_request
            else "optional"
        )
        if memory_request:
            retrieved = [
                item.memory for item in groundable_retrievals
                if (
                    f"memory:{item.memory.id}" in considered_ids
                    or (
                        synthesis.selected_conversation_candidate_id
                        == conversation_candidate.candidate_id
                        and conversation_candidate.move == "reminisce"
                        and float(item.reasons.get("authored_topic_tag", 0.0)) > 0.0
                    )
                )
            ]
        self.memory.record_recall(retrieved, now)
        available_artifacts = [
            item for item in available_artifacts
            if f"artifact:{item.artifact_id}" in considered_ids
        ]
        for trace in retrieved_memory_trace:
            trace["considered_in_synthesis"] = f"memory:{trace['memory_id']}" in considered_ids
            memory_item = next(
                (item.memory for item in retrievals if item.memory.id == trace["memory_id"]), None
            )
            trace["active_topic_score"] = (
                continuity_state.memory_context_score(memory_item.content) if memory_item else 0.0
            )
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
        selected_ritual = next(
            (item for item in self.dyadic_rituals.rituals if item.ritual_id == synthesis.selected_dyadic_ritual_id),
            None,
        )
        conversation_grounding_pool = (
            prior_memory_retrievals
            if conversation_candidate.move == "reminisce_and_note"
            else candidate_memory_retrievals
        )
        grounded_conversation_memory_id = next((
            item.memory.id for item in conversation_grounding_pool
            if f"memory:{item.memory.id}" in considered_ids
        ), None)
        if (
            grounded_conversation_memory_id is None
            and conversation_candidate.move == "reminisce"
        ):
            grounded_conversation_memory_id = next((
                item.memory.id for item in conversation_grounding_pool
                if float(item.reasons.get("authored_topic_tag", 0.0)) > 0.0
            ), None)
        conversation_memory_required = (
            conversation_candidate.move in {"reminisce", "reminisce_and_note"}
            or conversation_candidate.extension_move in {"compare", "reminisce"}
        )
        selected_conversation = (
            replace(conversation_candidate, source_memory_id=grounded_conversation_memory_id)
            if synthesis.selected_conversation_candidate_id == conversation_candidate.candidate_id
            and conversation_candidate.move != "basic_reply"
            and (not conversation_memory_required or grounded_conversation_memory_id is not None)
            else None
        )
        effective_conversation_candidate = selected_conversation or conversation_candidate
        if initiative_assessment.proposal is not None:
            if (
                selected_conversation is not None
                and selected_conversation.initiative_proposal_id
                == initiative_assessment.proposal.proposal_id
            ):
                initiative_assessment = initiative_assessment.with_outcome(
                    "proposal_selected", "initiative:selected_by_synthesis",
                )
                continuity_state.record_initiative_source(
                    initiative_assessment.proposal.source_id
                )
            elif conversation_candidate.initiative_proposal_id is not None:
                initiative_assessment = initiative_assessment.with_outcome(
                    "proposal_denied_by_synthesis", "initiative:not_selected_by_synthesis",
                )
            elif initiative_assessment.outcome == "proposal_available":
                initiative_assessment = initiative_assessment.with_outcome(
                    "proposal_inhibited", "initiative:conversation_gate",
                )
        self._last_initiative_assessment = initiative_assessment
        self._last_conversation_candidate = effective_conversation_candidate
        if selected_conversation and selected_conversation.tendency_id:
            self._behavior_tendency_history = [
                *self._behavior_tendency_history,
                (selected_conversation.tendency_id, self.timestep),
            ][-24:]
        if selected_conversation and selected_conversation.continuity_source_id:
            self._life_callback_history = [
                *self._life_callback_history,
                selected_conversation.continuity_source_id,
            ][-16:]
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
            selected_ritual=selected_ritual,
            selected_conversation=selected_conversation,
        )
        if (
            initiative_assessment.outcome == "proposal_selected"
            and initiative_assessment.proposal is not None
            and selected_conversation is not None
        ):
            validate_initiative_realization(
                proposal=initiative_assessment.proposal,
                conversation_candidate=selected_conversation,
                action_decision=action_decision,
            )
        transition_reason = None
        if input_act == "leave_or_return" and "back" not in user_text.lower() and "return" not in user_text.lower():
            transition_reason = "interrupted"
        elif resistance:
            transition_reason = "avoided"
        elif (
            continuity_state.active_topic
            and (
                continuity_state.active_topic.depth >= 8
                or continuity_state.active_topic.freshness <= 0.55
            )
            and not (selected_conversation and selected_conversation.extension_move)
        ):
            transition_reason = "exhausted"
        continuity_state.complete_turn(
            extension_move=(selected_conversation.extension_move if selected_conversation else None),
            action_kind=action_decision.action_kind,
            transition_reason=transition_reason,
        )
        if selected_conversation and selected_conversation.move in {"defer_and_note", "reminisce_and_note"}:
            user_requested_retention = (
                "journal:user_requested_retention"
                in selected_conversation.reason_codes
            )
            self.intentions.add_open_loop(OpenLoop(
                topic=user_text[:160],
                emotional_charge=max(0.2, min(1.0, appraisal.novelty + 0.2)),
                created_at=now,
                last_touched=now,
                urgency=0.62,
                preferred_resolution=(
                    "revisit with the same participant"
                    if user_requested_retention
                    else "revisit when language capability is available"
                ),
                topic_key=selected_conversation.topic_key,
                actor_id=self.active_actor_id,
                source_event_id=input_world_event.event_id,
                reason=(
                    "promised_followup"
                    if user_requested_retention
                    else "offline_knowledge_unavailable"
                ),
                required_capability=selected_conversation.required_capability,
                status="pending",
            ))
            journal_config = dict((self.cartridge_data or {}).get("journal", {}))
            note_template = str(journal_config.get(
                "pending_note_template",
                "I retained this unfinished question for later examination: {topic}",
            ))
            note_text = note_template.replace("{topic}", user_text[:160]).strip()[:500]
            if not any(item.text == note_text for item in self.journal.entries[-16:]):
                self.propose_world_action(
                    "write_journal",
                    {"text": note_text, "entry_kind": "field_note"},
                    event_time=now,
                )
        elif (
            selected_conversation and selected_conversation.move == "return_to_topic"
            and due_open_loop and action_decision.communicative_function == "return_to_topic"
        ):
            due_open_loop.status = "surfaced"
        self._accept_action_decision(action_decision, selected_proposal)
        active_autobiographical_ids = tuple(
            item.influence_id.removeprefix("autobiographical:")
            for item in synthesis.considered_influences
            if item.kind == "autobiographical_meaning"
        )
        context_tags = (
            "interaction",
            "interruption" if interruption.get("activity_interrupted") else "ongoing",
            communicative.dialogue_act,
        )
        selected_skill = self.skills.skills.get(action_decision.selected_skill_id or "")
        if selected_skill is None:
            selected_skill = self.skills.get_or_create(
                f"{action_decision.action_kind}:{action_decision.communicative_function or 'none'}",
                action_decision.action_kind, action_decision.communicative_function,
                context_tags, self.timestep,
            )
        self._pending_skill_id = selected_skill.skill_id if selected_skill else None
        expectation_record, outcome_record, prediction_record, development_episode = build_episode(
            tick=self.timestep, decision=action_decision, synthesis=synthesis,
            active_interpretation_ids=active_autobiographical_ids,
            retrieved_memory_ids=tuple(item.memory.id for item in retrievals),
            world_event_ids=(input_world_event.event_id,),
            subjective_experience_ids=(experience.experience_id,) if experience else (),
            day=day_index,
        )
        self.development_episodes.add(development_episode)
        ritual_trigger = "work_interruption_acknowledgment" if interruption.get("input_arrived") else "ongoing_presence"
        self.dyadic_rituals.observe(
            f"actor:{self.active_actor_id:08x}", ritual_trigger, action_decision.action_kind,
            action_decision.communicative_function, self.timestep,
            development_episode.episode_id, success=True,
        )
        for interpretation_id in active_autobiographical_ids:
            for memory_item in retrievals[:4]:
                self.memory_connections.connect(
                    interpretation_id, memory_item.memory.id, "interpretation_context",
                    development_episode.context_signature, self.timestep,
                    (interpretation_id, memory_item.memory.id, development_episode.episode_id),
                )
        self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "development_episode", {
            "expectation": expectation_record.to_dict(), "outcome": outcome_record.to_dict(),
            "prediction_error": prediction_record.to_dict(), "episode": development_episode.to_dict(),
            "memory_types": ["development_episode"],
        })
        for influence in [
            item for item in (*synthesis.considered_influences, *synthesis.inhibited_influences)
            if item.kind == "autobiographical_meaning"
        ]:
            interpretation_id = influence.influence_id.removeprefix("autobiographical:")
            considered = influence in synthesis.considered_influences
            use = InterpretationUseOutcome(
                1, _stable_record_id("interpretation_use", interpretation_id, synthesis.synthesis_id),
                interpretation_id, synthesis.synthesis_id, action_decision.decision_id, None,
                "emotionally_influential" if considered and influence.emotional_congruence > 0.4
                else "neutral" if considered else "not_integrated",
                influence.strength if considered else 0.0,
                influence.emotional_congruence if considered else 0.0,
                "subjective", self.timestep,
                (interpretation_id, synthesis.synthesis_id, action_decision.decision_id),
                development_episode.context_signature if 'development_episode' in locals() else "",
                considered, not considered, .35 if considered else .1,
            )
            if not any(item.use_outcome_id == use.use_outcome_id for item in self.interpretation_use_outcomes):
                self.interpretation_use_outcomes = [*self.interpretation_use_outcomes, use][-512:]
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
        activity_transition = (
            selected_conversation.activity_transition
            if selected_conversation and selected_conversation.activity_transition
            else "continued" if action_decision.action_kind in {"continue_activity", "silence"}
            else "paused" if action_decision.action_kind == "delay" or interruption.get("activity_interrupted")
            else "continued" if interruption.get("previous_activity") == self.life_state.current_activity
            else self.life_state.activity_status
            if self.life_state.activity_status in {"resumed", "completed", "failed", "abandoned", "changed"}
            else None
        )
        offline_topic_plan = None
        offline_topic_thread = None
        if (
            offline_topic_match.topic_id
            and input_act in {
                "ask_fact", "ask_opinion", "ask_memory", "ask_analysis",
                "inform", "request_action",
            }
        ):
            offline_topic_thread = self.offline_topic_threads.for_topic(
                self.active_actor_id, offline_topic_match.topic_id,
            )
            grounding_memory = next((
                item for item in retrieved
                if (
                    "autobiographical" in item.tags
                    and not item.content.casefold().startswith("i heard you say")
                    and not ({"sensorium", "ambient_event"} & item.tags)
                    and (
                        not offline_topic_memory_tags
                        or (
                            bool(offline_topic_memory_tags & item.tags)
                            and (
                                input_act == "ask_memory"
                                or len(offline_topic_memory_tags & item.tags) >= 2
                            )
                        )
                    )
                )
            ), None)
            topic_activity = (
                self.life_state.current_activity
                if self.life_state.current_activity not in {
                    "", "quiet observation", "responding to interruption",
                }
                else ""
            )
            offline_topic_plan = self.offline_topics.plan(
                match=offline_topic_match,
                thread=offline_topic_thread,
                input_act=input_act,
                turn=self.timestep,
                pressure=top_pressure.magnitude if top_pressure else 0.0,
                familiarity=self.relationship.familiarity,
                memory_id=getattr(grounding_memory, "id", None),
                memory_text=getattr(grounding_memory, "content", None),
                activity=topic_activity,
            )
        self._last_offline_topic_plan = offline_topic_plan
        realized_conversation = (
            selected_conversation
            if selected_conversation is not None
            else replace(effective_conversation_candidate, extension_move=None)
        )
        conversation_choreography = self.conversation_choreography_planner.plan(
            decision=action_decision,
            candidate=realized_conversation,
            continuity=continuity_state,
            body=self.body,
            relationship=self.relationship,
            dominant_pressure=top_pressure.magnitude if top_pressure else 0.0,
            self_monitor=self_monitor,
            activity_transition=activity_transition,
            stable_seed=turn_seed(self.user_id, self.timestep, "conversation_choreography"),
        )
        self._last_conversation_choreography = conversation_choreography
        continuity_state.record_trajectory(conversation_choreography.trajectory_signature)
        choreography_payload = conversation_choreography.to_dict()
        decision_payload["conversation_choreography"] = choreography_payload
        self.persistence.log_event(
            self.identity.name,
            self.user_id,
            self.timestep,
            "conversation_choreography",
            {
                **choreography_payload,
                "memory_types": ["conversation_choreography"],
            },
        )
        performance_plan = self.performance_planner.plan(
            decision=action_decision,
            relationship=self.relationship,
            pressures=self.pressures,
            capacity=synthesis.integration_capacity,
            concealment_mode=communicative.concealment_mode,
            interruption=interruption,
            performance_profile=PerformanceProfile.from_cartridge_tendency(
                (self.cartridge_data or {}).get("performance_tendencies", {}),
                (
                    selected_conversation.performance_tendency_id
                    if selected_conversation and selected_conversation.performance_tendency_id
                    else selected_proposal.performance_tendency_id if selected_proposal else None
                ),
            ),
            self_monitor=self_monitor,
            activity_transition=activity_transition,
            activity_label=self.life_state.current_activity,
            conversation_choreography=conversation_choreography,
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
            offline_realization = dict(
                (self.cartridge_data or {}).get("offline_expression", {})
            )
            authored_voice_examples = list(
                offline_topic_plan.fragments if offline_topic_plan else ()
            )
            example_group = {
                "greeting": "greeting",
                "apologize": "repair",
                "leave_or_return": "farewell",
            }.get(input_act, "question" if input_act.startswith("ask_") else "default")
            authored_voice_examples.extend(
                str(item) for item in offline_realization.get(example_group, ())[:3]
            )
            authored_voice_examples = list(dict.fromkeys(
                item.replace(
                    "{activity}",
                    self.life_state.current_activity or "the current work",
                ).replace(
                    "{topic}",
                    offline_topic_match.label or user_text[:100],
                )
                for item in authored_voice_examples
                if item
            ))[:6]
            realization_max_chars = envelope.max_chars
            if renderer_is_model_backed(self.renderer):
                realization_max_chars = (
                    max(realization_max_chars, 800)
                    if bucket == "LOW"
                    else max(realization_max_chars, 600)
                    if bucket == "MEDIUM"
                    else max(realization_max_chars, 350)
                )
            frame = WorkspaceFrame(
                core_identity_summary=self.ledger.summary() + (f" | beliefs: {self.belief_ledger.values}" if self.belief_ledger.values else ""),
                relationship_summary=relationship_to_qualitative(self.relationship),
                current_affect_bucket=bucket,
                dominant_pressure=dominant_name,
                secondary_pressure=secondary_name,
                selected_intention=selected_intention.name if selected_intention else None,
                retrieved_memories=(
                    [m.content for m in retrieved]
                    + [f"Validated knowledge: {item.content}" for item in available_artifacts]
                    + (
                        [f"Validated knowledge: {due_open_loop.character_position}"]
                        if (
                            selected_conversation
                            and selected_conversation.move == "return_to_topic"
                            and due_open_loop
                            and due_open_loop.character_position
                            and not any(
                                item.content == due_open_loop.character_position
                                for item in available_artifacts
                            )
                        )
                        else []
                    )
                ),
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
                forbidden_claims=[
                    "having no feelings",
                    "memories not listed in the relevant memory field",
                    "private thoughts from the user",
                ],
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
                autobiographical_context=tuple(
                    item.current_meaning for influence in synthesis.considered_influences
                    if influence.kind == "autobiographical_meaning"
                    for item in [self.autobiographical_interpretations.fetch(
                        influence.influence_id.removeprefix("autobiographical:")
                    )]
                    if item is not None and self.autobiographical_interpretations.current(item.experience_id) == item
                )[:2],
                memory_grounding=(
                    "Answer from the listed memories and current autobiographical meaning only. "
                    "Include at least one recalled detail not supplied by the interlocutor; do not invent connective detail."
                    if memory_grounding_mode == "required" else
                    "No directly relevant memory is accessible. Do not invent an event; state bounded uncertainty."
                    if memory_grounding_mode == "unavailable" else None
                ),
                conversation_move=selected_conversation.move if selected_conversation else None,
                conversation_topic=(
                    due_open_loop.topic if selected_conversation
                    and selected_conversation.move == "return_to_topic" and due_open_loop
                    else user_text[:160] if selected_conversation
                    and selected_conversation.move in {"defer_and_note", "reminisce_and_note"}
                    else user_text[:160] if selected_conversation
                    and selected_conversation.move in {"probe", "compare", "speculate", "express_curiosity"}
                    else offline_topic_match.label if offline_topic_match.topic_id
                    else None
                ),
                activity_transition=performance_plan.activity_transition,
                activity_context=(
                    self.life_state.current_activity
                    if selected_conversation and selected_conversation.move == "activity_update"
                    else None
                ),
                conversation_continuity=continuity_state.summary(),
                conversational_obligation=(
                    selected_conversation.obligation if selected_conversation else None
                ),
                optional_extension=(
                    selected_conversation.extension_move if selected_conversation else None
                ),
                conversation_choreography=choreography_payload,
                authored_voice_examples=authored_voice_examples,
                realization_max_chars=realization_max_chars,
                interlocutor_name=(
                    self.actor_registry.fetch(self.active_actor_id).display_name
                    if self.actor_registry.fetch(self.active_actor_id) is not None
                    else None
                ),
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
                    "max_chars": realization_max_chars,
                    "offline_realization": offline_realization,
                    "memory_grounding_mode": memory_grounding_mode,
                    "action_decision": action_decision.to_dict(),
                    "performance_plan": performance_payload,
                    "conversation_candidate": selected_conversation.to_dict() if selected_conversation else None,
                    "conversation_continuity": continuity_state.to_dict(),
                    "conversation_choreography": choreography_payload,
                    "offline_topic_match": offline_topic_match.to_dict(),
                    "offline_topic_plan": (
                        offline_topic_plan.to_dict() if offline_topic_plan else None
                    ),
                    "active_actor_id": self.active_actor_id,
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

        if offline_topic_thread is not None and action_decision.action_kind == "speak" and response:
            record_topic_turn(
                offline_topic_thread,
                plan=offline_topic_plan,
                input_act=input_act,
                turn=self.timestep,
                modality=str(getattr(self.renderer, "_actual_backend", "offline")),
            )

        model_call_metrics = {
            "private_cognition_renderer_called": cognition_execution.renderer_called,
            "expression_renderer_called": expression_renderer_called,
            "total_model_calls": int(cognition_execution.renderer_called) + int(expression_renderer_called),
            "external_model_calls": (
                int(cognition_execution.renderer_called)
                + int(
                    expression_renderer_called
                    and str(getattr(self.renderer, "_actual_backend", "offline")) != "offline"
                )
            ),
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
            "conversation_candidate": effective_conversation_candidate.to_dict(),
            "conversation_continuity": continuity_state.to_dict(),
            "conversation_choreography": choreography_payload,
            "offline_topic_match": offline_topic_match.to_dict(),
            "offline_topic_plan": offline_topic_plan.to_dict() if offline_topic_plan else None,
            "conversation_initiative": initiative_assessment.to_dict(),
            "initiative_memory_eligibility": initiative_memory_eligibility,
            "self_monitor": self_monitor.to_dict(),
            "development": self._development_summary(),
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
            "conversation_candidate": effective_conversation_candidate.to_dict(),
            "conversation_continuity": continuity_state.to_dict(),
            "conversation_choreography": choreography_payload,
            "offline_topic_match": offline_topic_match.to_dict(),
            "offline_topic_plan": offline_topic_plan.to_dict() if offline_topic_plan else None,
            "conversation_initiative": initiative_assessment.to_dict(),
            "initiative_memory_eligibility": initiative_memory_eligibility,
            "self_monitor": self_monitor.to_dict(),
            "development": self._development_summary(),
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
