from pathlib import Path

path = Path(__file__).resolve().parents[1] / "tests" / "test_engine.py"
text = path.read_text(encoding="utf-8")
old = '''        gates = {trace["gate"]: trace["action"] for trace in res["suppression_trace"]}\n        assert gates["output_validator"] == "blocked"\n        assert gates["renderer_sanitizer"] == "sanitized"\n        assert "As an AI" not in res["response"]\n'''
new = '''        gates = {trace["gate"]: trace["action"] for trace in res["suppression_trace"]}\n        assert gates["output_validator"] == "blocked"\n        assert gates["consistency_layer"] == "fallback"\n        assert res["validation_action"] == "fallback_identity_only"\n        assert "As an AI" not in res["response"]\n'''
if text.count(old) != 1:
    raise RuntimeError(f"expected one legacy validator assertion block, found {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
