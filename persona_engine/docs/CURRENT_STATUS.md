# Project Wayfarer Current Status

Project Wayfarer is the active development line of `Azimn/persona_engine_PYTHONX` on the `wayfarer` branch.

The frozen pre-Wayfarer comparison point remains `main` at commit `65df9144e7f0876b6e61e28d6446c50f283f9db4`. Do not use `main` documentation as current Wayfarer status.

PythonX is the reference implementation and experimental laboratory. The long-term objective is to discover and validate the minimum semantics required to preserve one portable, believable simulated individual, then project those stabilized contracts into lower-resource runtimes including a future P99/C99-compatible implementation.

## Current production checkpoint

Latest production commit:

```text
268739c
Preserve slow belief development in canonical continuity
```

The phase-sized Python 3.11 developmental integration gate completed with:

```text
Focused developmental/continuity/replay tests: 18 passed
Full deterministic suite: 330 passed, 1 skipped, 1 warning
```

The remaining warning is the existing Starlette/httpx TestClient deprecation, not a Wayfarer behavioral failure.

This status commit is intentionally made through the normal repository write path so the standard Python 3.11/3.12 Wayfarer CI matrix verifies the final documented branch state.

## Project definition

The authoritative character is not the LLM. Authored identity plus lived continuity state constitute the individual. A language model may provide interpretation, proposals, reasoning bandwidth, or linguistic realization, but renderer replacement must not silently replace identity, biography, commitments, relationships, or developmental trajectory.

Natural language is evidence, not write authority. Objective world facts require World Authority. Character-owned commitments require an explicit semantic self-decision path. Renderer/private-cognition/UI/avatar/voice output is noncanonical.

## Implemented foundation

M0 deterministic/offline evidence and repository handoff infrastructure are established. M1 ownership/authority repair is complete. M2 has permanent entity UUID, structured self-model/ontology foundations, progressive fidelity, and lossless MatrAIx phenotype interoperability. M4 ContinuityClock and demonstrated subject-owned clock state are implemented. Explicit commitment behavior, subject-wide canonical ordering, grounded cold biography, bounded resident memory behavior, and renderer-independent semantic decision paths have been exercised through deterministic tests and longitudinal probes.

The detailed operational record remains `WAYFARER_PROGRESS.md`; the roadmap remains `WAYFARER_MASTER_PLAN.md`.

## Current M3 continuity contract

New runtime continuity is **causal-root-only**.

`canonical_continuity_root_eligible()` governs new durable writes. Current root families include user input/user statement, authoritative time advance, explicit self-adopted commitments, rule-relevant slow-belief consolidation boundaries, bounded sensor observations, authorized world facts/manual facts, and accepted world-action resolutions.

Routine `state_transition` and `sensorium` records remain rich bounded diagnostic evidence but are no longer duplicated into new permanent biography. Replay regenerates those consequences from their causal roots.

Historical v1 ledgers containing derived canonical `state_transition` and `sensorium` rows remain valid, importable, and replayable. The broader historical canonical validator therefore remains separate from the narrower new-write root policy. `CONTINUITY_SCHEMA_VERSION` remains `1.0` because this is a compatible write-policy/payload refinement rather than an incompatible interchange change.

Production input roots use payload schema `input-root-v2` and preserve the user text plus only host context actually submitted at the boundary. Derived classifier output, canonicality flags, memory-type metadata, and internally generated body/world context are not stored in the durable input root.

## Root-projection and production evidence

The controlled canonical-root projection reduced a mixed history from 21 canonical events to 9 causal roots while preserving the exact semantic replay digest, cold biography, submitted host context, commitment continuity, subject time, and bounded sensory replay.

Measured projection reduction:

- serialized event bytes: 29,685 -> 7,934, a 73.27% reduction;
- payload bytes: 18,794 -> 3,245, an 82.73% reduction.

Production 1,000-turn storage after root-only integration:

- SQLite file: `2,486,272 B`;
- canonical continuity rows: `1,004`, or `1.004` per exercised turn;
- canonical continuity physical allocation: `319,488 B`;
- canonical input payload average: `75.75 B`;
- exact canonical/diagnostic duplicated payload bytes: `0`.

The comparable database measurement immediately before root-only continuity was approximately `6.78 MB`, after diagnostic/biography separation. Before persistence cleanup began, the 1,000-turn database was approximately `13.44 MB`.

Production 5,000-turn plateau after root-only integration:

- probe passed;
- turn-5,000 database: `8,581,120 B`;
- database growth from turn 250 to 5,000: `7,438,336 B`;
- turn-5,000 active serialized state: `12,758 B`;
- active-state growth from turn 250 to 5,000: `+205 B`;
- resident memories: `7`;
- canonical input count: `5,003`.

