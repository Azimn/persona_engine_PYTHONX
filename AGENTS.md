# Persona Engine Agent Instructions

These instructions are mandatory for Codex agents and other automated coding assistants working in this repository.

Before making code changes, read:

1. `README.md`
2. `persona_engine/docs/ARCHITECTURE_LOCK.md`
3. `persona_engine/docs/LAZARUS_MAPPING.md`
4. `persona_engine/docs/CURRENT_STATUS.md`

This repository is a Python lab for shaping behavior, UI, testing, and doctrine before selected improvements are ported back toward the low-hardware C99 PersonaConsole line.

## Core Doctrine

- The engine is character-agnostic.
- All character-specific content belongs in `.snp` cartridges.
- Session state stores lived history.
- World Authority owns objective facts.
- The character owns subjective interpretation.
- The LLM is a renderer only.
- Renderer output is not canonical truth.
- The UI displays organism state. It does not author organism state.
- Sensors report bounded observations only.
- Voice and avatar layers perform state only.
- Memory creation must pass through canonicality/firewall rules.
- Interpretive beliefs are subjective, noncanonical, and support-traced.
- Dream/reflection may consolidate patterns only through evidence-backed rules.

## Hard Boundaries

Do not redesign the engine unless the user explicitly asks for a redesign.

Do not change character behavior while doing packaging, documentation, UI hygiene, or test-governance work.

Do not edit cartridge files unless the task is explicitly cartridge authoring or a failing test proves a minimal schema compatibility fix is required.

Do not add dependencies unless the task explicitly requires them and the existing dependency files cannot support the requested behavior.

Do not add microphone, camera, TTS, avatar-engine, GPU, mobile-native, network-model, or Ollama requirements for tests to pass.

No UI, renderer, sensor, voice, avatar, simulator, or frontend module may directly mutate private organism state outside approved engine/world/session channels.

No engine/core module may hardcode cartridge-specific character names, phrases, voice traits, lore, or identity content.

## Where Things Belong

- Character identity, temperament, voice constraints, world/body profile, interpretation bias, belief schema, and lore: `.snp` cartridges.
- Objective facts: World Authority and approved world/session channels.
- Subjective short-term readings: interpretation layer as noncanonical, support-traced belief objects.
- Lived session history: persistence/event log/memory pathways with canonicality checks.
- Rendered prose: renderer output, logged as speech evidence only.
- UI state display: public status, trace panels, read-only debug surfaces.

## Safe Work Pattern

1. Inspect the relevant files before editing.
2. Keep changes narrowly scoped to the request.
3. Preserve package installability and command-line entry points.
4. Add or update tests when behavior or contracts change.
5. Run the most relevant tests before finishing.
6. Clearly report commands run, results, files changed, and unresolved risks.

For documentation-only changes, do not modify runtime code solely to satisfy style preferences.

## Current Verification Baseline

The expected full test command is:

```bash
python -m pytest persona_engine/tests -q
```

The current documented baseline is `195 passed, 1 skipped`.

If the local `python` command is unavailable on Windows because of the Microsoft Store alias, use an available Python interpreter and report the exact command used.
