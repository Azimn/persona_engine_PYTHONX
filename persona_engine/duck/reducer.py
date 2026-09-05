"""Serialized typed canonical patch reducer for organism-owned state."""

from __future__ import annotations

from .types import OrganismState, StatePatch


AUTHORITY = {
    "scheduler": {"tick", "scheduler_state"},
    "situation": {"situation"},
    "motivation": {"drive_state", "active_goals"},
    "action_selector": {"current_intention"},
    "executor": {"action_ledger", "commitments"},
    "prediction": {"prediction_ledger"},
    "workspace": {"working_memory"},
}


class CanonicalReducer:
    def authorize(self, patch: StatePatch) -> None:
        allowed = AUTHORITY.get(patch.source_module, set())
        if patch.domain not in allowed:
            raise PermissionError(f"{patch.source_module} cannot write DUCK domain {patch.domain}")

    def apply(self, state: OrganismState, patch: StatePatch) -> None:
        self.authorize(patch)
        if patch.domain == "tick":
            state.tick = int(patch.new_value)
        elif patch.domain == "scheduler_state":
            state.scheduler_state = dict(patch.new_value)
        elif patch.domain == "situation":
            state.situation = patch.new_value
        elif patch.domain == "drive_state":
            state.drive_state = dict(patch.new_value)
        elif patch.domain == "active_goals":
            state.active_goals = list(patch.new_value)
        elif patch.domain == "current_intention":
            state.current_intention = patch.new_value
        elif patch.domain == "action_ledger":
            state.action_ledger = list(patch.new_value)
        elif patch.domain == "commitments":
            state.commitments = list(patch.new_value)
        elif patch.domain == "prediction_ledger":
            state.prediction_ledger = list(patch.new_value)
        elif patch.domain == "working_memory":
            state.working_memory = list(patch.new_value)
        else:
            raise KeyError(patch.domain)
