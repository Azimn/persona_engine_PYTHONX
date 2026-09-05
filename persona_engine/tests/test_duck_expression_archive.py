from persona_engine.duck.expression import ExpressionResult
from persona_engine.duck.future_runtime import FutureDuckRuntime
from persona_engine.duck.persistence import DuckPersistence
from persona_engine.duck.text_body import TextChannelEmbodimentPort
from persona_engine.duck.types import CandidateAction


class ArchiveSubject:
    subject_id = "expression-archive-subject"

    def __init__(self):
        self.elapsed = 0.0
        self.receipts = []

    def snapshot(self):
        return {"subject_id": self.subject_id, "relationship": {"stance": "trusted"}}

    def observe_event(self, payload):
        del payload
        return None

    def advance_time(self, elapsed_seconds):
        self.elapsed += float(elapsed_seconds)
        return {"elapsed": self.elapsed}

    def record_delivery_receipt(self, receipt):
        self.receipts.append(dict(receipt))
        return {"recorded": True}


class TickExpressionPort:
    def __init__(self, prefix="rendered"):
        self.prefix = prefix
        self.calls = 0

    def realize(self, context):
        self.calls += 1
        return ExpressionResult(
            f"{self.prefix}-{context.tick}",
            "test",
            self.prefix,
            seed=context.tick + 100,
        )


def test_evicted_expression_replays_from_append_only_trace_after_restart(tmp_path):
    persistence = DuckPersistence(tmp_path)
    subject = ArchiveSubject()
    body = TextChannelEmbodimentPort()
    port = TickExpressionPort()
    runtime = FutureDuckRuntime(
        subject,
        embodiment=body,
        expression_port=port,
        persistence=persistence,
        organism_id="archive-organism",
    )
    runtime.expression_journal.max_rows = 2

    first_trace = None
    first_speech_id = None
    first_text = None
    for index in range(4):
        runtime.ingest_user_message(f"message {index}", event_id=f"u:{index}")
        trace = runtime.step()
        assert trace is not None
        if first_trace is None:
            first_trace = trace
            metadata = trace.outcome["execution"]["metadata"]
            first_speech_id = metadata["speech_id"]
            first_text = metadata["expression"]["text"]

    assert port.calls == 4
    assert len(runtime.expression_journal.rows) == 2
    assert first_speech_id not in runtime.expression_journal.rows
    assert persistence.find_expression(first_speech_id)["text"] == first_text

    restarted_subject = ArchiveSubject()
    blocked_port = TickExpressionPort("should-not-run")
    restarted = FutureDuckRuntime(
        restarted_subject,
        embodiment=TextChannelEmbodimentPort(),
        expression_port=blocked_port,
        persistence=persistence,
        state=persistence.load(),
    )
    assert len(restarted.expression_journal.rows) == 2
    assert first_speech_id not in restarted.expression_journal.rows

    action = CandidateAction(**first_trace.selected_intention["action"])
    context = {
        "tick": first_trace.tick,
        "subject_id": restarted_subject.subject_id,
        "trigger": first_trace.trigger,
        "situation": restarted.organism.current_state().situation.to_dict(),
        "subject": restarted_subject.snapshot(),
        "broadcast": first_trace.broadcast,
    }
    prepared, metadata = restarted.expression_preparer.prepare(action, context)

    assert prepared.parameters["utterance"] == first_text
    assert metadata["expression_replayed"] is True
    assert blocked_port.calls == 0
    assert first_speech_id in restarted.expression_journal.rows
    assert len(restarted.expression_journal.rows) == 2