Restart and behavioral contracts remained green: same permanent subject UUID, unresolved history still qualified trust, cold lighthouse recall remained visible, the Project Orchid non-disclosure commitment still produced `decline`, identity rewrite still produced `protect_boundary`, and genuine repair returned relationship conflict to zero without stale unresolved-tension loops.

Evidence files:

- `evidence/mvi/CANONICAL_ROOT_PROJECTION.md`
- `evidence/mvi/ROOT_ONLY_CONTINUITY_STORAGE.md`
- `evidence/mvi/ROOT_ONLY_PRODUCTION_PLATEAU.md`

## Persistence ownership after this phase

`continuity_event` owns durable causal biography.

`state` and the explicitly whitelisted `subject_state` entries are current-state snapshots/caches, not substitutes for event authority.

`event_log` is bounded recent operational telemetry. It is intentionally not part of the minimum permanent person.

`consolidation_evidence` is the compact semantic evidence stream currently used by slow belief consolidation. Consumed evidence can be pruned after its consolidation watermark is persisted.

The current 1,000-turn storage profile shows that canonical continuity is no longer the dominant persistent object. Consolidation evidence plus its index and the bounded diagnostic window are now larger than the durable continuity table.

## Developmental continuity contract

The pre-fix developmental probe forced a real slow `BeliefLedger` trajectory. Two identity violations consolidated separately moved `trust_user` from `0.0` to `-0.2` to `-0.4`, and ordinary restart preserved `-0.4`. The root-only canonical export contained only the two input events, so current replay reconstructed `0.0`. Replaying both inputs and consolidating only once at the end reconstructed only `-0.2`.

The threshold control was more decisive: one repair followed by a consolidation pass, repeated twice, stayed at `0.0` because each pass consumed a sub-threshold evidence window. The same two repairs grouped before one consolidation reached `+0.15`. A no-change consolidation boundary can therefore alter later development and is genuine causal history.

Production commit `268739c` adds the minimum mechanism supported by that result. An executed pass becomes a compact `belief_consolidation` root only when it consumed evidence relevant to the active belief rules. Threshold misses are recorded; empty irrelevant passes are not. The payload records a rule digest, before/after belief digests, relevant evidence counts, changed IDs, and before/after values for changed beliefs. It is verification/causal metadata, not a full state dump.

Replay regenerates the preceding evidence, verifies the active rule digest and pre-belief digest, executes consolidation at the recorded boundary without writing a duplicate root, then verifies changed IDs and the post-belief digest. Rule mismatch requires explicit migration rather than silently replaying development under different rules. Persistence atomically commits the belief snapshot, canonical consolidation root, and pruning of the consumed evidence window.

Post-fix evidence reproduces `trust_user=-0.4` across live state, restart, and canonical replay. Two separate no-change repair boundaries also reproduce `0.0` in canonical replay. Legacy `dream_consolidation` remains a derived compatibility family.

Evidence:

- `evidence/mvi/DEVELOPMENTAL_CONTINUITY.md`
- `evidence/mvi/developmental_continuity.json`
- `evidence/mvi/DEVELOPMENTAL_CONTINUITY_FIXED.md`
- `evidence/mvi/developmental_continuity_fixed.json`

## Hot-memory policy status

The global hot-memory admission/eviction policy remains **EXPERIMENTAL**. No total resident-memory capacity was promoted by this pass.

The older `hot-memory-causal-pressure-v2` evidence was rerun against the current production engine because the meaning of its `full` control had changed over time. `InteriorEngine._persist()` now applies the narrow production `USER_TOLD` recoverability compactor even when the probe adds no experimental projection. The control is therefore current production resident state, not the historical unconstrained 24-item store.

Current rerun: experimental smallest finite budget preserving the probe's demonstrated causal roles = `2`; current no-extra-projection resident count before reflection = `7`; current no-extra-projection core pass = `True`; old-style full-resident interference still demonstrated = `False`; ordinary contextual gap across all variants = `False`. These are experiment results, not a production capacity recommendation.

The consumer-role probe still points to **role protection rather than raw capacity**. Its smallest tested role projection preserving current causal plus retrieval-trace continuity is `causal2_only`. Continuous-budget experiments report a smallest passing tested budget of `1`, but that number remains explicitly non-normative.

Production remains narrower: only canonically recoverable `USER_TOLD` autobiography is compacted, using the widths required by current consumers, while non-`USER_TOLD` families stay pinned until their reconstruction contracts are demonstrated. Contextual cold-biography candidates are transient retrieval evidence and are not automatically promoted back into hot state.

