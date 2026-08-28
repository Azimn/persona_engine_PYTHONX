"""Engine integration tests for permanent subject binding and checkpoints."""

import os
import tempfile
from pathlib import Path

from persona_engine.agent import CharacterAgent

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "cartridges" / "pretorius.snp"


def test_engine_continuity_events_use_portable_entity_uuid():
    with tempfile.TemporaryDirectory() as d:
        agent = CharacterAgent(cartridge_path=str(CART), user_id="continuity_user", db_path=os.path.join(d, "state.db"))
        assert agent.engine.identity.entity_uuid
        agent.say("Hello.")
        events = agent.engine.persistence.load_continuity_events(agent.engine.identity.name, agent.engine.user_id)
        assert events
        assert {event["subject_uuid"] for event in events} == {agent.engine.identity.entity_uuid}
        assert [event["sequence"] for event in events] == list(range(1, len(events) + 1))


def test_engine_persist_records_checkpoint_at_latest_canonical_sequence():
    with tempfile.TemporaryDirectory() as d:
        agent = CharacterAgent(cartridge_path=str(CART), user_id="checkpoint_user", db_path=os.path.join(d, "state.db"))
        agent.say("Hello.")
        checkpoint = agent.engine.persistence.latest_checkpoint(agent.engine.identity.name, agent.engine.user_id)
        events = agent.engine.persistence.load_continuity_events(agent.engine.identity.name, agent.engine.user_id)
        assert checkpoint is not None
        assert checkpoint["subject_uuid"] == agent.engine.identity.entity_uuid
        assert checkpoint["sequence"] == events[-1]["sequence"]
        assert len(checkpoint["state_digest"]) == 64
