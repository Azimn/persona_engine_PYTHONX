# Project Wayfarer Current Status

Project Wayfarer is the active development line of `Azimn/persona_engine_PYTHONX` on the `wayfarer` branch.

The frozen pre-Wayfarer comparison point remains `main` at commit `65df9144e7f0876b6e61e28d6446c50f283f9db4`. Do not use `main` documentation as current Wayfarer status.

PythonX is the reference implementation and experimental laboratory. The long-term objective is to discover and validate the minimum semantics required to preserve one portable, believable simulated individual, then project those stabilized contracts into lower-resource runtimes including a future P99/C99-compatible implementation.

## Current production checkpoint

Latest production commit:

```text
71790eb
Persist minimum-sufficient causal continuity roots
```

Latest documentation checkpoint before this status refresh:

```text
84bb1ba
Document root-only continuity production contract
```

The phase-sized Python 3.11 integration gate completed with:

```text
Focused root/continuity/replay/persistence tests: 36 passed
Full deterministic suite: 326 passed, 1 skipped, 1 warning
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

`canonical_continuity_root_eligible()` governs new durable writes. Current root families include user input/user statement, authoritative time advance, explicit self-adopted commitments, bounded sensor observations, authorized world facts/manual facts, and accepted world-action resolutions.

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

## Important open continuity gap

Slow `BeliefLedger` consolidation is persistent, but its causal replay semantics are not yet established as a first-class continuity root.

Do not declare developmental continuity complete merely because conversational, sensory, commitment, and temporal roots replay correctly. A replay that loses consolidated long-term belief change would fail the project definition even if ordinary dialogue state reconstructs correctly.

The next evidence-driven continuity experiment should force an actual slow-belief change, restart it, export it, replay it from canonical history, and determine the smallest valid causal contract. The likely alternatives are an explicit typed internal consolidation root or deterministic regeneration from another durable evidence contract. The experiment should decide between them rather than assuming either design.

Only after that semantic contract is established should Wayfarer consider further reducing or restructuring the `consolidation_evidence` stream.

## Other known limitations

Replay does not yet cover every future authoritative host/world/action family. Cross-host single-writer lease and handoff semantics remain future work. Social influence/collaboration authority is not yet fully typed. The default zero-model renderer remains linguistically limited. There is no production microphone, camera, TTS, avatar engine, or mobile-native host. Offscreen life remains limited compared with the planned event-based autonomy layer. The minimum viable individual has not yet been established through the complete ablation program.

## Standing design decisions

The local single-owner default does not require a per-event cryptographic previous-hash chain. Add adversarial tamper evidence only if the threat model expands to hostile hosts, untrusted synchronization, remote custody, or multi-party administrative control.

Developmental/plasticity parameters must earn their existence through observable behavioral effects, sensitivity analysis, identifiability checks, held-out scenarios, simpler baselines, and versioned experiment provenance. Numerical precision is not evidence of psychological validity.

## Immediate next work

1. Verify the normal Python 3.11/3.12 CI matrix on this final branch state.
2. Run a controlled slow-belief developmental continuity experiment that forces a real `BeliefLedger` change and tests restart/export/replay.
3. Promote only the minimum causal consolidation mechanism supported by that experiment.
4. Re-measure persistence after the developmental replay contract is fixed before optimizing the compact evidence stream further.

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
