"""M4 linear subject-time and replay contracts."""

from pathlib import Path
import os
import tempfile

from persona_engine.agent import CharacterAgent
from persona_engine.core.continuity_clock import ContinuityClock
from persona_engine.core.replay import replay_from_continuity_bundle, semantic_digest

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "cartridges" / "pretorius.snp"


def test_clock_preserves_full_elapsed_time_and_never_runs_backward():
    clock = ContinuityClock(last_wall_time=1000.0)
    forward = clock.observe_wall(1000.0 + 8 * 60 * 60)
    assert forward.elapsed_seconds == 8 * 60 * 60
    assert clock.subject_elapsed_seconds == 8 * 60 * 60

    backward = clock.observe_wall(900.0)
    assert backward.elapsed_seconds == 0.0
    assert backward.backward_correction_seconds > 0.0
    assert clock.subject_elapsed_seconds == 8 * 60 * 60
    assert clock.correction_count == 1


def test_explicit_time_advance_persists_and_is_canonical():
    with tempfile.TemporaryDirectory() as d:
        db = os.path.join(d, "state.db")
        agent = CharacterAgent(cartridge_path=str(CART), user_id="clock", db_path=db)
        result = agent.advance_time(8 * 60 * 60, source="test")
        assert result["elapsed_seconds"] == 8 * 60 * 60
        assert result["subject_elapsed_seconds"] >= 8 * 60 * 60
        # Old body/pressure coefficients are not granted eight hours of fake
        # scientific meaning. Their compatibility integration remains bounded.
        assert result["dynamics_seconds"] == 1000.0

        restarted = CharacterAgent(cartridge_path=str(CART), user_id="clock", db_path=db)
        assert restarted.engine.clock.subject_elapsed_seconds >= 8 * 60 * 60
        bundle = restarted.engine.persistence.export_continuity_tail(restarted.engine.identity.name, restarted.engine.user_id)
        time_events = [event for event in bundle["events"] if event["event_type"] == "time_advance"]
        assert time_events
        assert time_events[-1]["payload"]["elapsed_seconds"] == 8 * 60 * 60


def test_time_advance_is_a_replayable_root():
    with tempfile.TemporaryDirectory() as d:
        source = CharacterAgent(cartridge_path=str(CART), user_id="time_replay", db_path=os.path.join(d, "source.db"))
        source.advance_time(3600.0, source="test")
        bundle = source.engine.persistence.export_continuity_tail(source.engine.identity.name, source.engine.user_id)
        result = replay_from_continuity_bundle(str(CART), bundle, user_id="time_replay")
        assert result.complete is True
        assert result.root_events_replayed == 1
        assert result.semantic_digest == semantic_digest(source)


def test_subject_clock_follows_one_subject_across_interlocutors():
    with tempfile.TemporaryDirectory() as d:
        db = os.path.join(d, "shared.db")
        alice = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)
        alice.advance_time(8 * 60 * 60, source="subject_clock_test")
        alice_elapsed = alice.engine.clock.subject_elapsed_seconds
        alice_subject = alice.engine.persistence._resolve_subject(alice.engine.identity.name, "alice")[0]

        bob = CharacterAgent(cartridge_path=str(CART), user_id="bob", db_path=db)
        bob_subject = bob.engine.persistence._resolve_subject(bob.engine.identity.name, "bob")[0]
        assert bob_subject == alice_subject
        assert bob.engine.clock.subject_elapsed_seconds == alice_elapsed

        bob.advance_time(60 * 60, source="subject_clock_test")
        bob_elapsed = bob.engine.clock.subject_elapsed_seconds
        assert bob_elapsed == alice_elapsed + 60 * 60

        alice_again = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)
        assert alice_again.engine.clock.subject_elapsed_seconds == bob_elapsed

        events = alice_again.engine.persistence.load_subject_continuity_events(
            alice_again.engine.identity.name,
            alice_again.engine.user_id,
            event_type="time_advance",
        )
        assert [event["payload"]["subject_elapsed_seconds"] for event in events] == [
            alice_elapsed,
            bob_elapsed,
        ]


def test_clock_snapshot_uses_canonical_microsecond_precision():
    clock = ContinuityClock(
        subject_elapsed_seconds=60.00401997566223,
        last_wall_time=1234.5,
        timezone_name="unknown",
        correction_count=0,
    )
    snapshot = clock.to_dict()
    assert snapshot["subject_elapsed_seconds"] == 60.00402
    assert ContinuityClock.from_dict(snapshot).to_dict() == snapshot
