import json

from persona_engine.duck.llm_services import OllamaJsonCognitiveService
from persona_engine.duck.services import ServiceContext


def test_ollama_cognitive_service_parses_only_noncanonical_typed_proposals():
    captured = {}
    def transport(url, payload, timeout):
        captured.update({"url": url, "payload": payload, "timeout": timeout})
        return {"message": {"content": json.dumps({"items": [{
            "kind": "action_hypothesis",
            "payload": {"action_candidates": [{"action_type": "inspect", "action_id": "inspect"}]},
            "confidence": 0.7,
            "salience": 0.8,
            "self_relevance": 0.6,
        }]})}}

    service = OllamaJsonCognitiveService("qwen-test", transport=transport)
    items = service.propose(ServiceContext(2, "subject", "workspace_candidates", {"fact": "bounded"}))

    assert captured["url"].endswith("/api/chat")
    assert items[0].canonical is False
    assert items[0].subject_id == "subject"
    assert items[0].provenance["authority"] == "proposal_only"
    assert items[0].provenance["model"] == "qwen-test"
    assert items[0].payload["action_candidates"][0]["action_type"] == "inspect"


def test_invalid_llm_item_kind_is_not_promoted_into_workspace_candidate():
    def transport(url, payload, timeout):
        return {"message": {"content": json.dumps({"items": [{
            "kind": "canonical_identity_write",
            "payload": {"new_identity": "wrong"},
            "salience": 1.0,
        }]})}}
    service = OllamaJsonCognitiveService("bad", transport=transport)
    assert service.propose(ServiceContext(0, "subject", "workspace_candidates", {})) == []
