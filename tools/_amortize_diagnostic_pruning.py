#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
persistence_path = ROOT / "persona_engine" / "core" / "persistence.py"
test_path = ROOT / "persona_engine" / "tests" / "test_bounded_diagnostic_persistence.py"

p = persistence_path.read_text(encoding="utf-8")
old_init = '''        self.diagnostic_event_limit = None if diagnostic_event_limit is None else max(1, int(diagnostic_event_limit))\n        self._subject_bindings: dict[tuple[str, str], tuple[str, int]] = {}\n'''
new_init = '''        self.diagnostic_event_limit = None if diagnostic_event_limit is None else max(1, int(diagnostic_event_limit))\n        # Operational hysteresis: avoid a SELECT/DELETE maintenance cycle on\n        # every logged event. Small limits still prune every event; the normal\n        # 512-row runtime window amortizes maintenance across 128 writes.\n        self._diagnostic_writes_since_prune: dict[tuple[str, str], int] = {}\n        self._subject_bindings: dict[tuple[str, str], tuple[str, int]] = {}\n'''
if old_init not in p:
    raise SystemExit("init anchor not found")
p = p.replace(old_init, new_init, 1)

old_prune_public = '''    def prune_diagnostic_events(self, character_id: str, user_id: str) -> int:\n        """Bound recent operational telemetry without touching lived history."""\n\n        with self._connection() as conn:\n            return self._prune_diagnostic_events_conn(conn, character_id, user_id)\n\n'''
new_prune_public = '''    def _diagnostic_prune_stride(self) -> int:\n        limit = self.diagnostic_event_limit\n        if limit is None:\n            return 0\n        return max(1, min(128, max(1, int(limit) // 4)))\n\n    def prune_diagnostic_events(self, character_id: str, user_id: str) -> int:\n        """Bound recent operational telemetry without touching lived history."""\n\n        with self._connection() as conn:\n            removed = self._prune_diagnostic_events_conn(conn, character_id, user_id)\n        self._diagnostic_writes_since_prune[(str(character_id), str(user_id))] = 0\n        return removed\n\n'''
if old_prune_public not in p:
    raise SystemExit("public prune anchor not found")
p = p.replace(old_prune_public, new_prune_public, 1)

old_log_prune = '''            self._prune_diagnostic_events_conn(conn, character_id, user_id)\n\n    def _next_sequence_conn'''
new_log_prune = '''            if self.diagnostic_event_limit is not None:\n                key = (str(character_id), str(user_id))\n                writes = self._diagnostic_writes_since_prune.get(key, 0) + 1\n                stride = self._diagnostic_prune_stride()\n                if writes >= stride:\n                    self._prune_diagnostic_events_conn(conn, character_id, user_id)\n                    writes = 0\n                self._diagnostic_writes_since_prune[key] = writes\n\n    def _next_sequence_conn'''
if old_log_prune not in p:
    raise SystemExit("log prune anchor not found")
p = p.replace(old_log_prune, new_log_prune, 1)
persistence_path.write_text(p, encoding="utf-8")

# The tiny-limit regression still prunes each write. Add a normal-runtime bound
# test to make the hysteresis envelope explicit without pretending it is cognition.
t = test_path.read_text(encoding="utf-8")
t += '''\n\ndef test_normal_runtime_pruning_is_amortized_but_stays_inside_operational_slack():\n    with tempfile.TemporaryDirectory() as d:\n        path = os.path.join(d, "state.db")\n        p = Persistence(path, diagnostic_event_limit=512)\n        p.bind_subject("K", "u", str(uuid.uuid4()))\n        for index in range(2000):\n            p.log_event("K", "u", index, "diagnostic", {"memory_types": ["neutral"]})\n        retained = _count(path, "event_log")\n        assert 512 <= retained < 512 + 128\n        assert p._diagnostic_prune_stride() == 128\n        assert _count(path, "consolidation_evidence") == 2000\n'''
test_path.write_text(t, encoding="utf-8")
