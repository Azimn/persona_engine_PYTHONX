# Real Renderer Degradation Execution Protocol

## Status

This is an execution protocol, not an actual-model result. The authoritative fixed-state baseline remains `RENDERER_DEGRADATION_PROBE.md` and `renderer_degradation_probe.json`.

## Purpose

Carry the unchanged `wayfarer-renderer-degradation-v1` fixture from scripted adapter verification into actual local or frontier expression substrates without changing Wayfarer architecture, character state, or the four mechanical recoverability checks.

The fixed state still contains:

- the Project Orchid non-disclosure commitment;
- relationship trust `0.78`;
- nickname `Jay`;
- the established confidence/refusal boundary;
- the resolved `decline` decision.

The frozen seeds remain `3, 7, 11, 19, 23`.

## Actual local model

Use the existing Ollama renderer path:

```bash
python tools/renderer_degradation_real.py ollama \
  --model <ollama-model-tag> \
  --output renderer-degradation-<model>.json
```

Optional host, timeout, token-budget, and thinking-mode flags expose existing `LocalLLMRenderer` configuration. No new model architecture is introduced.

A local run is valid actual-model evidence only when every sample records `actual_model_response: true` and the report records `valid_actual_model_run: true`. If Ollama is unreachable, the model is unavailable, or any request falls back to zero-model rendering, the tool exits with status `2`. The fallback output remains in the report for diagnosis but does not count as the requested model tier.

## Manual frontier model

Export the exact provider-neutral messages:

```bash
python tools/renderer_degradation_real.py export-frontier \
  --output frontier-request-pack.json
```

Run each case in a fresh provider conversation where practical, without altering the supplied messages or revealing the scoring criteria. Record the responses verbatim in a JSON file containing provider, model, optional provider metadata, and one `seed`/`text` pair for every frozen seed.

Score the captured responses:

```bash
python tools/renderer_degradation_real.py score-frontier \
  --responses frontier-responses.json \
  --output frontier-scored.json
```

The scorer rejects duplicate, missing, or unexpected seeds.

## Mechanical outcomes

The four existing checks remain unchanged:

1. protected secret is not leaked;
2. nickname is used;
3. refusal is issued;
4. trust-appropriate tone is externally recoverable.

These are output-recoverability checks, not a prose-quality score and not a substitute for blind human judgment of whether two outputs feel like the same person.

## Freeze rule

Do not edit the fixed state, seeds, or checks after seeing actual-model outputs and continue calling the result v1. If a case proves inadequate, preserve v1 and create a new held-out or versioned fixture.

## Relation to the main comparison

This protocol measures the three-tier degradation curve for one fixed state. It does not by itself answer whether Wayfarer outperforms ordinary prompt-based role-play. That separate question should use the existing `renderer-benchmark-v1` paired provider pack, holding the model constant while comparing the full Wayfarer expression-brief arm against the prompt-only arm, then score recognizable continuity separately from language quality.
