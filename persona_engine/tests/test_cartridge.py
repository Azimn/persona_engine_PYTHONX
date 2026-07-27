"""Tests for immutable cartridge loading."""

from pathlib import Path
import tomllib

import pytest

from persona_engine.core.cartridge import CartridgeError, load_cartridge, validate_cartridge_data
from persona_engine.core.offline_dialogue import clear_dialogue_registry, dialogue_for

ROOT = Path(__file__).resolve().parents[1]


def setup_function():
    clear_dialogue_registry()


def test_load_neutral_cartridge():
    core, ledger, raw = load_cartridge(str(ROOT / "cartridges" / "neutral.snp"))
    assert core.name == "Neutral"
    assert ledger.immutable.name == "Neutral"
    assert raw["beliefs"][0]["id"] == "user_trustworthiness"
    assert raw["dialogue"] == {}


def test_load_pretorius_registers_authored_dialogue():
    core, _, raw = load_cartridge(str(ROOT / "cartridges" / "pretorius.snp"))
    assert raw["dialogue"]["greeting"]
    assert dialogue_for(core.name)["identity_boundary"] == raw["dialogue"]["identity_boundary"]


def test_missing_required_section(tmp_path):
    bad = tmp_path / "bad.snp"
    bad.write_text('[metadata]\nentity_id="x"\nentity_name="X"\nschema_version="1"\n')
    with pytest.raises(CartridgeError, match="identity"):
        load_cartridge(str(bad))


def test_malformed_belief_array(tmp_path):
    bad = tmp_path / "bad.snp"
    bad.write_text('''
[metadata]
entity_id="x"
entity_name="X"
schema_version="1"
[identity]
core_beliefs=["a"]
temperament="even"
moral_boundaries=[]
speech_constraints=[]
prohibited_mutations=[]
model_name="mock"
[voice]
forbidden_lexicon=[]
speaking_style="plain"
address_user_as="you"
beliefs="not an array"
[[belief_rules]]
belief_id="x"
trigger_memory_type="turn"
threshold_count=1
delta=0.1
''')
    with pytest.raises(CartridgeError):
        load_cartridge(str(bad))


def _neutral_data() -> dict:
    with open(ROOT / "cartridges" / "neutral.snp", "rb") as handle:
        return tomllib.load(handle)


def test_dialogue_rejects_unknown_group():
    data = _neutral_data()
    data["dialogue"] = {"pretorius_only": ["This must not enter the engine."]}
    with pytest.raises(CartridgeError, match="unknown field"):
        validate_cartridge_data(data)


def test_dialogue_rejects_unknown_slot():
    data = _neutral_data()
    data["dialogue"] = {"greeting": ["Hello {invented_state}."]}
    with pytest.raises(CartridgeError, match="unsupported dialogue slot"):
        validate_cartridge_data(data)


def test_dialogue_requires_nonempty_string_lists():
    data = _neutral_data()
    data["dialogue"] = {"greeting": []}
    with pytest.raises(CartridgeError, match="non-empty list of strings"):
        validate_cartridge_data(data)
