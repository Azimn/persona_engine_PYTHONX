"""Contracts for deterministic Tide idle drift."""

from __future__ import annotations

from pathlib import Path

from persona_engine.agent import CharacterAgent


ROOT = Path(__file__).resolve().parents[1]
PRET = ROOT / "cartridges" / "pretorius.snp"


def _agent(tmp_path, name="state.db"):
    return CharacterAgent(cartridge_path=str(PRET), user_id=name, db_path=str(tmp_path / name))


def _drift_projection(agent):
    body = agent.engine.body
    return {
        "engine_energy": round(agent.engine.energy, 6),
        "restlessness": round(agent.engine.restlessness, 6),
        "body_energy": round(body.energy, 6),
        "body_tension": round(body.tension, 6),
        "body_fatigue": round(body.fatigue, 6),
        "stillness_seconds": round(body.stillness_seconds, 6),
        "need_for_movement": round(body.need_for_movement, 6),
        "pressures": {name: round(p.magnitude, 6) for name, p in agent.engine.pressures.pressures.items()},
        "identity_name": agent.engine.identity.name,
    }


def test_run_idle_cycle_changes_tide_state_without_fresh_user_input(tmp_path):
    agent = _agent(tmp_path)
    agent.add_pressure("fear", 0.6)
    before = _drift_projection(agent)

    agent.engine.run_idle_cycle()

    after = _drift_projection(agent)
    assert after["engine_energy"] < before["engine_energy"]
    assert after["restlessness"] > before["restlessness"]
    assert after["body_fatigue"] > before["body_fatigue"]
    assert after["stillness_seconds"] > before["stillness_seconds"]


def test_idle_drift_is_deterministic_for_equivalent_state(tmp_path):
    first = _agent(tmp_path, "first.db")
    second = _agent(tmp_path, "second.db")
    first.add_pressure("fear", 0.6)
    second.add_pressure("fear", 0.6)

    first.engine.run_idle_cycle()
    second.engine.run_idle_cycle()

    assert _drift_projection(first) == _drift_projection(second)


def test_idle_drift_requires_no_renderer_or_external_capability(tmp_path):
    agent = _agent(tmp_path)
    agent.engine.renderer._client = None

    agent.engine.run_idle_cycle()

    assert agent.engine.timestep == 1
    assert agent.engine.body.stillness_seconds == 5.0


def test_idle_drift_does_not_rewrite_cartridge_identity(tmp_path):
    agent = _agent(tmp_path)
    before_name = agent.engine.identity.name
    before_beliefs = tuple(agent.engine.identity.core_beliefs)

    agent.engine.run_idle_cycle()

    assert agent.engine.identity.name == before_name
    assert tuple(agent.engine.identity.core_beliefs) == before_beliefs
