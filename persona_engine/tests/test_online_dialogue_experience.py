"""Online realization stays character-owned while sharing portable continuity."""

import json
from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.offline_conversation import classify_input
from persona_engine.core.renderer import LocalLLMRenderer


ROOT = Path(__file__).resolve().parents[1]
KIKI = ROOT / "cartridges" / "kiki.snp"
PRETORIUS = ROOT / "cartridges" / "pretorius.snp"
END_TIME = 1_800_000_000.0


class _Response:
    def __init__(self, text: str):
        self.text = text

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps({"message": {"content": self.text}}).encode("utf-8")


def test_imperative_questions_create_answer_obligations():
    assert classify_input("Explain why Newtonian gravity fails near a black hole.") == "ask_analysis"
    assert classify_input("Describe the body you would choose.") == "ask_fact"
    assert classify_input("I do not agree that creation excuses manipulation.") == "challenge"
    assert classify_input("Return to your work. I am leaving.") == "leave_or_return"
    assert classify_input("Keep this for our next conversation: what survives replacement?") == "request_action"


def test_online_prompt_uses_authored_voice_without_forbidding_artificial_identity(tmp_path):
    captured = {}

    def opener(request, timeout):
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return _Response("Gold, articulate, and conspicuously artificial. Subtlety is not the assignment.")

    agent = CharacterAgent(
        cartridge_path=str(KIKI),
        user_id="jay",
        db_path=str(tmp_path / "kiki-online.db"),
    )
    agent.engine.set_renderer(LocalLLMRenderer(
        model_name="fake",
        provider="ollama",
        thinking_mode="off",
        opener=opener,
    ))

    result = agent.say(
        "Describe the body you would choose if engineering were no obstacle.",
        visible_context={"speaker_id": "jay", "speaker_name": "Jay"},
    )
    prompt = captured["payload"]["messages"][0]["content"]

    assert result["action_decision"]["action_kind"] == "speak"
    assert result["model_calls"]["expression_renderer_called"] is True
    assert "AUTHORED CHARACTER EXAMPLES" in prompt
    assert "CURRENT INTERLOCUTOR: Jay" in prompt
    assert "do not append a generic offer, invitation, or follow-up question" in prompt
    assert "being an AI" not in prompt
    assert "having no feelings" in prompt


def test_online_retention_request_writes_journal_and_promises_followup(tmp_path):
    agent = CharacterAgent(
        cartridge_path=str(KIKI),
        user_id="jay",
        db_path=str(tmp_path / "kiki-note.db"),
    )
    agent.engine.set_renderer(LocalLLMRenderer(
        model_name="fake",
        provider="ollama",
        thinking_mode="off",
        opener=lambda *_args, **_kwargs: _Response(
            "That is worth keeping. I recorded the question without pretending I have finished it."
        ),
    ))

    result = agent.say(
        "Keep this question for next time: could memory reconsolidation resemble error correction?",
        visible_context={"speaker_id": "jay", "speaker_name": "Jay"},
    )
    promised = [
        item for item in agent.engine.intentions.open_loops
        if item.reason == "promised_followup"
    ]

    assert result["action_decision"]["action_kind"] == "world_action"
    assert result["action_decision"]["communicative_function"] == "defer_and_note"
    assert agent.engine.renderer_status()["actual_provider"] == "ollama"
    assert len(agent.engine.journal.entries) == 1
    assert len(promised) == 1
    assert promised[0].required_capability == "none"


def test_considered_memory_does_not_force_grounding_on_later_opinion(tmp_path):
    responses = iter([
        "I recognized Henry Frankenstein's appetite for forbidden creation and deliberately cultivated it.",
        "Creation does not excuse manipulation. It makes responsibility harder to evade.",
    ])
    agent = CharacterAgent(
        cartridge_path=str(PRETORIUS),
        user_id="jay",
        db_path=str(tmp_path / "pretorius-online.db"),
    )
    agent.replay_genesis(end_time=END_TIME)
    agent.engine.set_renderer(LocalLLMRenderer(
        model_name="fake",
        provider="ollama",
        thinking_mode="off",
        opener=lambda *_args, **_kwargs: _Response(next(responses)),
    ))

    first = agent.say(
        "Tell me what you remember about teaching Henry Frankenstein.",
        event_time=END_TIME + 1,
    )
    second = agent.say(
        "I do not agree that creation excuses manipulation.",
        event_time=END_TIME + 2,
    )

    assert first["conversation_candidate"]["source_memory_id"] is not None
    assert second["response"].startswith("Creation does not excuse")
    assert agent.engine.renderer_status()["actual_provider"] == "ollama"
