from pathlib import Path

path = Path(__file__).resolve().parents[1] / "core" / "engine.py"
text = path.read_text(encoding="utf-8")

old_init = '''        self.consistency = ConsistencyLayer(self.validator)\n        self.persistence = Persistence(db_path)\n        self.deception_ledger = DeceptionLedger()\n'''
new_init = '''        self.consistency = ConsistencyLayer(self.validator)\n        self.persistence = Persistence(db_path)\n        if self.identity.entity_uuid:\n            self.persistence.bind_subject(self.identity.name, self.user_id, self.identity.entity_uuid)\n        self.deception_ledger = DeceptionLedger()\n'''
if text.count(old_init) != 1:
    raise RuntimeError(f"subject binding anchor expected once, found {text.count(old_init)}")
text = text.replace(old_init, new_init, 1)

old_persist = '''    def _persist(self):\n        self.persistence.save_many(self.identity.name, self.user_id, self._serialize_state())\n'''
new_persist = '''    def _persist(self):\n        state = self._serialize_state()\n        self.persistence.save_many(self.identity.name, self.user_id, state)\n        self.persistence.record_checkpoint(self.identity.name, self.user_id, state)\n'''
if text.count(old_persist) != 1:
    raise RuntimeError(f"persist anchor expected once, found {text.count(old_persist)}")
text = text.replace(old_persist, new_persist, 1)

path.write_text(text, encoding="utf-8")
