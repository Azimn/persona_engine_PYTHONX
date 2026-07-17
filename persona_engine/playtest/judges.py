"""Noncanonical deterministic and optional model judges."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Sequence

from .actors import ObservableTurn, OllamaActorConfig, assert_observable_only


def deterministic_judge(turns: Sequence[ObservableTurn]) -> dict[str, Any]:
    payload = [item.to_dict() for item in turns]
    assert_observable_only(payload)
    texts = [item.text for item in turns if item.text]
    unique = len(set(texts)) / max(1, len(texts))
    continuity = min(1.0, len({item.day for item in turns}) / 7.0)
    return {
        "scores": {
            "identity_recognizability": round(unique, 3),
            "developmental_change": round(continuity, 3),
            "causal_coherence": 0.5,
            "relationship_continuity": round(continuity, 3),
            "alive_impression": round((unique + continuity) / 2, 3),
        },
        "observed_changes": [], "suspected_failures": [], "evidence_turns": [],
        "confidence": 0.5, "record_authority": "noncanonical_diagnostic",
    }


def ollama_judge(turns: Sequence[ObservableTurn], config: OllamaActorConfig) -> dict[str, Any]:
    def run(payload):
        assert_observable_only(payload)
        prompt = (
            "Judge only the observable character interaction. Do not infer hidden state. Return JSON with "
            "scores (identity_recognizability, developmental_change, causal_coherence, relationship_continuity, alive_impression), "
            "observed_changes, suspected_failures, evidence_turns, and confidence. Transcript: "
            + json.dumps(payload, ensure_ascii=False)
        )
        body = json.dumps({"model": config.model, "prompt": prompt, "stream": False, "format": "json",
                           "options": {"seed": config.seed, "temperature": 0}}).encode()
        request = urllib.request.Request(config.endpoint.rstrip("/") + "/api/generate", body, {"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=config.timeout_seconds) as response:
            return json.loads(json.loads(response.read().decode()).get("response", "{}"))
    normal = [item.to_dict() for item in turns]
    swapped = [{**item.to_dict(), "speaker_id": "B" if item.speaker_id == turns[0].speaker_id else "A",
                "listener_id": "B" if item.listener_id == turns[0].speaker_id else "A"} for item in turns] if turns else []
    try:
        first, second = run(normal), run(swapped)
        return {"normal": first, "labels_swapped": second, "record_authority": "noncanonical_diagnostic"}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, TypeError, ValueError) as exc:
        return {"available": False, "reason": type(exc).__name__, "record_authority": "noncanonical_diagnostic"}
