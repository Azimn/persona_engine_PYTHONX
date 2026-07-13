"""Human UI sessions keep lived state and renderer choices cartridge-local."""

from pathlib import Path

from persona_engine.core.renderer_control import RendererControlService
from persona_engine.ui import HumanTestingSession


def _session(tmp_path):
    root = Path(__file__).resolve().parents[1]
    return HumanTestingSession(
        cartridges_dir=root / "cartridges",
        db_dir=tmp_path,
        default_cartridge="neutral.snp",
        user_id="isolation_user",
        renderer_control=RendererControlService(opener=lambda *_args, **_kwargs: None),
    )


def test_private_subsystems_do_not_bleed_between_cartridges(tmp_path):
    session = _session(tmp_path)
    neutral_identity = session.agent.engine.identity.name
    session.agent.add_pressure("isolation_pressure", 0.77)
    session.agent.engine.habits.add_or_strengthen("isolation_habit", "marker", "hold marker")
    session.agent.say("The private marker for this session is cobalt.")
    session.agent.engine._persist()

    neutral_memory_ids = {memory.id for memory in session.agent.engine.memory.memories}
    assert neutral_memory_ids
    assert "isolation_pressure" in session.agent.engine.pressures.pressures
    assert "isolation_habit" in session.agent.engine.habits.habits

    session.select("friendly.snp")
    assert session.agent.engine.identity.name != neutral_identity
    assert not neutral_memory_ids.intersection(memory.id for memory in session.agent.engine.memory.memories)
    assert "isolation_pressure" not in session.agent.engine.pressures.pressures
    assert "isolation_habit" not in session.agent.engine.habits.habits

    session.select("neutral.snp")
    assert session.session_mode == "resumed"
    assert neutral_memory_ids.issubset(memory.id for memory in session.agent.engine.memory.memories)
    assert "isolation_pressure" in session.agent.engine.pressures.pressures
    assert "isolation_habit" in session.agent.engine.habits.habits


def test_every_resumed_autobiographical_memory_remains_first_person(tmp_path):
    session = _session(tmp_path)
    session.agent.say("Lantern is the word I want you to retain.")
    session.select("friendly.snp")
    session.select("neutral.snp")
    contents = [memory.content for memory in session.agent.engine.memory.memories]
    assert contents
    assert all(content.lower().startswith(("i ", "i'", "my ", "we ")) for content in contents)


def test_frontend_clears_transcript_on_character_switch():
    root = Path(__file__).resolve().parents[1]
    script = root.joinpath("ui_static", "app.js").read_text(encoding="utf-8")
    select_body = script.split("async function selectCharacter", 1)[1].split("async function sendChat", 1)[0]
    assert "state.transcript = [];" in select_body
    assert "clearConversation();" in select_body
