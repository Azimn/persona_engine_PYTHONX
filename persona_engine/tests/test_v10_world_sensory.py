"""v10 tests for world authority and sensory plumbing."""

import tempfile
from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.audio_sensor import AudioObservation, MockAudioSensor, MicrophoneAdapter
from persona_engine.core.avatar import AvatarProjector, AvatarProfile
from persona_engine.core.event_classifier import EventClassifier, can_promote_to_canonical_memory
from persona_engine.core.vision_sensor import VisionObservation
from persona_engine.core.voice import VoicePlanner, VoiceProfile, MockTTSAdapter
from persona_engine.core.world_authority import WorldAuthority, WorldActionProposal

ROOT = Path(__file__).resolve().parents[1]
CARTRIDGE = ROOT / "cartridges" / "pretorius.snp"


def _agent(tmpdir):
    return CharacterAgent(cartridge_path=str(CARTRIDGE), db_path=str(Path(tmpdir) / "state.db"), user_id="tester")


def test_world_authority_owns_fact_mutation():
    authority = WorldAuthority()
    resolution = authority.apply_sensor_event("audio", {"sound_level": "high"}, confidence=0.8)
    assert resolution.accepted
    assert authority.get_visible_context()["audio_sound_level"] == "high"
    hidden = authority.apply_host_event({"hidden_note": "not for character"}, source="debug", visible=False)
    assert hidden.accepted
    assert "hidden_note" in authority.get_server_truth()
    assert "hidden_note" not in authority.get_visible_context()


def test_character_action_is_proposal_not_fact_until_resolved():
    authority = WorldAuthority()
    proposal = WorldActionProposal("actor", "set_attention", {"target": "hallway"}, 1.0)
    assert "attention_target" not in authority.get_server_truth()
    resolution = authority.resolve_action(proposal)
    assert resolution.accepted
    assert authority.get_visible_context()["attention_target"] == "hallway"


def test_audio_sensor_does_not_mutate_pressure():
    with tempfile.TemporaryDirectory() as d:
        agent = _agent(d)
        agent.add_pressure("fear", 0.2)
        before = dict(agent.engine.debug_snapshot()["pressures"])
        result = agent.observe_audio(AudioObservation(sound_level="high", sudden_onset=True, confidence=0.9))
        after = dict(agent.engine.debug_snapshot()["pressures"])
        assert result["pressure_unchanged"]
        assert before == after
        assert result["facts"]


def test_vision_sensor_does_not_mutate_relationship():
    with tempfile.TemporaryDirectory() as d:
        agent = _agent(d)
        before = dict(agent.engine.relationship.__dict__)
        result = agent.observe_vision(VisionObservation(face_present=True, user_presence="present", movement_detected=True))
        after = dict(agent.engine.relationship.__dict__)
        assert result["relationship_unchanged"]
        assert before == after
        assert result["facts"]


def test_voice_plan_uses_expression_envelope_and_tts_mock():
    with tempfile.TemporaryDirectory() as d:
        agent = _agent(d)
        result = agent.say("Hello.")
        plan = result["voice_plan"]
        assert plan["text"] == result["response"]
        assert plan["rate_bucket"] in {"slow", "normal", "fluid", "fast"}
        tts = MockTTSAdapter()
        from persona_engine.core.voice import VoicePlan
        spoken = tts.speak(VoicePlan(**plan))
        assert spoken["spoken"] is True


def test_avatar_projection_uses_public_state_only():
    projector = AvatarProjector(AvatarProfile(default_face="neutral", guarded_face="guarded"))
    state = projector.project({"avatar_state": "guarded", "attention": "user", "posture": "seated", "movement_need": "low"})
    assert state.face_state == "guarded"
    assert state.gaze_state == "toward_user"


def test_event_classifier_memory_firewall():
    classifier = EventClassifier()
    speech = classifier.classify("speech", {"response": "I said something", "response_is_canonical_truth": False})
    belief = classifier.classify("belief", {"text": "The silence feels guarded."})
    assert not speech.canonical_truth
    assert speech.memory_type == "speech"
    # Wayfarer contract: a subjective belief may be important state without
    # automatically becoming canonical memory truth. Slow belief changes are
    # owned by the governed belief/consolidation path.
    assert not belief.canonical_truth
    assert belief.memory_type == "interpretive"
    assert can_promote_to_canonical_memory("voice_plan", {}) is False


def test_mock_audio_and_microphone_adapter_contract():
    sensor = MockAudioSensor([AudioObservation(sound_level="moderate")])
    assert sensor.poll().sound_level == "moderate"
    try:
        MicrophoneAdapter().poll()
    except RuntimeError as exc:
        assert "No microphone backend" in str(exc)
    else:
        raise AssertionError("MicrophoneAdapter must not pretend to be configured")
