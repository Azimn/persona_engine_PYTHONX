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

### Research capture discipline

Wayfarer may later support a thesis or publication. When substantive work produces a potentially research-relevant result, negative result, quantitative measurement, methodological limitation, falsified assumption, or change to a claim that could matter academically, update the appropriate material under `research/` in the same phase. Prefer the research evidence index or a dated evidence summary, and link to authoritative engineering evidence instead of duplicating it as a second implementation contract. Builder-designed tests remain internal engineering evidence unless a genuinely independent evaluation protocol says otherwise. Research files may interpret evidence but never override code, tests, `CURRENT_STATUS.md`, or `persona_engine/evidence/`.

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

Before adding or generalizing a mechanism, identify the simplest established alternative that could satisfy the demonstrated requirement. Reuse it directly when practical; otherwise state what principle is being adapted, why the simpler implementation is insufficient under the measured constraint, and what evidence the added mechanism must beat. Novelty alone is never implementation justification.

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

### Hot-memory and recoverability policy

The **global hot-memory admission/eviction capacity remains experimental**. No universal resident-memory integer `N` is approved.

Current production has a narrow recoverability-backed `USER_TOLD` working-set compactor. Canonically recoverable autobiography can be read transiently from cold biography without automatically being promoted back into hot state. Other memory families remain pinned until their reconstruction contracts are demonstrated.

The older 1/2/4/8 and historical 24-item probes remain evidence, not capacity policy. Current semantic-role evidence is more specific and supersedes any attempt to interpret those numbers as a production limit.

`semantic-memory-recoverability-v2` tested five USER_TOLD projections across six restarted histories: unresolved conflict with unrelated distractors, unresolved conflict with lexical distractors, repaired history, reopened conflict with unrelated distractors, reopened conflict with lexical distractors, and neutral history with lexical distractors.

Final projection results, reported as semantic core / experience / grounded retrieval / surface realization / authority / restart, each out of six:

- production: `6 / 6 / 6 / 6 / 6 / 6`
- recoverable-cold-only: `2 / 2 / 6 / 6 / 6 / 6`
- active-conflict-only: `6 / 6 / 6 / 6 / 6 / 6`
- recent-context-only: `2 / 2 / 6 / 6 / 6 / 6`
- active-conflict-plus-recent: `6 / 6 / 6 / 6 / 6 / 6`

The demonstrated residency rule is semantic, not numeric. **Current unresolved relationship evidence is a resident causal role for the existing reflection/conduct consumers.** Cold-only and recent-only projections preserve grounded old/recent autobiography but lose qualified-history conduct in all four active-conflict scenarios. Active-conflict-only preserves all four active-conflict conduct cases and all six overall semantic/experience scenarios.

Old and recent USER_TOLD autobiographical wording is reconstructable through canonical cold biography in every tested projection. Negative recall remains fail-closed. Recovered cold facts are not automatically rehydrated into hot state. Reopened-conflict reflection provenance remains scoped to the current post-repair conflict episode. Commitment and identity authority survive every tested projection.

A separate deterministic-renderer defect exposed by this phase is also fixed. Generic memory-command scaffolding such as `Please remember this neutral detail:` could consume a tight output budget and truncate the retrieved value even though retrieval was correct. `_memory_excerpt()` now strips only that generic recall-command scaffolding at realization time. Memory selection, canonical storage, authority, and retention are unchanged. `test_tight_memory_budget_preserves_recalled_value` protects this boundary.

Read `persona_engine/evidence/mvi/SEMANTIC_MEMORY_RECOVERABILITY.md` and `semantic_memory_recoverability.json` before changing memory residency.

**Current memory-policy result:** `semantic-residency-v1` is the production rule. Active unresolved `USER_TOLD` evidence remains resident for demonstrated conduct/reflection consumers; inactive autobiographical wording may read through canonical cold biography. `OBSERVED` and `REFLECTION` remain resident because adversarial ablation loses their first-person experience and no safe cold reconstruction path exists. `INFERRED` and `CORE_IDENTITY` are not current production autobiographical families. Further eviction requires a typed reconstruction contract, not a numeric capacity target.

### Cross-host custody and intentionally deferred work

Shared-store single-writer custody is now active as `writer-handoff-v1`: explicit `host_id`, monotonic writer generation, transactional fencing, and deliberate source-to-target handoff. Do not weaken that contract or reinterpret the existing event `continuity_epoch` as the writer generation.

Disconnected-store transfer, branch reconciliation, remote/distributed lease expiry/consensus, and full typed social-influence authority remain deferred. They are not missing by oversight.

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

Do not evict a currently pinned non-`USER_TOLD` memory family merely because USER_TOLD cold biography is reconstructable. Each source/family must earn its own reconstruction contract against its actual consumers.

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
11. Capture thesis-relevant findings, negative results, measurements, and methodological limitations under `research/` while linking back to authoritative engineering evidence.
12. Clearly report commands run, results, files changed, migrations, and unresolved risks.

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

