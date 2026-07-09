"""Contract tests for anchored noncanonical interpretation objects."""

from __future__ import annotations

from pathlib import Path
import inspect
import os
import subprocess
import sys
import tempfile

from persona_engine.agent import CharacterAgent
from persona_engine.core.emotion import EmotionalPressure, PressureSystem
from persona_engine.core.interpretation import (
    ALLOWED_DISTORTIONS,
    InterpretationEngine,
    InterpretationSource,
    sources_from_mapping,
)

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "cartridges" / "pretorius.snp"


def _pressures(name="fear"):
    pressures = PressureSystem()
    pressures.add(EmotionalPressure(name, 0.6))
    return pressures


def test_no_visible_sources_produces_no_beliefs():
    result = InterpretationEngine().form_beliefs(visible_sources=(), pressure_state=_pressures())
    assert result.beliefs == ()


def test_interpretation_uses_source_ids_and_support_keys():
    sources = sources_from_mapping({"user_absent_minutes": 45}, "visible_context")
    result = InterpretationEngine().form_beliefs(visible_sources=sources, pressure_state=_pressures())
    assert result.beliefs
    belief = result.beliefs[0]
    assert belief.source_ids == (sources[0].source_id,)
    assert belief.support_keys == ("user_absent_minutes",)


def test_interpretive_beliefs_are_noncanonical():
    sources = sources_from_mapping({"user_absent_minutes": 45}, "visible_context")
    belief = InterpretationEngine().form_beliefs(visible_sources=sources, pressure_state=_pressures()).beliefs[0]
    assert belief.canonical is False
    assert belief.distortion in ALLOWED_DISTORTIONS


def test_interpretation_ignores_hidden_sources():
    sources = sources_from_mapping({
        "hidden_location": {"value": "secret room", "visible_to_character": False},
    }, "server")
    result = InterpretationEngine().form_beliefs(visible_sources=sources, pressure_state=_pressures())
    assert sources == ()
    assert result.beliefs == ()


def test_absence_can_be_biased_without_fabrication():
    sources = sources_from_mapping({"user_absent_minutes": 52}, "visible_context")
    result = InterpretationEngine().form_beliefs(
        visible_sources=sources,
        pressure_state=_pressures("attachment"),
        identity_bias={"trust": 0.2, "guardedness": 0.8},
    )
    text = result.beliefs[0].text.lower()
    assert "distance" in text or "waiting" in text
    assert not any(term in text for term in ["door", "person", "footsteps", "outside"])


def test_sound_can_create_watchfulness_without_inventing_agent():
    sources = sources_from_mapping({"ambient_event": "sudden sound"}, "visible_context")
    result = InterpretationEngine().form_beliefs(visible_sources=sources, pressure_state=_pressures("curiosity"))
    text = result.beliefs[0].text.lower()
    assert "watchfulness" in text
    assert "person" not in text and "door" not in text and "footsteps" not in text


def test_ambiguous_user_phrase_can_create_uncertainty_without_accusation():
    sources = sources_from_mapping({"user_text": "Fine."}, "visible_context")
    result = InterpretationEngine().form_beliefs(visible_sources=sources, pressure_state=_pressures())
    text = " ".join(b.text.lower() for b in result.beliefs)
    assert "uncertainty" in text
    assert "lied" not in text and "betray" not in text and "deceived" not in text


def test_interpretation_is_deterministic():
    sources = sources_from_mapping({"user_absent_minutes": 52, "user_text": "Fine."}, "visible_context")
    engine = InterpretationEngine()
    first = engine.form_beliefs(visible_sources=sources, pressure_state=_pressures())
    second = engine.form_beliefs(visible_sources=sources, pressure_state=_pressures())
    assert first == second


def test_interpretation_module_has_no_renderer_import():
    import persona_engine.core.interpretation as interpretation

    source = inspect.getsource(interpretation)
    assert "from .renderer" not in source
    assert "import persona_engine.core.renderer" not in source
    assert "ollama" not in source.lower()


def test_interpretation_has_no_character_literals():
    text = (ROOT / "core" / "interpretation.py").read_text(encoding="utf-8").lower()
    for literal in ["pretorius", "kiki", "henry", "jay", "friendly", "mentor", "rival"]:
        assert literal not in text


def test_engine_logs_interpretive_belief_events():
    with tempfile.TemporaryDirectory() as d:
        agent = CharacterAgent(cartridge_path=str(CART), user_id="contract", db_path=os.path.join(d, "state.db"))
        agent.say("...", visible_context={"user_absent_minutes": 52})
        events = agent.engine.persistence.load_events_since(agent.engine.identity.name, "contract", 0, event_type="belief")
    assert events
    payload = events[-1]["payload"]
    assert payload["belief_id"]
    assert payload["source_ids"]
    assert payload["support_keys"]
    assert payload["canonical"] is False


def test_workspace_contains_belief_not_hidden_fact():
    with tempfile.TemporaryDirectory() as d:
        agent = CharacterAgent(cartridge_path=str(CART), user_id="workspace_contract", db_path=os.path.join(d, "state.db"))
        result = agent.say(
            "Fine.",
            server_truth={"hidden_location": {"value": "secret room", "visible_to_character": False}},
            visible_context={"user_text": "Fine."},
        )
    assert result["interpretive_belief_trace"]
    assert "secret room" not in result["system_prompt"]
    assert "Current character beliefs" in result["system_prompt"]


def test_interpretive_beliefs_do_not_mutate_belief_ledger():
    with tempfile.TemporaryDirectory() as d:
        agent = CharacterAgent(cartridge_path=str(CART), user_id="ledger_contract", db_path=os.path.join(d, "state.db"))
        before = dict(agent.engine.belief_ledger.values)
        agent.say("Fine.", visible_context={"user_text": "Fine."})
        agent.dream(min_interval_seconds=0)
        after = dict(agent.engine.belief_ledger.values)
    assert after == before


def test_renderer_output_remains_noncanonical():
    with tempfile.TemporaryDirectory() as d:
        agent = CharacterAgent(cartridge_path=str(CART), user_id="renderer_contract", db_path=os.path.join(d, "state.db"))
        agent.say("Hello.")
        events = agent.engine.persistence.load_events_since(agent.engine.identity.name, "renderer_contract", 0, event_type="speech")
    assert events[-1]["payload"]["response_is_canonical_truth"] is False


def test_anchored_misread_simulator_script_exists():
    assert (ROOT / "simulator_scripts" / "interpretation_anchored_misread.yaml").exists()


def test_anchored_misread_simulator_runs():
    script = ROOT / "simulator_scripts" / "interpretation_anchored_misread.yaml"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "simulator.py"),
            "--script",
            str(script),
            "--cartridge",
            str(CART),
        ],
        cwd=str(ROOT.parent),
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
