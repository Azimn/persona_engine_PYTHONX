"""Tests for immutable cartridge loading."""

from pathlib import Path
import pytest

from persona_engine.core.cartridge import CartridgeError, load_cartridge

ROOT = Path(__file__).resolve().parents[1]


def test_load_neutral_cartridge():
    core, ledger, raw = load_cartridge(str(ROOT / "cartridges" / "neutral.snp"))
    assert core.name == "Neutral"
    assert ledger.immutable.name == "Neutral"
    assert raw["beliefs"][0]["id"] == "user_trustworthiness"


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
    with pytest.raises(CartridgeError, match="beliefs"):
        load_cartridge(str(bad))
