# Current Status

Persona Engine is currently at the v12 Human UI lineage. The Python package is the reference implementation for a deterministic, cartridge-driven character organism with a mock-safe local testing interface.

## Current Features

- Installable `persona_engine` package with editable-install support.
- Strict `.snp` cartridge validation.
- Character-agnostic engine modules.
- Lived session persistence in SQLite.
- Deterministic relationship, pressure, body, world, memory, intention, habit, symbol, belief-ledger, and interpretation systems.
- World Authority for objective host, simulator, audio, vision, and action-resolution facts.
- Formalized interpretation layer with noncanonical, support-traced interpretive beliefs grounded in visible facts.
- Mask suppression trace taxonomy for identity guard, expression envelope, resistance selector, output validator, renderer sanitizer, and memory firewall observability.
- Deterministic Tide idle drift through pressure decay, energy/restlessness/body/world/sensorium coupling.
- Long Sleep null consolidation checkpoints explicitly tested.
- Renderer output treated as noncanonical speech evidence.
- Replay/debug utilities for deterministic state inspection.
- Mock-safe audio and vision observation endpoints.
- Voice-plan state and avatar-safe state projection.
- FastAPI human-testing UI with cartridge selection, session reset, streamed chat, public status, current beliefs, proactive proposals, mock sensors, and optional read-only debug details.
- Server-backed renderer controls with local Ollama discovery, per-cartridge configuration, timeout and token limits, thinking mode, explicit offline selection, and visible fallback status.
- Conservative model capability profiles for thinking support, JSON reliability, context hints, practical generation limits, and final-answer behavior.
- Explicit new/resumed/fresh session modes, tested cartridge isolation, and read-only retrieved-memory provenance traces.
- Versioned, checksum-verified UI session bundles with transcript/report capture, canonical event separation, diagnostic turn traces, and isolated deterministic replay.
- Lean v0.2 simulated life: objective world-event ledger, subjective experience lifecycle, explained retrieval, optional embedding adapter, persisted activity/interruption state, bounded seeded vitality events, imperfect execution/learning, and cross-tier capability artifacts.
- Read-only life inspector showing objective/subjective discrepancies, recall reasons, vitality provenance, and learning artifacts.
- Situated synthesis derives integration capacity from existing organism load, narrows structured influences under strain, and links action outcomes to objective and subjective records.
- Bounded intrinsic motivation supplies cartridge-authored proposals to situated synthesis; it no longer owns final actions or changes accepted activity before selection.
- Blind behavioral evaluation can run isolated paired characters and export visible transcript separately from causal synthesis, retrieval, interpretation, and world-event records.
- A single canonical typed `ActionDecision` owns each situated turn. Replay-authoritative deterministic performance plans coordinate speech, voice, gaze, face, gesture, timing, posture, activity, and movement without becoming world facts.
- Private cognition has deterministic, model-optional, and model-required session modes with separate cognition/expression call accounting. Non-speech turns can complete with zero renderer calls.
- Interruption records distinguish input arrival, attention capture, actual activity interruption, urgency, and prior interruptibility.
- Pretorius and Kiki provide cartridge-authored dependency-free realization pools without placing character phrases in core modules.
- A bounded read-only semantic substrate provides explicit generic features, inheritance, one-hop associations, unknowns, and candidate affordances from structured concept IDs.
- Deterministic fallible self-monitoring distinguishes actual engine condition from character-perceived capacity, memory reliability, bias, conflict awareness, and attributed cause.
- Self-monitoring emits bounded regulation candidates into situated synthesis; selected delay, clarification, correction, concealment, withdrawal, habitual continuation, or doubling down changes action and multimodal performance without bypassing the executive.
- Self-monitor records persist and replay as canonical cognitive records while public status and renderer workspaces remain protected from actual diagnostics and missed conflicts.

## Current Tests

The current expected test command is:

```bash
python -m pytest persona_engine/tests -q
```

Current expected result:

```text
274 passed, 1 skipped
```

The simulator scripts for Pretorius, interpretation, organism behavior, anchored misread behavior, situated strain/recovery, paired Pretorius/Kiki evaluation, and PersonaConsole v6 compatibility are expected to pass with the mock renderer fallback.

## Known Limitations

- No real microphone adapter is implemented.
- No real camera adapter is implemented.
- No real TTS output is implemented.
- No real avatar engine is implemented.
- No GPU support is required or tested.
- No mobile-native app is implemented.
- Ollama is optional and local-only when installed.
- Local-HF registry entries are scaffolding only; the provider is not enabled in the human UI.
- Tide drift is deterministic only; stochastic mood weather is not implemented.
- Seeded whim, limitation, and rare chaos events exist only in the separate bounded vitality subsystem; they do not author world facts.
- The UI sensor controls are mock adapters.
- Debug mode is read-only and intended for local developer inspection.
- Autonomous behavior is limited to local engine idle hooks, not a full background agent runtime.
- The semantic pilot is intentionally tiny and is not a production commonsense ontology.
- Semantic activation currently requires host-supplied structured concept IDs; it does not extract concepts from prose.

## Recommended Next Work

1. Add bounded social attribution now that hypotheses have observable destinations in clarification, concealment, anticipation, delay, repair, withdrawal, and multimodal performance.
2. Blind-review the improved offline Pretorius/Kiki transcript and compare the same causal setup through Ollama without sharing private state.
3. Begin C99 fixtures for stable action, interruption, performance, self-monitor, event, experience, and semantic-activation records.
