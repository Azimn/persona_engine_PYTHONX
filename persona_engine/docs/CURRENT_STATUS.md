# Current Status

Persona Engine is currently at the v12 Human UI lineage. The Python package is the reference implementation for a deterministic, cartridge-driven character organism with a mock-safe local testing interface.

## Current Features

- Installable `persona_engine` package with editable-install support.
- Strict `.snp` cartridge validation.
- Character-agnostic engine modules.
- Lived session persistence in SQLite.
- Deterministic relationship, pressure, body, world, memory, intention, habit, symbol, belief-ledger, and interpretation systems.
- World Authority for objective host, simulator, audio, vision, and action-resolution facts.
- Interpretive beliefs grounded in visible facts.
- Renderer output treated as noncanonical speech evidence.
- Replay/debug utilities for deterministic state inspection.
- Mock-safe audio and vision observation endpoints.
- Voice-plan state and avatar-safe state projection.
- FastAPI human-testing UI with cartridge selection, session reset, streamed chat, public status, current beliefs, proactive proposals, mock sensors, and optional read-only debug details.

## Current Tests

The current expected test command is:

```bash
python -m pytest persona_engine/tests -q
```

Current expected result:

```text
69 passed
```

The simulator scripts for Pretorius, interpretation, and organism behavior are expected to pass with the mock renderer fallback.

## Known Limitations

- No real microphone adapter is implemented.
- No real camera adapter is implemented.
- No real TTS output is implemented.
- No real avatar engine is implemented.
- No GPU support is required or tested.
- No mobile-native app is implemented.
- Ollama is optional and local-only when installed.
- The UI sensor controls are mock adapters.
- Debug mode is read-only and intended for local developer inspection.
- Autonomous behavior is limited to local engine idle hooks, not a full background agent runtime.

## Recommended Next Work

1. Run a structured human-testing pass across all included cartridges.
2. Add observability and replay export from UI sessions.
3. Add cartridge tooling: lint, compare, and authoring helpers.
4. Cleanly abstract renderer providers beyond the current local Ollama/mock path.
5. Begin C99 or mobile host work only after the Python reference contracts and human-test findings stabilize.
