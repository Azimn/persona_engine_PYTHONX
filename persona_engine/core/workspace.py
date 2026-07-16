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
    performance_guidance: List[str] = field(default_factory=list)

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
        if self.performance_guidance:
            lines.append("CHARACTER PERFORMANCE: " + " | ".join(self.performance_guidance))
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
