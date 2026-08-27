# AI Developer Handoff Protocol

This repository is expected to be worked on by multiple AI-assisted development tools and human contributors. The repository must therefore carry enough explicit project memory that no contributor needs the originating chat transcript to continue safely.

## Required reading before changes

1. `persona_engine/docs/WAYFARER_MASTER_PLAN.md`
2. `persona_engine/docs/WAYFARER_CHARTER.md`
3. `persona_engine/docs/ARCHITECTURE_LOCK.md`
4. `persona_engine/docs/CURRENT_STATUS.md`
5. `persona_engine/docs/AUTHORITY_MATRIX.md` when present
6. Relevant tests for the subsystem being modified

## Branch discipline

Wayfarer work belongs on the `wayfarer` branch unless the owner explicitly changes the workflow. Do not modify `main` directly for Wayfarer development.

## Project-memory discipline

The master plan is the canonical progress tracker. After every completed or materially changed task:

- update the relevant checkbox,
- record what changed,
- record what was tested,
- record known limitations or unresolved decisions,
- add a dated change-log entry when the change is architecturally significant.

Do not leave important decisions only in commit messages, chat threads, or hidden reasoning.

## Code-comment discipline

Comment invariants, ownership boundaries, migration assumptions, and non-obvious causal behavior. Do not fill files with comments that simply restate syntax.

Useful comment example:

```python
# Social proposals are observations, not executable goals. Promotion into an
# intention requires the character-side authority and compatibility pipeline.
```

Low-value comment example:

```python
# Increment i

i += 1
```

Public modules and boundary objects should have docstrings explaining who owns the data, whether it is canonical, and what may mutate it.

## Authority rules

- Renderer/model output may not directly mutate canonical state.
- UI code may not directly mutate private character state.
- Sensors report observations only.
- Other agents have no direct write authority over this character.
- Natural-language claims remain claims until verified by the appropriate authority path.
- World Authority owns objective world facts.
- Character state owns subjective interpretation and character-side choice.
- Host capability and character willingness are separate checks.

## Testing rules

Behavior changes require regression tests. Do not weaken a test solely to make a new implementation pass. If the contract itself changes, update the documentation and explain the migration.

At minimum, run the most relevant test module. Before a milestone is marked complete, run the complete suite documented in `CURRENT_STATUS.md` unless there is a documented blocker.

Prefer deterministic tests for canonical behavior. Model-backed tests are supplemental and must not be required for basic correctness.

## Dependency discipline

Avoid adding dependencies unless they materially improve a required capability. The deterministic core must remain offline-capable. Optional model, sensor, TTS, avatar, or network integrations must remain optional.

## Persistence discipline

Never silently reinterpret persisted state under a new schema. Add schema versions and migration logic. Preserve unknown portable fields where possible. Do not make renderer configuration part of canonical identity.

## Character-agnostic core rule

Do not hard-code Pretorius, Kiki, the user, a specific ontology, a particular species, a particular model, or a particular service into generic core logic. Character-specific behavior belongs in cartridge data or explicitly character-scoped state.

## Handoff summary requirement

When ending a substantial development session, leave the repository in a state where another contributor can answer all of the following from committed documentation:

- What milestone are we on?
- What exact task is next?
- What has already been changed?
- What tests currently pass or fail?
- What known risks remain?
- What files should be read before touching the next subsystem?
