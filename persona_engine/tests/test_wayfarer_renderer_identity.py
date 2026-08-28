"""Wayfarer tests for renderer/identity separation.

The portable character may describe who the individual is, but it may not select
which model executes or renders the character. Renderer choice belongs to the
host/session layer.
"""

from dataclasses import asdict, fields
from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.cartridge import load_cartridge
from persona_engine.core.identity import CoreIdentity


ROOT = Path(__file__).resolve().parents[1]
NEUTRAL = ROOT / "cartridges" / "neutral.snp"


def _without_model_name(text: str) -> str:
    return "\n".join(
        line for line in text.splitlines()
        if not line.strip().startswith("model_name =")
    ) + "\n"


def test_v1_cartridge_without_identity_model_name_loads(tmp_path):
    source = NEUTRAL.read_text(encoding="utf-8")
    path = tmp_path / "no_model.snp"
    path.write_text(_without_model_name(source), encoding="utf-8")

    identity, ledger, raw = load_cartridge(str(path))

    assert identity.name == "Neutral"
    assert ledger.immutable.name == "Neutral"
    assert raw["migration_warnings"] == []


def test_legacy_identity_model_name_is_accepted_but_ignored(tmp_path):
    source = NEUTRAL.read_text(encoding="utf-8")
    if 'model_name = "missing-model-for-mock"' in source:
        source = source.replace(
            'model_name = "missing-model-for-mock"',
            'model_name = "peer-controlled-model-must-not-win"',
        )
    else:
        source = source.replace(
            "prohibited_mutations =",
            'model_name = "peer-controlled-model-must-not-win"\nprohibited_mutations =',
            1,
        )
    path = tmp_path / "legacy_model.snp"
    path.write_text(source, encoding="utf-8")

    identity, _, raw = load_cartridge(str(path))

    # During the v1 compatibility window attribute access returns only the
    # compatibility default. The caller/cartridge-supplied value is discarded.
    assert identity.model_name == "missing-model-for-mock"
    assert raw["migration_warnings"]
    assert "ignored by Wayfarer" in raw["migration_warnings"][0]


def test_model_name_is_not_stored_identity_state():
    identity = CoreIdentity(
        name="Portable",
        core_beliefs=("I persist",),
        temperament="steady",
        model_name="should-not-become-identity",
    )

    assert "model_name" not in {item.name for item in fields(identity)}
    assert "model_name" not in asdict(identity)
    assert "should-not-become-identity" not in repr(identity)


def test_legacy_model_name_does_not_change_identity_equality():
    first = CoreIdentity(
        name="Portable",
        core_beliefs=("I persist",),
        temperament="steady",
        model_name="model-a",
    )
    second = CoreIdentity(
        name="Portable",
        core_beliefs=("I persist",),
        temperament="steady",
        model_name="model-b",
    )

    assert first == second


def test_cartridge_cannot_select_runtime_renderer(tmp_path):
    source = NEUTRAL.read_text(encoding="utf-8")
    source = source.replace(
        'model_name = "missing-model-for-mock"',
        'model_name = "some-cloud-model"',
    )
    path = tmp_path / "cloud_hint.snp"
    path.write_text(source, encoding="utf-8")

    agent = CharacterAgent(
        cartridge_path=str(path),
        user_id="renderer_authority",
        db_path=str(tmp_path / "state.db"),
    )
    status = agent.engine.renderer_status()

    assert status["requested_provider"] == "offline"
    assert status["actual_provider"] == "offline"
    assert status["model_name"] == "missing-model-for-mock"


def test_engine_bootstrap_does_not_read_identity_model_name(tmp_path, monkeypatch):
    identity = CoreIdentity(
        name="NoRendererInIdentity",
        core_beliefs=("I persist across renderers",),
        temperament="steady",
        model_name="legacy-value-must-not-be-read",
    )

    # The compatibility InitVar is not stored on the instance. Removing
    # its class default makes any accidental engine read fail immediately.
    monkeypatch.delattr(CoreIdentity, "model_name", raising=False)
    agent = CharacterAgent(
        identity,
        user_id="no_identity_renderer_read",
        db_path=str(tmp_path / "state.db"),
    )

    status = agent.engine.renderer_status()
    assert status["requested_provider"] == "offline"
    assert status["actual_provider"] == "offline"
    assert status["model_name"] == "missing-model-for-mock"


def test_host_can_replace_renderer_without_changing_identity(tmp_path):
    agent = CharacterAgent(
        cartridge_path=str(NEUTRAL),
        user_id="host_renderer",
        db_path=str(tmp_path / "state.db"),
    )
    before_name = agent.engine.identity.name
    before_beliefs = agent.engine.identity.core_beliefs

    class HostRenderer:
        def runtime_status(self):
            return {
                "requested_provider": "custom",
                "actual_provider": "custom",
                "model_name": "host-test-renderer",
            }

        def generate_expression(self, request):
            return "Renderer changed; identity did not."

        def generate_private_cognition(self, request):
            from persona_engine.core.cognition_schemas import PrivateCognitionProposal
            from persona_engine.core.renderer_contract import PrivateCognitionResult
            return PrivateCognitionResult(PrivateCognitionProposal(
                prose="",
                attention_targets=[],
                pressure_deltas={},
                impulse_candidates=[],
                memory_activation_requests=[],
                cognitive_theme_ids=[],
            ))

    agent.engine.set_renderer(HostRenderer())

    assert agent.engine.identity.name == before_name
    assert agent.engine.identity.core_beliefs == before_beliefs
    assert agent.engine.renderer_status()["model_name"] == "host-test-renderer"
