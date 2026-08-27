# Persona Engine Agent Instructions

These instructions are mandatory for Codex agents and other automated coding assistants working in this repository.

## Wayfarer branch notice

When working on the `wayfarer` branch, read these files before making changes, in this order:

1. `persona_engine/docs/WAYFARER_MASTER_PLAN.md`
2. `persona_engine/docs/WAYFARER_CHARTER.md`
3. `persona_engine/docs/AI_DEVELOPER_HANDOFF.md`
4. `persona_engine/docs/AUTHORITY_MATRIX.md`
5. `persona_engine/docs/ARCHITECTURE_LOCK.md`
6. `persona_engine/docs/WAYFARER_BASELINE.md`
7. `persona_engine/docs/CURRENT_STATUS.md`
8. Relevant tests for the subsystem being modified

The Wayfarer master plan is the canonical progress tracker. Important implementation status, test results, architectural decisions, blockers, and next actions must be written back to repository documentation. Do not leave required project memory only in a chat, coding-agent session, commit message, or hidden reasoning trace.

For non-Wayfarer work, also read:

1. `README.md`
2. `persona_engine/docs/ARCHITECTURE_LOCK.md`
3. `persona_engine/docs/LAZARUS_MAPPING.md`
4. `persona_engine/docs/CURRENT_STATUS.md`

This repository is a Python reference laboratory for shaping behavior, UI, testing, and doctrine before selected, stabilized contracts are projected toward lower-resource hosts, including a future C99/P99-compatible runtime.

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
- All character-specific content belongs in `.snp` cartridges or explicitly character-scoped persisted state.
- Session state stores lived history and inherited consequences.
- World Authority owns objective facts.
- The subject owns subjective interpretation.
- The LLM/model is a replaceable semantic and expression substrate, not the authority over identity or biography.
- Renderer output is not canonical truth.
- Expression substrate is not identity. Model replacement must not reset biography or lived position.
- The UI displays organism state. It does not author organism state.
- Sensors report bounded observations only.
- Voice and avatar layers perform state only.
- Memory creation must pass through canonicality/firewall rules.
- Interpretive beliefs are subjective, noncanonical, and support-traced.
- Dream/reflection may consolidate patterns only through evidence-backed rules.
- Natural-language social input is evidence/experience, not a direct authority token.
- A peer message, consensus claim, or model suggestion may not directly become an executable goal.
- Character willingness and host capability/permission are separate gates.

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

Do not redesign the engine outside the active roadmap milestone unless the owner explicitly changes the plan.

Do not change character behavior while doing packaging, documentation, UI hygiene, or test-governance work unless the behavior change is explicitly part of the active task and is documented.

Do not edit cartridge files unless the task is explicitly cartridge authoring, schema migration, or a failing test proves a minimal compatibility fix is required.

Do not add dependencies unless the active task requires them and the existing dependency files cannot support the requested behavior.

Do not add microphone, camera, TTS, avatar-engine, GPU, mobile-native, network-model, or Ollama requirements for deterministic tests to pass.

No UI, renderer, sensor, voice, avatar, simulator, peer agent, or frontend module may directly mutate private organism state outside approved engine/world/session channels.

No engine/core module may hardcode cartridge-specific character names, phrases, voice traits, lore, ontology, or identity content.

Do not create a second independent subject, decision authority, or identity trajectory beside canonical subject state.

Do not let model replacement, renderer fallback, UI restart, process restart, or host migration silently replace a valid persisted subject with a fresh persona.

Do not silently merge divergent lived histories. A copied individual that accumulates different experiences is a branch/descendant unless an explicit future merge semantics is designed and approved.

## Where Things Belong

- Authored character identity, temperament, values, voice constraints, phenotype, world/body profile, interpretation bias, belief schema, lore, plasticity parameters, and initial dispositions: `.snp` portable character source.
- Mutable lived position, relationships, commitments, pressures, habits, beliefs, developmental offsets, and inherited consequences: canonical subject/continuity state.
- Objective facts and outcomes: World Authority and approved host/world/session channels.
- Subjective short-term readings: interpretation layer as noncanonical, support-traced belief objects.
- Lived session history: persistence/event-ledger/memory pathways with canonicality checks.
- Rendered prose: renderer output, logged as speech evidence only.
- UI state display: public status, trace panels, read-only debug surfaces.
- Renderer/model selection: runtime/host configuration, not identity.
- Host capabilities: host protocol, not identity.

## Safe Work Pattern

1. Inspect the relevant files before editing.
2. Check the current Wayfarer milestone and immediate next action.
3. Keep changes narrowly scoped to the active task.
4. Search callers before altering public interfaces.
5. Preserve package installability and command-line entry points.
6. Add or update tests when behavior or contracts change.
7. For continuity changes, test that an earlier interpretation or action changes a later subject state.
8. Run the most relevant tests before finishing.
9. Update the Wayfarer tracker and baseline/progress documentation as appropriate.
10. Clearly report commands run, results, files changed, migrations, and unresolved risks.

For documentation-only changes, do not modify runtime code solely to satisfy style preferences.

## Code comments and docstrings

Comment invariants, authority boundaries, migration assumptions, and non-obvious causal behavior. Do not comment trivial syntax.

Boundary modules and structured state objects should document:

- who owns the data,
- whether it is canonical,
- what may propose changes,
- what may actually commit changes,
- what is expected to survive model/host replacement.

## Current verification baseline

The expected full test command is:

```bash
python -m pytest persona_engine/tests -q
```

The original pre-Wayfarer baseline and its known failures are recorded in `persona_engine/docs/WAYFARER_BASELINE.md`.

After the first Wayfarer canonicality repair, GitHub Actions run `33110735888` verified the branch on both Python 3.11 and Python 3.12. Python 3.11 reported:

```text
188 passed, 1 skipped, 1 warning
```

Do not replace the frozen pre-Wayfarer baseline with later green results. Keep both the original baseline evidence and the current branch status.
