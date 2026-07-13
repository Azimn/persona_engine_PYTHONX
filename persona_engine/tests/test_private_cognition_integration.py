import os
import tempfile

from persona_engine.agent import CharacterAgent
from persona_engine.core.cognition_schemas import PrivateCognitionProposal


class SuspicionRenderer:
    def generate_private_cognition(self, state_packet, cartridge):
        return PrivateCognitionProposal(
            prose="untrusted",
            attention_targets=[],
            pressure_deltas={"suspicion": 0.10},
            impulse_candidates=[],
            memory_activation_requests=[],
            cognitive_theme_ids=[],
        )

    def generate(self, messages, max_chars=200, retrieved_memories=None, seed=None):
        return "I hear you. I will stay with what is actually present."


def test_same_turn_private_cognition_influences_decision():
    with tempfile.TemporaryDirectory() as d:
        agent = CharacterAgent(
            cartridge_path=os.path.join(os.path.dirname(__file__), "..", "cartridges", "neutral.snp"),
            user_id="same_turn",
            db_path=os.path.join(d, "state.db"),
        )
        agent.engine.renderer = SuspicionRenderer()
        agent.add_pressure("suspicion", 0.55)
        result = agent.say("Fine.")
    assert result["cognitive_application_report"]["applied_pressure_deltas"]["suspicion"] == 0.10
    assert result["decision_payload"]["suspicion"] == 0.65
    assert result["decision_payload"]["dialogue_act"] == "challenge"


def test_private_cognition_report_persisted_without_raw_prose():
    with tempfile.TemporaryDirectory() as d:
        agent = CharacterAgent(
            cartridge_path=os.path.join(os.path.dirname(__file__), "..", "cartridges", "neutral.snp"),
            user_id="cog_report",
            db_path=os.path.join(d, "state.db"),
        )
        agent.engine.renderer = SuspicionRenderer()
        agent.say("Hello.")
        events = agent.engine.persistence.load_events_since(agent.engine.identity.name, "cog_report", 0, event_type="private_cognition")
    assert events
    payload = events[-1]["payload"]
    assert payload["raw_proposal_persisted"] is False
    assert "application_report" in payload
    assert "untrusted" not in str(payload)
