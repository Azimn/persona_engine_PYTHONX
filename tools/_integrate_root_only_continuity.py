#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"expected block not found in {path}: {old[:100]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# 1. Separate historical canonical validity from the new root-only write policy.
continuity = ROOT / "persona_engine/core/continuity.py"
replace_once(
    continuity,
    "STATE_DIGEST_SCHEMA_VERSION = \"1.0\"\nSUBJECT_TIME_SEMANTICS = \"engine_timestep\"\n",
    "STATE_DIGEST_SCHEMA_VERSION = \"1.0\"\nSUBJECT_TIME_SEMANTICS = \"engine_timestep\"\n\n# New runtime writes retain causal roots only. Historical v1 ledgers may still\n# contain derived canonical verification records; canonical_continuity_eligible\n# remains the compatibility validator for those older streams.\nCANONICAL_CONTINUITY_ROOT_EVENT_TYPES = frozenset({\n    \"input\",\n    \"user_statement\",\n    \"time_advance\",\n    \"commitment_adopted\",\n    \"sensor_observation\",\n    \"world_fact\",\n    \"manual_authorized_fact\",\n    \"world_action_resolution\",\n})\n",
)
replace_once(
    continuity,
    "def canonical_json(value: Any) -> str:\n",
    "def canonical_continuity_root_eligible(event_type: str, payload: dict[str, Any] | None = None) -> bool:\n    \"\"\"Return whether a new runtime event belongs in durable causal history.\n\n    This is intentionally narrower than ``canonical_continuity_eligible``. The\n    latter accepts historical v1 derived records for migration/replay. This\n    predicate governs new writes and fails closed for unknown event families.\n    \"\"\"\n\n    event_type = str(event_type)\n    return event_type in CANONICAL_CONTINUITY_ROOT_EVENT_TYPES and canonical_continuity_eligible(event_type, payload)\n\n\ndef canonical_json(value: Any) -> str:\n",
)

# 2. Persist full diagnostics, but give canonical continuity its own root payload.
persistence = ROOT / "persona_engine/core/persistence.py"
replace_once(
    persistence,
    "    canonical_continuity_eligible,\n    event_authority,\n",
    "    canonical_continuity_eligible,\n    canonical_continuity_root_eligible,\n    event_authority,\n",
)
replace_once(
    persistence,
    "    def log_event(self, character_id: str, user_id: str, timestep: int, event_type: str, payload: dict):\n        \"\"\"Write the broad diagnostic log and, when eligible, canonical continuity.\"\"\"\n\n        now = time.time()\n        payload = dict(payload or {})\n",
    "    def log_event(\n        self,\n        character_id: str,\n        user_id: str,\n        timestep: int,\n        event_type: str,\n        payload: dict,\n        *,\n        continuity_payload: dict[str, Any] | None = None,\n        continuity_payload_schema: str | None = None,\n    ):\n        \"\"\"Write diagnostics plus the minimum-sufficient durable causal root.\n\n        ``payload`` remains the rich recent diagnostic packet. New canonical\n        history is intentionally narrower and may receive a separate exogenous\n        root payload. Historical v1 readers remain able to consume older derived\n        canonical rows.\n        \"\"\"\n\n        now = time.time()\n        payload = dict(payload or {})\n        root_payload = dict(continuity_payload) if continuity_payload is not None else dict(payload)\n",
)
replace_once(
    persistence,
    "            if canonical_continuity_eligible(event_type, payload):\n                self._append_continuity_event_conn(\n                    conn,\n                    character_id=character_id,\n                    user_id=user_id,\n                    timestep=timestep,\n                    event_type=event_type,\n                    payload=payload,\n                    wall_time=now,\n                    legacy_event_id=legacy_id,\n                )\n",
    "            if canonical_continuity_root_eligible(event_type, root_payload):\n                self._append_continuity_event_conn(\n                    conn,\n                    character_id=character_id,\n                    user_id=user_id,\n                    timestep=timestep,\n                    event_type=event_type,\n                    payload=root_payload,\n                    wall_time=now,\n                    legacy_event_id=legacy_id,\n                    payload_schema=continuity_payload_schema,\n                )\n",
)
replace_once(
    persistence,
    "                if not isinstance(payload, dict) or not canonical_continuity_eligible(str(event_type), payload):\n                    continue\n",
    "                # Legacy diagnostic migration keeps only causal roots. Older\n                # continuity tables that already contain derived v1 rows remain\n                # readable; this prevents a fresh migration from recreating the\n                # redundancy that root-only persistence removes.\n                if not isinstance(payload, dict) or not canonical_continuity_root_eligible(str(event_type), payload):\n                    continue\n",
)

