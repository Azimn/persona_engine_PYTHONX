"""Character-owned conversational agenda projection for Project Ensemble.

The agenda is not an engagement optimizer and does not reward conversation
length. It projects already-owned continuing state into a small inspectable set
of reasons the subject might carry something forward into the present turn.

V1 is deliberately a projection rather than a new persistence authority. The
underlying intention, open loop, shared symbol, habit, relationship, and affect
remain canonical in their existing subsystems. The agenda can be rebuilt after
restart from that state.
"""

from __future__ import annotations

from dataclasses import dataclass


CONVERSATIONAL_AGENDA_VERSION = "ensemble-conversational-agenda-v1"


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True)
class ConversationalAgenda:
    active_intention: str | None = None
    unresolved_thread: str | None = None
    shared_symbol: str | None = None
    active_habit: str | None = None
    relationship_stance: str | None = None
    social_goal: str | None = None
    initiative_pressure: float = 0.0
    initiative_allowed: bool = False
    provenance: tuple[str, ...] = ()
    version: str = CONVERSATIONAL_AGENDA_VERSION

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "active_intention": self.active_intention,
            "unresolved_thread": self.unresolved_thread,
            "shared_symbol": self.shared_symbol,
            "active_habit": self.active_habit,
            "relationship_stance": self.relationship_stance,
            "social_goal": self.social_goal,
            "initiative_pressure": round(float(self.initiative_pressure), 6),
            "initiative_allowed": bool(self.initiative_allowed),
            "provenance": list(self.provenance),
        }


def agenda_from_expression_request(request) -> ConversationalAgenda:
    """Project existing trusted subject state into a conversational agenda.

    The pressure formula is intentionally transparent. Unfinished business and
    an active intention are the strongest causes. Familiarity/attachment can
    make initiative easier; guardedness suppresses it. A shared symbol or active
    habit adds a smaller continuity contribution. No component depends on user
    retention, response length, or a generic desire to keep talking.
    """

    resolved = request.resolved_state if isinstance(request.resolved_state, dict) else {}
    experience = resolved.get("experience_context", {}) if isinstance(resolved, dict) else {}
    continuity = experience.get("continuity", {}) if isinstance(experience, dict) else {}
    relationship = experience.get("relationship", {}) if isinstance(experience, dict) else {}
    if not isinstance(continuity, dict):
        continuity = {}
    if not isinstance(relationship, dict):
        relationship = {}

    active_intention = str(continuity.get("selected_intention", "") or "").strip() or None
    unresolved_thread = str(continuity.get("open_loop", "") or "").strip() or None
    shared_symbol = str(continuity.get("shared_symbol", "") or "").strip() or None
    active_habit = str(continuity.get("active_habit", "") or "").strip() or None
    stance = str(relationship.get("stance", "") or "").strip() or None

    familiarity = _clamp(float(relationship.get("familiarity", 0.0) or 0.0))
    attachment = _clamp(float(relationship.get("attachment", 0.0) or 0.0))
    guardedness = _clamp(float(relationship.get("guardedness", 0.0) or 0.0))
    tension = _clamp(float(relationship.get("tension", 0.0) or 0.0))

    pressure = 0.05
    provenance: list[str] = []
    if active_intention:
        pressure += 0.28
        provenance.append("continuity.selected_intention")
    if unresolved_thread:
        pressure += 0.38
        provenance.append("continuity.open_loop")
    if shared_symbol:
        pressure += 0.10
        provenance.append("continuity.shared_symbol")
    if active_habit:
        pressure += 0.06
        provenance.append("continuity.active_habit")
    if familiarity or attachment:
        pressure += 0.12 * ((familiarity + attachment) / 2.0)
        provenance.append("relationship.familiarity_attachment")
    if guardedness:
        pressure -= 0.18 * guardedness
        provenance.append("relationship.guardedness")
    # High tension can produce initiative when there is unfinished business,
    # but does not independently create a reason to speak.
    if unresolved_thread and tension:
        pressure += 0.08 * tension
        provenance.append("relationship.tension_with_open_loop")

    pressure = _clamp(pressure)

    social_goal = None
    if active_intention:
        social_goal = active_intention
    elif unresolved_thread:
        social_goal = "revisit unresolved interaction"
    elif shared_symbol and familiarity >= 0.55:
        social_goal = "maintain shared continuity"

    return ConversationalAgenda(
        active_intention=active_intention,
        unresolved_thread=unresolved_thread,
        shared_symbol=shared_symbol,
        active_habit=active_habit,
        relationship_stance=stance,
        social_goal=social_goal,
        initiative_pressure=pressure,
        initiative_allowed=pressure >= 0.45 and bool(active_intention or unresolved_thread or shared_symbol),
        provenance=tuple(provenance),
    )
