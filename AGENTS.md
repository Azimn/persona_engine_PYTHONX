# Project Wayfarer Agent Instructions

These instructions are mandatory for Codex agents and other automated coding assistants working in this repository.

## Wayfarer branch notice

When working on the `wayfarer` branch, read these files before making changes, in this order:

1. `persona_engine/docs/WAYFARER_MASTER_PLAN.md`
2. `persona_engine/docs/WAYFARER_PROGRESS.md`
3. `persona_engine/docs/WAYFARER_CHARTER.md`
4. `persona_engine/docs/AI_DEVELOPER_HANDOFF.md`
5. `persona_engine/docs/AUTHORITY_MATRIX.md`
6. `persona_engine/docs/ARCHITECTURE_LOCK.md`
7. `persona_engine/docs/WAYFARER_BASELINE.md`
8. `persona_engine/docs/CURRENT_STATUS.md`
9. Relevant tests and evidence for the subsystem being modified

`WAYFARER_MASTER_PLAN.md` is the detailed roadmap. `WAYFARER_PROGRESS.md` is the short-form live operational record and must be updated after substantive work. Important implementation status, test results, architectural decisions, blockers, and next actions must be written back to repository documentation. Do not leave required project memory only in a chat, coding-agent session, commit message, or hidden reasoning trace.

At the end of a substantive Wayfarer phase, synchronize this `AGENTS.md` status/verification section whenever a new agent could otherwise anchor on obsolete test counts, completed gaps, experimental numbers, or superseded next actions.

For non-Wayfarer work, also read:

1. `README.md`
2. `persona_engine/docs/ARCHITECTURE_LOCK.md`
3. `persona_engine/docs/LAZARUS_MAPPING.md`
4. `persona_engine/docs/CURRENT_STATUS.md`

This repository is the Python reference laboratory for shaping and falsifying Project Wayfarer semantics before selected, stabilized contracts are projected toward lower-resource hosts, including a future C99/P99-compatible runtime.

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
- Slow `BeliefLedger` development is evidence-gated and path-dependent. Rule-relevant consolidation boundaries are causal history, including demonstrated no-change threshold passes.
- Natural-language social input is evidence/experience, not a direct authority token.
- A peer message, consensus claim, or model suggestion may not directly become an executable goal.
- Character willingness and host capability/permission are separate gates.
- Renderer/model selection belongs to runtime/host configuration, not identity.
- Generic engine code must not impose one ontology on every character.

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

## Current live semantic status

### Developmental continuity

The former slow-`BeliefLedger` replay gap is **closed for the current demonstrated belief-rule contract**.

Production commit `268739c` introduced the compact canonical `belief_consolidation` root. Every executed pass that consumes evidence relevant to the active belief rules is causal history, including a threshold miss that changes no belief value. Empty passes with no rule-relevant evidence remain noncanonical housekeeping.

Replay regenerates evidence from preceding causal roots, verifies the active rule digest and pre-belief digest, executes consolidation at the recorded boundary without creating a duplicate root, then verifies changed belief IDs and the post-belief digest. A rule mismatch requires explicit migration rather than silently rebuilding the subject under different developmental rules.

Do not reopen this gap merely because older progress notes describe it as pending. See `persona_engine/evidence/mvi/DEVELOPMENTAL_CONTINUITY.md` and `DEVELOPMENTAL_CONTINUITY_FIXED.md` before modifying this contract.

### Hot-memory policy

The **global hot-memory admission/eviction policy remains experimental**. Do not infer or productionize a universal resident-memory limit from any one probe.

Current production has only a narrow recoverability-backed `USER_TOLD` working-set compactor. It preserves the widths required by demonstrated consumers while canonically recoverable old autobiography can be read transiently from cold biography. Non-`USER_TOLD` memory families remain pinned until a reconstruction contract is demonstrated. Contextual cold-biography candidates are retrieval evidence for the current turn and are not automatically promoted back into hot state.

The 2026-08-30 refresh changed the interpretation of older evidence. In the current causal-pressure fixture, the no-extra-projection production path carried 7 resident memories and passed the demonstrated causal/contextual roles. The old historical 24-item unconstrained-interference result is therefore not a measurement of current production behavior.

Experimental projections remain deliberately non-normative and disagree by procedure: the refreshed role/pressure study can preserve its demonstrated roles with a 2-item projection, while the continuous-budget experiment passes 1, 2, and 4 but fails its tested 8-budget condition. This is evidence to design around **semantic consumer role and recoverability**, not to choose a global integer `N`.

See `HOT_MEMORY_CAUSAL_PRESSURE.md`, `MEMORY_CONSUMER_ROLE.md`, `CONTINUOUS_HOT_MEMORY.md`, and `DEVELOPMENTAL_PERSISTENCE_COST.md` before changing admission or eviction behavior.

### Intentionally deferred work