# 3. Preserve only context actually submitted by the host in the input root.
engine = ROOT / "persona_engine/core/engine.py"
replace_once(
    engine,
    "        server_truth = dict(server_truth or {})\n        visible_context = dict(visible_context or {})\n        submitted_visible_context = dict(visible_context)\n",
    "        submitted_server_truth = dict(server_truth or {})\n        server_truth = dict(submitted_server_truth)\n        visible_context = dict(visible_context or {})\n        submitted_visible_context = dict(visible_context)\n",
)
replace_once(
    engine,
    "        input_payload[\"classification\"] = input_classification.__dict__\n        input_payload[\"canonical_truth\"] = can_promote_to_canonical_memory(\"input\", input_payload)\n        self.persistence.log_event(self.identity.name, self.user_id, self.timestep, \"input\", input_payload)\n",
    "        input_payload[\"classification\"] = input_classification.__dict__\n        input_payload[\"canonical_truth\"] = can_promote_to_canonical_memory(\"input\", input_payload)\n        input_root_payload = {\"user_text\": user_text}\n        if submitted_server_truth:\n            input_root_payload[\"server_truth\"] = submitted_server_truth\n        if submitted_visible_context:\n            input_root_payload[\"visible_context\"] = submitted_visible_context\n        self.persistence.log_event(\n            self.identity.name,\n            self.user_id,\n            self.timestep,\n            \"input\",\n            input_payload,\n            continuity_payload=input_root_payload,\n            continuity_payload_schema=\"input-root-v2\",\n        )\n",
)

# 4. Update the old direct-write expectation: state_transition remains diagnostic,
# while historical state_transition rows are still valid v1 imports.
ledger_test = ROOT / "persona_engine/tests/test_continuity_ledger.py"
replace_once(
    ledger_test,
    "        assert [event[\"event_type\"] for event in events] == [\"input\", \"state_transition\"]\n        assert [event[\"sequence\"] for event in events] == [1, 2]\n",
    "        assert [event[\"event_type\"] for event in events] == [\"input\"]\n        assert [event[\"sequence\"] for event in events] == [1]\n",
)
# Exercise migration filtering of a formerly canonical derived row.
replace_once(
    ledger_test,
    "            conn.execute(\n                \"INSERT INTO event_log(character_id,user_id,timestep,event_type,payload,created_at) VALUES(?,?,?,?,?,?)\",\n                (\"Character\", \"user\", 1, \"renderer_output\", json.dumps({\"text\": \"not biography\"}), 1.1),\n            )\n",
    "            conn.execute(\n                \"INSERT INTO event_log(character_id,user_id,timestep,event_type,payload,created_at) VALUES(?,?,?,?,?,?)\",\n                (\"Character\", \"user\", 1, \"renderer_output\", json.dumps({\"text\": \"not biography\"}), 1.1),\n            )\n            conn.execute(\n                \"INSERT INTO event_log(character_id,user_id,timestep,event_type,payload,created_at) VALUES(?,?,?,?,?,?)\",\n                (\"Character\", \"user\", 1, \"state_transition\", json.dumps({\"relationship_after\": {\"trust\": 0.2}}), 1.2),\n            )\n",
)

