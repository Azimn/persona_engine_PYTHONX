#!/usr/bin/env python3
"""Apply the minimal interlocutor-boundary repair to InteriorEngine."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "persona_engine" / "core" / "engine.py"
text = ENGINE.read_text(encoding="utf-8")

old = """        self._load_state()\n\n    def set_renderer(self, renderer) -> None:\n"""
new = """        self._load_state()\n        self._restore_subject_owned_commitments()\n\n    def set_renderer(self, renderer) -> None:\n"""
if old not in text or text.count(old) != 1:
    raise RuntimeError("engine initialization anchor missing or ambiguous")
text = text.replace(old, new, 1)

old = """        self.world_authority = WorldAuthority.from_list(self.persistence.load(cid, uid, \"world_authority\", []))\n\n    def _serialize_state(self) -> dict:\n"""
new = """        self.world_authority = WorldAuthority.from_list(self.persistence.load(cid, uid, \"world_authority\", []))\n\n    def _restore_subject_owned_commitments(self) -> None:\n        \"\"\"Restore self-owned commitments from canonical subject history.\n\n        Snapshot state remains interlocutor-scoped for compatibility. Commitments\n        are different: once explicitly self-adopted, they belong to the continuing\n        subject rather than to whichever interlocutor happened to be present at\n        adoption. Canonical history is therefore the source used to rehydrate them\n        when a new relationship context opens.\n\n        This deliberately restores only the commitment behavior demonstrated by\n        the interlocutor-continuity probe. Other snapshot families remain unchanged\n        until a separate longitudinal test shows that their ownership is wrong.\n        \"\"\"\n\n        events = self.persistence.load_subject_continuity_events(\n            self.identity.name,\n            self.user_id,\n            event_type=\"commitment_adopted\",\n        )\n        for event in events:\n            payload = event.get(\"payload\") or {}\n            if payload.get(\"adoption_source\") != \"self_decision\":\n                continue\n            kind = str(payload.get(\"commitment_kind\", \"\"))\n            target = str(payload.get(\"commitment_target\", \"\"))\n            if kind != \"non_disclosure\" or not target.strip():\n                continue\n            self.adopt_commitment(\n                kind,\n                target,\n                record_event=False,\n                persist=False,\n            )\n\n    def _serialize_state(self) -> dict:\n"""
if old not in text or text.count(old) != 1:
    raise RuntimeError("engine persistence anchor missing or ambiguous")
text = text.replace(old, new, 1)

ENGINE.write_text(text, encoding="utf-8")
print("Applied subject-owned commitment restoration")
