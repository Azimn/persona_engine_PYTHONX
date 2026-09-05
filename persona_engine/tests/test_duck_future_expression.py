from persona_engine.duck.expression import ExpressionResult
from persona_engine.duck.future_runtime import FutureDuckRuntime
from persona_engine.duck.persistence import DuckPersistence
from persona_engine.duck.text_body import TextChannelEmbodimentPort


class ReceiptSubject:
    subject_id = "expression-subject"

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


class StaticExpressionPort:
    def __init__(self, text, model="static-a"):
        self.text = text
        self.model = model
        self.calls = 0

    def realize(self, context):
        self.calls += 1
        return ExpressionResult(self.text, "test", self.model, seed=context.tick + 10)


def test_user_message_becomes_selected_communication_and_delivery_receipt():
    subject = ReceiptSubject()
    body = TextChannelEmbodimentPort()
    expression = StaticExpressionPort("Hello from the selected intention.")
    runtime = FutureDuckRuntime(subject, embodiment=body, expression_port=expression)
    runtime.ingest_user_message("Hello?", event_id="user:1")
    trace = runtime.step()
    assert trace is not None
    assert trace.selected_intention["action"]["action_type"] == "communicate"
    execution = trace.outcome["execution"]
    assert execution["executed"] is True
    assert execution["metadata"]["expression"]["text"] == "Hello from the selected intention."
    assert body.latest_output()["text"] == "Hello from the selected intention."
    assert subject.receipts[-1]["status"] == "delivered"
    assert runtime.latest_expression()["model"] == "static-a"


def test_expression_model_swap_changes_surface_not_duck_canonical_state(tmp_path):
    def run(text, root):
        subject = ReceiptSubject()
        body = TextChannelEmbodimentPort()
        persistence = DuckPersistence(root)
        runtime = FutureDuckRuntime(subject, embodiment=body, expression_port=StaticExpressionPort(text), persistence=persistence, organism_id="stable-organism")
        runtime.ingest_user_message("Same input", event_id="same-event")
        trace = runtime.step()
        return DuckPersistence.digest_state(runtime.organism.current_state()), trace.outcome["execution"]["metadata"]["expression"]["text"]

    digest_a, text_a = run("Surface A", tmp_path / "a")
    digest_b, text_b = run("Surface B", tmp_path / "b")
    assert text_a != text_b
    assert digest_a == digest_b


def test_recorded_expression_is_reused_without_recalling_renderer(tmp_path):
    subject = ReceiptSubject()
    body = TextChannelEmbodimentPort()
    persistence = DuckPersistence(tmp_path)
    first_port = StaticExpressionPort("Recorded words")
    runtime = FutureDuckRuntime(subject, embodiment=body, expression_port=first_port, persistence=persistence, organism_id="journal-organism")
    runtime.ingest_user_message("Hi", event_id="u1")
    first = runtime.step()
    speech_id = first.outcome["execution"]["metadata"]["speech_id"]
    assert first_port.calls == 1
    assert runtime.expression_journal.get(speech_id).text == "Recorded words"

    second_port = StaticExpressionPort("Should not be used")
    runtime.set_expression_port(second_port)
    action = runtime.organism.current_state().current_intention.action
    context = {
        "tick": first.tick,
        "subject_id": subject.subject_id,
        "trigger": first.trigger,
        "situation": runtime.organism.current_state().situation.to_dict(),
        "subject": subject.snapshot(),
        "broadcast": first.broadcast,
    }
    prepared, metadata = runtime.expression_preparer.prepare(action, context)
    assert prepared.parameters["utterance"] == "Recorded words"
    assert metadata["expression_replayed"] is True
    assert second_port.calls == 0