# 5. Add explicit production and legacy-compatibility regressions.
new_test = ROOT / "persona_engine/tests/test_root_only_continuity.py"
new_test.write_text('''"""Root-only durable continuity and v1 migration compatibility."""\n\nimport os\nimport tempfile\nimport uuid\nfrom pathlib import Path\n\nfrom persona_engine.agent import CharacterAgent\nfrom persona_engine.core.persistence import Persistence\nfrom persona_engine.core.replay import replay_from_continuity_bundle, validate_continuity_bundle\n\nROOT = Path(__file__).resolve().parents[1]\nCART = ROOT / "cartridges" / "pretorius.snp"\n\n\ndef test_runtime_writes_only_causal_root_with_exogenous_input_context():\n    with tempfile.TemporaryDirectory() as d:\n        agent = CharacterAgent(cartridge_path=str(CART), user_id="root_only", db_path=os.path.join(d, "state.db"))\n        agent.say(\n            "I am in the north gallery.",\n            server_truth={"zone": "north_gallery", "bell_state": "ringing"},\n            visible_context={"notice_board": "restoration scheduled"},\n        )\n        events = agent.engine.persistence.load_continuity_events(agent.engine.identity.name, agent.engine.user_id)\n        assert [event["event_type"] for event in events] == ["input"]\n        event = events[0]\n        assert event["payload_schema"] == "input-root-v2"\n        assert event["payload"] == {\n            "user_text": "I am in the north gallery.",\n            "server_truth": {"zone": "north_gallery", "bell_state": "ringing"},\n            "visible_context": {"notice_board": "restoration scheduled"},\n        }\n        assert "classification" not in event["payload"]\n        assert "canonical_truth" not in event["payload"]\n        assert "memory_types" not in event["payload"]\n\n\ndef _legacy_event(subject_uuid, sequence, event_type, payload, authority="canonical_event"):\n    return {\n        "event_uuid": str(uuid.uuid4()),\n        "subject_uuid": subject_uuid,\n        "character_id": "Pretorius",\n        "user_id": "legacy_user",\n        "sequence": sequence,\n        "continuity_epoch": 0,\n        "subject_time": float(sequence),\n        "wall_time": float(sequence),\n        "source_actor": "legacy",\n        "source_class": "legacy",\n        "authority_class": authority,\n        "event_type": event_type,\n        "visibility": "character_observed",\n        "canonicality": "canonical_event",\n        "causal_parents": [],\n        "payload_schema": "legacy-event-v1",\n        "payload": payload,\n        "legacy_event_id": None,\n    }\n\n\ndef test_legacy_v1_derived_rows_remain_importable_and_replayable():\n    subject_uuid = str(uuid.uuid4())\n    bundle = {\n        "schema_version": "1.0",\n        "subject_uuid": subject_uuid,\n        "character_id": "Pretorius",\n        "user_id": "legacy_user",\n        "continuity_epoch": 0,\n        "after_sequence": 0,\n        "events": [\n            _legacy_event(subject_uuid, 1, "input", {"user_text": "Hello."}, "reported_input"),\n            _legacy_event(subject_uuid, 2, "state_transition", {"relationship_after": {"trust": 0.0}}, "character_state_authority"),\n            _legacy_event(subject_uuid, 3, "sensorium", {"world": {"zone": "study"}}, "world_authority"),\n        ],\n        "checkpoint": None,\n    }\n    validated = validate_continuity_bundle(bundle)\n    assert [event["event_type"] for event in validated] == ["input", "state_transition", "sensorium"]\n    replay = replay_from_continuity_bundle(str(CART), bundle, user_id="legacy_user")\n    assert replay.complete is True\n    assert replay.root_events_replayed == 1\n    assert replay.derived_events_skipped == 2\n    with tempfile.TemporaryDirectory() as d:\n        store = Persistence(os.path.join(d, "state.db"))\n        store.bind_subject("Pretorius", "legacy_user", subject_uuid)\n        assert store.import_continuity_tail("Pretorius", "legacy_user", bundle) == 3\n        assert [e["event_type"] for e in store.load_continuity_events("Pretorius", "legacy_user")] == [\n            "input", "state_transition", "sensorium"\n        ]\n''', encoding="utf-8")

print("root-only continuity integration staged")
