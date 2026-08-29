from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "persona_engine" / "core" / "engine.py"
OFFLINE = ROOT / "persona_engine" / "core" / "offline_template_renderer.py"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"Missing patch anchor in {path}: {old[:100]!r}")
    if text.count(old) != 1:
        raise RuntimeError(f"Non-unique patch anchor in {path}: {old[:100]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    ENGINE,
    'from .memory import KnowledgeSource, MemoryStore, MemoryUnit\n',
    'from .memory import KnowledgeSource, MemoryStore, MemoryUnit\nfrom .decision_memory import evaluate_history_for_decision\n',
)

replace_once(
    ENGINE,
    '    def _resolve_decision_payload(self, triggers: list[str], risk: float, resistance: str | None = None) -> dict[str, Any]:\n',
    '    def _resolve_decision_payload(self, triggers: list[str], risk: float, resistance: str | None = None, history_evidence: dict[str, Any] | None = None) -> dict[str, Any]:\n',
)

replace_once(
    ENGINE,
    '        dialogue_act = "challenge" if suspicion_value >= 0.60 else "respond"\n        if resistance == "character_refusal":\n',
    '        dialogue_act = "challenge" if suspicion_value >= 0.60 else "respond"\n        history_payload = dict(history_evidence or {})\n        # Retrieved lived history may qualify a present trust/commitment decision,\n        # but it never outranks explicit identity/resistance policy and never\n        # mutates relationship state on its own.\n        if dialogue_act == "respond" and bool(history_payload.get("active")) and resistance is None:\n            dialogue_act = "qualified_response"\n        if resistance == "character_refusal":\n',
)

replace_once(
    ENGINE,
    '            "risk_bucket": bucket_risk(risk),\n        }\n',
    '            "risk_bucket": bucket_risk(risk),\n            "history_evidence": history_payload or {"active": False, "strength": 0.0, "memory_ids": [], "reason": "none"},\n        }\n',
)

replace_once(
    ENGINE,
    '        retrieved_memory_trace = [\n            {\n                "memory_id": memory.id,\n                "source": memory.source.value,\n                "tags": sorted(memory.tags),\n                "created_at": memory.created_at,\n                "content": memory.content,\n            }\n            for memory in retrieved\n        ]\n\n        triggers = []\n',
    '        retrieved_memory_trace = [\n            {\n                "memory_id": memory.id,\n                "source": memory.source.value,\n                "tags": sorted(memory.tags),\n                "created_at": memory.created_at,\n                "content": memory.content,\n            }\n            for memory in retrieved\n        ]\n        history_evidence = evaluate_history_for_decision(user_text, retrieved, self.relationship)\n\n        triggers = []\n',
)

replace_once(
    ENGINE,
    '        decision_payload = self._resolve_decision_payload(triggers, risk, resistance)\n',
    '        decision_payload = self._resolve_decision_payload(\n            triggers,\n            risk,\n            resistance,\n            history_evidence=history_evidence.to_dict(),\n        )\n',
)

replace_once(
    OFFLINE,
    '        if dialogue_act == "withdraw":\n            return "quiet"\n',
    '        if dialogue_act == "withdraw":\n            return "quiet"\n        if dialogue_act == "qualified_response":\n            return "uncertain"\n',
)

print("Applied bounded history evidence integration")