Developmental persistence was also re-measured with the new consolidation contract exercised every `50` turns across the same 1,000-input history used by its control. It committed `20` `belief_consolidation` roots at an average payload of `462.7` B. SQLite delta versus the same inputs without executed consolidation was `-761,856` B; consolidation-evidence row delta was `-7,508` because committed boundaries consume/prune their evidence windows. This is an engineering storage measurement, not validation of the psychological threshold/delta values.

**Next memory-policy question:** test admission/eviction by semantic consumer role and recoverability across multiple histories, distractor structures, repair states, and restart boundaries. Do not select a global `N` from the 1/2/4/8 experiments.

## Other known limitations

Replay does not yet cover every future authoritative host/world/action family. Cross-host single-writer lease and handoff semantics remain future work. Social influence/collaboration authority is not yet fully typed. The default zero-model renderer remains linguistically limited. There is no production microphone, camera, TTS, avatar engine, or mobile-native host. Offscreen life remains limited compared with the planned event-based autonomy layer. The minimum viable individual has not yet been established through the complete ablation program.

## Standing design decisions

The local single-owner default does not require a per-event cryptographic previous-hash chain. Add adversarial tamper evidence only if the threat model expands to hostile hosts, untrusted synchronization, remote custody, or multi-party administrative control.

Developmental/plasticity parameters must earn their existence through observable behavioral effects, sensitivity analysis, identifiability checks, held-out scenarios, simpler baselines, and versioned experiment provenance. Numerical precision is not evidence of psychological validity.

## Immediate next work

1. Verify the normal Python 3.11/3.12 CI matrix on the final developmental-continuity branch state.
2. Re-measure persistence with `belief_consolidation` roots active before changing the compact evidence stream further.
3. Use the next controlled longitudinal failure to choose between broader world/action replay, cross-host single-writer handoff, or another minimum-individual requirement; do not add all three speculatively.
4. Keep M7 plasticity calibration separate from this continuity result: replay correctness does not validate the psychological values of belief deltas or thresholds.

## Required reading

Before modifying Wayfarer behavior, read in this order:

1. `WAYFARER_MASTER_PLAN.md`
2. `WAYFARER_PROGRESS.md`
3. `WAYFARER_CHARTER.md`
4. `AI_DEVELOPER_HANDOFF.md`
5. `AUTHORITY_MATRIX.md`
6. `ARCHITECTURE_LOCK.md`
7. `WAYFARER_BASELINE.md`
8. this file
9. relevant tests and evidence

Repository documentation is part of the implementation contract. If documentation and code disagree, establish live behavior through code, history, tests, and evidence, then update documentation in the same work pass.

## Semantic memory recoverability status

**EVIDENCE COMPLETE; production global hot-memory policy remains EXPERIMENTAL.** No universal resident-memory capacity was selected and no production retention behavior changed in this phase.

`semantic-memory-recoverability-v1` compared current production against four experimental USER_TOLD projections across six histories: unresolved conflict with unrelated distractors, unresolved conflict with lexical distractors, repaired history, reopened conflict with unrelated distractors, reopened conflict with lexical distractors, and neutral history with lexical distractors. Every variant was restarted before evaluation. The probe separately checked current conduct, old and recent contextual recall, negative-recall fail-closed behavior, commitment/identity authority, and reopened-conflict provenance.

Projection results (core passes / 6): production `0/6`; recoverable-cold-only `0/6`; active-conflict-only `0/6`; recent-context-only `0/6`; active-conflict-plus-recent `0/6`.

Production passed all scenarios: `False`. Active-conflict-only passed all scenarios: `False`. Recent-only preserved every active-conflict conduct case: `False`. Cold-only preserved every active-conflict conduct case: `False`. All projections preserved the tested recoverable-context contract: `False`.

Interpret these results by semantic role, not count. Canonical biography can reconstruct the tested old/recent USER_TOLD wording without automatically rehydrating it into resident state. The discriminating resident role in this experiment is current unresolved relationship evidence needed by conduct/reflection consumers. A passing projection is not evidence that all other memory families or future behaviors can be evicted.

Evidence: `persona_engine/evidence/mvi/SEMANTIC_MEMORY_RECOVERABILITY.md` and `semantic_memory_recoverability.json`.

**Next memory-policy target:** use the observed failure matrix, if any, to isolate the smallest missing semantic/recoverability contract. If no production failure appears, expand consumer-role coverage beyond USER_TOLD before changing retention policy. Non-USER_TOLD families remain pinned until reconstruction is demonstrated.

