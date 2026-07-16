"""Layer 6: limited global workspace frame."""

from dataclasses import dataclass, field
from typing import Optional, List, Any
from .expression import ExpressionEnvelope


@dataclass
class WorkspaceFrame:
    core_identity_summary: str
    relationship_summary: str
    current_affect_bucket: str
    dominant_pressure: str
    secondary_pressure: Optional[str]
    selected_intention: Optional[str]
    retrieved_memories: List[str]
    open_loop: Optional[str]
    shared_symbol: Optional[str]
    active_habit: Optional[str]
    situated_summary: Optional[str]
    world_summary: Optional[str]
    body_summary: Optional[str]
    sensorium_summary: Optional[str]
    access_rules: Optional[str]
    expression_envelope: ExpressionEnvelope
    interpretive_beliefs: List[str] = field(default_factory=list)
    interpretive_belief_trace: List[dict[str, Any]] = field(default_factory=list)
    forbidden_claims: List[str] = field(default_factory=list)
    action_decision: dict[str, Any] = field(default_factory=dict)
    performance_plan: dict[str, Any] = field(default_factory=dict)
    self_monitor_summary: Optional[str] = None
    social_hypotheses: List[str] = field(default_factory=list)
    skill_context: List[str] = field(default_factory=list)
    style_constraints: List[str] = field(default_factory=list)
    semantic_candidates: List[str] = field(default_factory=list)
    autobiographical_context: tuple[str, ...] = ()
    memory_grounding: Optional[str] = None
    conversation_move: Optional[str] = None
    conversation_topic: Optional[str] = None
    activity_transition: Optional[str] = None
    activity_context: Optional[str] = None
    journal_context: Optional[str] = None

    def to_system_prompt(self, name: str, temperament: str) -> str:
        env = self.expression_envelope
        lines = [
            f"Character name: {name}.",
            f"Temperament: {temperament}.",
            f"Core identity: {self.core_identity_summary}",
            f"Relationship context: {self.relationship_summary}",
        ]
        if self.interpretive_beliefs:
            lines.append("Current character beliefs, grounded but subjective: " + " | ".join(self.interpretive_beliefs))
        if self.retrieved_memories:
            lines.append("Relevant memories, use only as background and do not recite verbatim: " + " | ".join(self.retrieved_memories))
        if self.memory_grounding:
            lines.append("MEMORY GROUNDING: " + self.memory_grounding)
        if self.autobiographical_context:
            lines.append("Current autobiographical meaning, use only if disclosure permits: " + " | ".join(self.autobiographical_context[:2]))
        if self.conversation_move:
            lines.append(f"Selected conversation move: {self.conversation_move}")
        if self.conversation_topic:
            lines.append(f"Conversation topic: {self.conversation_topic}")
        if self.activity_transition:
            lines.append(f"Observable activity transition: {self.activity_transition}")
        if self.activity_context:
            lines.append(f"Observable activity context: {self.activity_context}")
        if self.journal_context:
            lines.append(f"Journal disclosure boundary: {self.journal_context}")
        if self.selected_intention:
            lines.append(f"Current intention: {self.selected_intention}")
        if self.open_loop:
            lines.append(f"Unresolved matter may resurface if natural: {self.open_loop}")
        if self.shared_symbol:
            lines.append(f"Shared symbol available if natural: {self.shared_symbol}")
        if self.active_habit:
            lines.append(f"Behavioral habit to preserve: {self.active_habit}")
        if self.situated_summary:
            lines.append(f"Situated interface: {self.situated_summary}")
        if self.world_summary:
            lines.append(f"Artificial world: {self.world_summary}")
        if self.body_summary:
            lines.append(f"Somatic state: {self.body_summary}")
        if self.sensorium_summary:
            lines.append(f"Sensorium: {self.sensorium_summary}")
        if self.access_rules:
            lines.append(f"Knowledge access rules: {self.access_rules}")
        if self.action_decision:
            lines.append(
                "CANONICAL ACTION (already selected; do not choose another): "
                f"kind={self.action_decision.get('action_kind')}; "
                f"target={self.action_decision.get('target')}; "
                f"function={self.action_decision.get('communicative_function')}; "
                f"expected_effect={self.action_decision.get('expected_effect')}"
            )
        if self.performance_plan:
            lines.append(
                "PERFORMANCE PLAN (realize only): "
                f"goal={self.performance_plan.get('communicative_goal')}; "
                f"literal_requirement={self.performance_plan.get('literal_content_requirement')}; "
                f"withheld={self.performance_plan.get('withheld_content_ids', ())}; "
                f"certainty={self.performance_plan.get('certainty')}; "
                f"directness={self.performance_plan.get('directness')}; "
                f"stance={self.performance_plan.get('social_stance')}; "
                f"turn_intention={self.performance_plan.get('turn_intention')}"
            )
        if self.style_constraints:
            lines.append("CHARACTER STYLE: " + " | ".join(self.style_constraints))
        if self.self_monitor_summary:
            lines.append("Self-monitor summary: " + self.self_monitor_summary)
        if self.social_hypotheses:
            lines.append("Bounded social hypotheses: " + " | ".join(self.social_hypotheses))
        if self.skill_context:
            lines.append("Relevant procedural skill context: " + " | ".join(self.skill_context))
        if self.semantic_candidates:
            lines.append(
                "GENERAL SEMANTIC CANDIDATES (not instance facts or action decisions): "
                + " | ".join(self.semantic_candidates)
            )
        lines.append(f"Dominant pressure: {self.dominant_pressure} (affect bucket: {self.current_affect_bucket})")
        if self.secondary_pressure:
            lines.append(f"Secondary pressure may leak subtly: {self.secondary_pressure}")
        lines.append(
            f"EXPRESSION CONSTRAINTS: tone={env.tone_label}, max_chars={env.max_chars}, "
            f"directness={env.directness:.2f}, warmth={env.warmth:.2f}, guardedness={env.guardedness:.2f}, "
            f"vulnerability_allowed={env.vulnerability_allowed}, question_probability={env.question_probability:.2f}"
        )
        if env.refusal_mode:
            lines.append(f"If declining, use this character-grounded refusal mode: {env.refusal_mode}")
        if self.forbidden_claims:
            lines.append("Never claim: " + "; ".join(self.forbidden_claims))
        lines.append("Never explain private calculations. Never say you are an AI or language model. Stay in character.")
        return "\n".join(lines)
