"""Narrow LLM cognitive-service adapters for DUCK.

An LLM response is a proposal artifact. It is never a canonical write, action,
identity update, memory fact, or privileged instruction merely because it is
fluent. The adapter accepts only a bounded JSON contract and emits ordinary
noncanonical CognitiveItems for workspace competition.
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Callable
from urllib.request import Request, urlopen

from .services import ServiceContext
from .types import CognitiveItem, clamp


DUCK_LLM_PROPOSAL_SCHEMA = "duck-llm-proposals-v1"
_ALLOWED_KINDS = {
    "interpretation_hypothesis",
    "action_hypothesis",
    "simulation_hypothesis",
    "memory_abstraction",
    "question_hypothesis",
}


def _default_transport(url: str, payload: dict, timeout: float) -> dict:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


class OllamaJsonCognitiveService:
    service_name = "ollama-json-cognitive-service"

    def __init__(
        self,
        model_name: str,
        *,
        purpose: str = "interpretation_and_action_proposals",
        host: str = "http://localhost:11434",
        timeout_seconds: float = 30.0,
        seed: int = 0,
        temperature: float = 0.2,
        max_items: int = 4,
        transport: Callable[[str, dict, float], dict] | None = None,
        template_version: str = "duck-cognitive-json-v1",
    ):
        self.model_name = str(model_name)
        self.purpose = str(purpose)
        self.host = host.rstrip("/")
        self.timeout_seconds = max(0.1, float(timeout_seconds))
        self.seed = int(seed)
        self.temperature = max(0.0, float(temperature))
        self.max_items = max(1, min(8, int(max_items)))
        self.transport = transport or _default_transport
        self.template_version = str(template_version)

    def _messages(self, context: ServiceContext) -> list[dict[str, str]]:
        instructions = {
            "schema": DUCK_LLM_PROPOSAL_SCHEMA,
            "purpose": self.purpose,
            "rules": [
                "Return JSON only.",
                "You are a proposal service, not the organism or its authority.",
                "Do not assert that your proposal changes identity, memory, relationships, goals, drives, world truth, or action state.",
                "Use only evidence in the provided bounded projection.",
                "Uncertain interpretations must remain hypotheses.",
                "At most %d items." % self.max_items,
            ],
            "output": {
                "items": [{
                    "kind": "one of: " + ", ".join(sorted(_ALLOWED_KINDS)),
                    "payload": "JSON object. action_hypothesis may contain action_candidates list using the DUCK CandidateAction-shaped fields.",
                    "confidence": "0..1",
                    "salience": "0..1",
                    "self_relevance": "0..1",
                    "novelty": "0..1",
                    "threat": "0..1",
                    "valence": "-1..1",
                    "arousal": "0..1",
                }],
            },
        }
        return [
            {"role": "system", "content": json.dumps(instructions, sort_keys=True)},
            {"role": "user", "content": json.dumps(context.projection, sort_keys=True, default=str)},
        ]

    def propose(self, context: ServiceContext) -> list[CognitiveItem]:
        request_payload = {
            "model": self.model_name,
            "messages": self._messages(context),
            "stream": False,
            "format": "json",
            "options": {"seed": self.seed + context.tick, "temperature": self.temperature},
        }
        started = time.time()
        response = self.transport(f"{self.host}/api/chat", request_payload, self.timeout_seconds)
        message = response.get("message", {}) if isinstance(response, dict) else {}
        raw_content = message.get("content", "") if isinstance(message, dict) else ""
        if not isinstance(raw_content, str) or not raw_content.strip():
            raise ValueError("Ollama response did not contain message.content")
        parsed = json.loads(raw_content)
        if not isinstance(parsed, dict) or not isinstance(parsed.get("items", []), list):
            raise ValueError("LLM proposal response does not match duck-llm-proposals-v1")
        response_hash = hashlib.sha256(raw_content.encode("utf-8")).hexdigest()
        duration_ms = round((time.time() - started) * 1000.0, 3)
        items: list[CognitiveItem] = []
        for index, raw in enumerate(parsed.get("items", [])[: self.max_items]):
            if not isinstance(raw, dict):
                continue
            kind = str(raw.get("kind", ""))
            if kind not in _ALLOWED_KINDS:
                continue
            payload = raw.get("payload", {})
            if not isinstance(payload, dict):
                continue
            items.append(CognitiveItem(
                item_id=f"llm:{self.model_name}:{context.tick}:{index}",
                tick=context.tick,
                kind=kind,
                source_module="llm_service",
                subject_id=context.subject_id,
                payload=dict(payload),
                confidence=clamp(raw.get("confidence", 0.5)),
                salience=clamp(raw.get("salience", 0.4)),
                self_relevance=clamp(raw.get("self_relevance", 0.3)),
                novelty=clamp(raw.get("novelty", 0.3)),
                threat=clamp(raw.get("threat", 0.0)),
                valence=max(-1.0, min(1.0, float(raw.get("valence", 0.0) or 0.0))),
                arousal=clamp(raw.get("arousal", 0.0)),
                provenance={
                    "authority": "proposal_only",
                    "provider": "ollama",
                    "model": self.model_name,
                    "service": self.service_name,
                    "purpose": self.purpose,
                    "template_version": self.template_version,
                    "schema": DUCK_LLM_PROPOSAL_SCHEMA,
                    "schema_valid": True,
                    "response_sha256": response_hash,
                    "duration_ms": duration_ms,
                    "recorded_at": started,
                },
                canonical=False,
            ))
        return items
