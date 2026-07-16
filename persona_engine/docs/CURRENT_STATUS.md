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
- Bounded intrinsic motivation selects cartridge-authored wants and activities into inspectable speech or nonverbal action decisions; Pretorius and Kiki carry distinct profiles.

## Current Tests

The current expected test command is:

```bash
python -m pytest persona_engine/tests -q
```

Current expected result:

```text
216 passed, 1 skipped
```

The simulator scripts for Pretorius, interpretation, organism behavior, anchored misread behavior, situated strain/recovery, and PersonaConsole v6 compatibility are expected to pass with the mock renderer fallback.

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

## Recommended Next Work

1. Run a structured human-testing pass focused on whether pre-existing activity and interruption are perceptible in expression.
2. Compare Pretorius and Kiki offline and through Ollama, including a paired-character host scenario, without sharing private state.
3. Add conservative cartridge vitality weights only where human tests show a visible benefit.
4. Add cartridge tooling: lint, compare, and authoring helpers.
5. Begin C99 port fixtures for the stable event, experience, life-state, and artifact records.
