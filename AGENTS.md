# Persona Engine Agent Instructions

These instructions are mandatory for Codex agents and other automated coding assistants working in this repository.

Before making code changes, read:

1. `README.md`
2. `persona_engine/docs/ARCHITECTURE_LOCK.md`
3. `persona_engine/docs/LAZARUS_MAPPING.md`
4. `persona_engine/docs/CURRENT_STATUS.md`

This repository is a Python lab for shaping behavior, UI, testing, and doctrine before selected improvements are ported back toward the low-hardware C99 PersonaConsole line.

## Foundational Definition

A digital organism is a persistent first-person subject whose interpretations and actions become the conditions of its future existence. It continuously experiences, interprets, acts, and changes through its own history. Memory records experience, but continuity is created by living under the consequences of previous experience.

The project is not fundamentally about a loop. It is about a subject. The loop is machinery used to preserve the same continuing individual across moments.

## Governing Design Filter

Every computation in the system exists only because it changes what the subject experiences, believes, intends, expresses, or becomes.

Do not add a subsystem merely because another agent framework has one or because it resembles a human faculty. A subsystem belongs in the organism core only when it changes the subject's lived position while preserving ownership, boundedness, and causal traceability.

## Core Doctrine

- The persistent subject is the object of design. The loop is machinery.
- Each new moment must be encountered by the same individual who lived through the previous moment.
- Prior experience must be capable of changing the subject who encounters the next moment.
- Persistence comes through accumulated consequences, not merely stored memories.
- The engine is character-agnostic.
- All character-specific content belongs in `.snp` cartridges.
- Session state stores lived history and inherited consequences.
- World Authority owns objective facts.
- The subject owns subjective interpretation.
- The LLM is a renderer only.
- Renderer output is not canonical truth.
- Expression substrate is not identity. Model replacement must not reset biography or lived position.
- The UI displays organism state. It does not author organism state.
- Sensors report bounded observations only.
- Voice and avatar layers perform state only.
- Memory creation must pass through canonicality/firewall rules.
- Interpretive beliefs are subjective, noncanonical, and support-traced.
- Dream/reflection may consolidate patterns only through evidence-backed rules.

## Subject Continuity Contract

Behavior-changing work must preserve the causal chain linking:

1. what happened to the subject
2. what the subject perceived
3. what prior experience became relevant
4. what the subject interpreted
5. what the subject intended
6. what the subject expressed, concealed, withheld, or did
7. what objectively followed
8. how the result changed the next subject state

Not every stage must mutate state. A valid result may be restraint, uncertainty, failed action, no disclosure, or null consolidation. The requirement is that consequences are represented honestly and remain available to condition later experience.

Memory retrieval alone does not establish continuity. Prior events must be capable of altering later appraisal, interpretation, intention, expression, inhibition, expectation, relationship position, or governed consolidation.

## Hard Boundaries

Do not redesign the engine unless the user explicitly asks for a redesign.

Do not change character behavior while doing packaging, documentation, UI hygiene, or test-governance work.

Do not edit cartridge files unless the task is explicitly cartridge authoring or a failing test proves a minimal schema compatibility fix is required.

Do not add dependencies unless the task explicitly requires them and the existing dependency files cannot support the requested behavior.

Do not add microphone, camera, TTS, avatar-engine, GPU, mobile-native, network-model, or Ollama requirements for tests to pass.

No UI, renderer, sensor, voice, avatar, simulator, or frontend module may directly mutate private organism state outside approved engine/world/session channels.

No engine/core module may hardcode cartridge-specific character names, phrases, voice traits, lore, or identity content.

Do not create a second independent subject, decision authority, or identity trajectory beside canonical subject state.

Do not let model replacement, renderer fallback, UI restart, or process restart silently replace a valid persisted subject with a fresh persona.

## Where Things Belong

- Character identity, temperament, voice constraints, world/body profile, interpretation bias, belief schema, lore, and initial dispositions: `.snp` cartridges.
- Mutable lived position, relationships, commitments, pressures, habits, and inherited consequences: canonical session/subject state.
- Objective facts and outcomes: World Authority and approved world/session channels.
- Subjective short-term readings: interpretation layer as noncanonical, support-traced belief objects.
- Lived session history: persistence/event log/memory pathways with canonicality checks.
- Rendered prose: renderer output, logged as speech evidence only.
- UI state display: public status, trace panels, read-only debug surfaces.

## Safe Work Pattern

1. Inspect the relevant files before editing.
2. Keep changes narrowly scoped to the request.
3. Preserve package installability and command-line entry points.
4. Add or update tests when behavior or contracts change.
5. For continuity changes, test that an earlier interpretation or action changes a later subject state.
6. Run the most relevant tests before finishing.
7. Clearly report commands run, results, files changed, and unresolved risks.

For documentation-only changes, do not modify runtime code solely to satisfy style preferences.

## Current Verification Baseline

The expected full test command is:

```bash
python -m pytest persona_engine/tests -q
```

The current documented baseline is `171 passed, 1 skipped`.

If the local `python` command is unavailable on Windows because of the Microsoft Store alias, use an available Python interpreter and report the exact command used.