Cross-host single-writer handoff/lease/branch semantics and full typed social-influence authority are intentionally deferred. They are not missing by oversight. Do not pull them into a memory or developmental-continuity task merely because they appear later in the roadmap.

Divergent lived histories remain branches/descendants. Silent merge is prohibited until explicit merge semantics are designed and approved.

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

Do not add cryptographic machinery merely because an ordinary append-only local ledger exists. Security mechanisms must correspond to an explicit threat model. For the current local single-owner prototype, sequence numbers, transactions, schema validation, state digests/checkpoints, and integrity checks are the default continuity-ledger tools. A cryptographic hash chain is optional future hardening for untrusted synchronization or hostile custody.

Do not proliferate per-trait plasticity constants without an experimental validation plan. Numerical parameters must produce identifiable observable effects, survive sensitivity/holdout testing, and be versioned with their evidence.

Do not impose a global hot-memory count from a single 1/2/4/8 or similar probe. A production admission/eviction rule must be justified by demonstrated consumer roles, recoverability, multiple histories/distractor structures, repair state, restart behavior, and the relevant ablations.

## Where Things Belong

- Authored character identity, temperament, values, voice constraints, phenotype, world/body profile, interpretation bias, belief schema, lore, plasticity profiles, and initial dispositions: `.snp` portable character source.
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
2. Check the current Wayfarer milestone, `WAYFARER_PROGRESS.md`, and current evidence before assuming an older stated gap still exists.
3. Keep changes narrowly scoped to the active task.
4. Search callers before altering public interfaces.
5. Preserve package installability and command-line entry points.
6. Add or update tests when behavior or contracts change.
7. For continuity changes, test that an earlier interpretation or action changes a later subject state and survives the relevant restart/export/replay boundary.
8. Run the most relevant tests before finishing.
9. Update `WAYFARER_PROGRESS.md` and the master plan/status documentation as appropriate.
10. Synchronize this `AGENTS.md` current-status/verification block when substantive work changes what a fresh agent should assume.
11. Clearly report commands run, results, files changed, migrations, and unresolved risks.

Prefer one tested phase commit for implementation/evidence/documentation when practical. If GitHub Actions must be used as a write/test bridge, avoid long `Stage` / `Trigger` / `Retrigger` commit chains. Prefer a one-shot self-triggering temporary workflow or another mechanism that leaves one meaningful phase commit after cleanup. Failed tooling attempts are not architecture and should not become the main project narrative.

For documentation-only changes, do not modify runtime code solely to satisfy style preferences.

## Code comments and docstrings

Comment invariants, authority boundaries, migration assumptions, and non-obvious causal behavior. Do not comment trivial syntax.

Boundary modules and structured state objects should document:

- who owns the data,
- whether it is canonical,
- what may propose changes,
- what may actually commit changes,
- what is expected to survive model/host replacement.

## Current verification state

The expected full test command is:

```bash
python -m pytest persona_engine/tests -q
```

The original pre-Wayfarer baseline and its known failures are recorded in `persona_engine/docs/WAYFARER_BASELINE.md`. Do not replace that frozen baseline with later green results.

Current phase/evidence head before this instruction sync:

- Phase commit: `01b0a9524db37b98c4debc101f63b490a77fa9ed` (`Refresh hot-memory and developmental persistence evidence`)
- Phase integration run: `33337114891`
- Python 3.11 integration suite: `330 passed, 1 skipped, 1 warning in 43.39s`
- The warning is the existing Starlette/httpx TestClient deprecation, not a Wayfarer behavioral failure.

Latest completed normal two-version Wayfarer CI before this instruction sync:

- Run: `33337114880`
- Tested commit: `3c1232fc721fadcdaafebfb2f9d8c61fba96018e`
- Python 3.11.16: `330 passed, 1 skipped, 1 warning in 35.49s`
- Python 3.12.14: `330 passed, 1 skipped, 1 warning in 27.93s`

The phase commit differs from that CI-tested staging commit by the generated evidence/tool/docs and cleanup of the temporary evidence workflow; the phase integration itself ran the full Python 3.11 suite successfully before committing those results. Check GitHub Actions for any newer branch head before quoting a newer result.

## Current evidence checkpoint

- Slow-belief developmental replay: closed for the demonstrated current rule contract.
- Hot-memory global capacity: experimental; no universal `N` approved.
- Current pressure-fixture production resident count: 7, scenario-specific and not a limit.
- Developmental storage probe: 20 `belief_consolidation` roots added 9,254 canonical payload bytes while consuming 7,508 stale consolidation-evidence rows; the developmental database was 761,856 B smaller than the same 1,000 inputs without executed consolidation.
- Cross-host handoff/branching: intentionally deferred.
- Full typed social-influence authority: intentionally deferred.

Do not anchor on older test totals, old unresolved-gap language, or historical experimental memory counts when newer code/evidence exists.