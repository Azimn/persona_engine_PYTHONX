"""v10 cartridge profile tests."""

from pathlib import Path
from persona_engine.core.cartridge import load_cartridge

ROOT = Path(__file__).resolve().parents[1]


def test_v10_optional_profiles_load_from_cartridge():
    core, ledger, raw = load_cartridge(str(ROOT / "cartridges" / "pretorius.snp"))
    assert raw["sensory_profile"]["audio_sensitivity"] == 0.65
    assert raw["voice_profile"]["default_rate"] == "slow"
    assert raw["avatar_profile"]["guarded_face"] == "guarded"
    assert core.name == "Pretorius"
