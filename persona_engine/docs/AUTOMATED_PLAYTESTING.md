# Automated Playtesting

Run the deterministic 30-day laboratory:

```bash
python -m persona_engine.playtest --scenario persona_engine/playtest_scenarios/steady_collaborator_30_days.yaml --actor-mode scripted --judge deterministic --output-dir playtest_output/steady
```

Actors are test infrastructure, not cognition. `ActorContext` recursively
rejects private-state keys. Scripted and Ollama actors see only observable
transcript, public status, visible activity, and host-visible world records.
Causal diagnostics are collected after moves and never fed into actor policy.

Reports separate `blind_transcript.txt` from `causal_trace.json`. Saved actor
moves can replay without regenerating the actor. Optional Ollama actors use a
strict JSON response and fall back to deterministic policy on unavailability,
timeout, malformed JSON, or disallowed moves. CI never requires Ollama.

Current automated testing deliberately reports exact repetition as a failure.
The laboratory is meant to expose where the illusion breaks, not certify every
run as lifelike.