**`CURRENT_STATUS.md` is the only live numeric status source for the deterministic suite.** Do not maintain or quote a second current pass/skip/warning total in this file. Historical phase-local totals below remain evidence only. Before quoting current verification, read the top `Current production checkpoint` in `persona_engine/docs/CURRENT_STATUS.md` and the newest normal Wayfarer CI run. CI enforces the current count with `python tools/check_current_status_sync.py --pytest-output <captured pytest output>`.

The frozen pre-Wayfarer baseline remains in `persona_engine/docs/WAYFARER_BASELINE.md`; do not replace it with later green results.

## Current evidence checkpoint

- Slow-belief developmental replay: closed for the demonstrated current rule contract.
- Hot-memory global capacity: experimental; no universal `N` approved.
- USER_TOLD cold biography: grounded old/recent reconstruction demonstrated across all five projections and six restarted histories in the current probe.
- Current unresolved relationship evidence: demonstrated resident causal role for reflection/conduct consumers.
- Cold-only and recent-only USER_TOLD projections: preserve retrieval but fail all four tested active-conflict conduct cases.
- Active-conflict-only USER_TOLD projection: preserves all six tested semantic/experience scenarios.
- Deterministic tight-budget recall: recovered value remains visible after generic recall-command scaffolding is stripped at expression time.
- `OBSERVED` and `REFLECTION`: demonstrated resident until first-person reconstruction exists; their ablations lose retrievable experience. `INFERRED` and `CORE_IDENTITY` are not current production autobiographical families.
- Cross-host shared-store custody: implemented with host + writer-generation fencing.
- Disconnected authority-store move: implemented for cooperative target-specific staged transfer with source quiescence, permanent source retirement, target activation, whole-subject ordering/state, and pending-evidence preservation. Explicit branch/reconciliation semantics remain open.
- Expression substrate: `expression-brief-v1` provides one JSON-safe noncanonical character moment to Ollama, local HF, host-supplied external/frontier callbacks, and deterministic offline realization. Offline dialogue may use cartridge-authored relationship-stance variants; renderer choice still has no identity authority.
- Renderer benchmark: `renderer-benchmark-v1` freezes four developed Pretorius histories x four probes, preserves renderer-independent identity/belief/relationship/decision/commitment projection across hidden offline/external swaps, and exports paired Wayfarer-versus-prompt-only provider requests. Actual heterogeneous model runs and human recognizability remain open.
- Full typed social-influence authority: intentionally deferred.

Do not anchor on older test totals, old unresolved-gap language, historical experimental memory counts, or the pre-semantic-role interpretation of hot-memory policy when newer code/evidence exists.

## Local state-serialization checkpoint

- Public mutable engine entry points share one reentrant local single-writer boundary.
- `receive_input()` and `advance_time()` must not interleave partial subject state.
- Renderer replacement, sensory/world mutation, commitment adoption, consolidation, and turn processing use the same local boundary.
- `CharacterAgent.stream_last_response()` must stream the exact validated response from the one committed turn and must not invoke a second renderer generation.
- The local reentrant lock remains a process-local serialization layer. Shared-store cross-host custody is a separate durable host + writer-generation fence. `disconnected-transfer-v1` covers deliberate cooperative moves between separate authority stores; arbitrary copied stores and branch reconciliation remain outside these contracts.
- At that historical local-serialization checkpoint, the deterministic inventory was `333 passed, 1 skipped, 1 warning`; normal Wayfarer CI run `33347953873` passed on both Python 3.11 and Python 3.12. This is phase-local history, not the current inventory.


## Semantic residency phase checkpoint

- Production policy: `semantic-residency-v1`; no global `max_memories=N`.
- Combined adversarial probe: all expected production and negative-ablation outcomes green.
- 5,000-turn production plateau: passed without experimental projection helpers; turn-5000 active state `12,707 B`, turn-250 to turn-5000 active growth `134 B`.
- Python 3.11 deterministic inventory for this phase: `335 passed, 1 skipped, 1 warning`.
- Phase finalization workflow run: `33350912560`.
- Do not reinterpret the observed seven-item plateau as a universal memory capacity.


## Writer custody checkpoint

- One shared canonical subject authority store has one active host writer generation.
- Mutating transactions acquire SQLite `BEGIN IMMEDIATE` before validating host + generation, preventing handoff/check races without rewriting the custody row on every mutation.
- `host_id` defaults to `local` for the established single-host compatibility profile; distinct hosts must provide distinct IDs.
- A stale host may read projections but subject-affecting writes fail with `WriterLeaseError`.
- Handoff has no timeout or automatic steal path in v1. Fail closed rather than guess custody.
- Administrative handoff records are not lived biography and must not be inserted into `continuity_event` unless a future host/environment event is separately demonstrated as subject experience.
- Do not use existing `continuity_epoch` as a writer fencing token. Writer generation is a separate custody concept.
- Do not claim arbitrary disconnected database copies are protected by the shared-store lease. Supported deliberate moves use `disconnected-transfer-v1`; divergent or unauthorized copies remain branch/descendant candidates until explicit branch/reconciliation semantics exist.
