# Engineering Evidence Checkpoint — 2026-08-31

This is a dated research snapshot. It is intentionally immutable historical context, **not** the live project-status source.

## System checkpoint

Runtime phase commit: `37ae2ff2ce29183a4e308ae35a195220f8535ed6` (`Enforce cross-host writer custody and handoff`).

The subsequent branch head `d881abe6493781d7cec8dfcba309601dbe9fc9f7` changed the scholarly-resources document only; normal Wayfarer CI run `33414150593` passed on both Python 3.11 and Python 3.12 against that head.

Final normal CI results:

- Python 3.11.16: `340 passed, 1 skipped, 1 warning in 29.77s`;
- Python 3.12.14: `340 passed, 1 skipped, 1 warning in 30.46s`;
- warning: existing Starlette/httpx TestClient deprecation.

## Shared-store writer custody

Authoritative evidence: `persona_engine/evidence/mvi/CROSS_HOST_WRITER_HANDOFF.md`.

The pre-fix condition allowed two independent hosts to author the same canonical subject. The production `writer-handoff-v1` contract adds explicit host identity, monotonic writer generation, transactional fencing, deliberate handoff, state-digest validation, and stale-writer failure.

Phase-local verification recorded:

- targeted custody/continuity set: `32 passed`;
- permanent shared-store handoff probe: passed;
- full deterministic Python 3.11 suite: `340 passed, 1 skipped, 1 warning in 31.68s` during the phase verification run.

A first correct implementation caused the full suite to take `314.52s` because it rewrote the custody row on every mutation. Replacing that unused heartbeat with a SQLite write reservation restored approximately normal throughput without weakening the demonstrated fence.

Scope limitation: shared canonical SQLite store only. Disconnected copies and branch reconciliation are not solved.

## Semantic memory residency

Authoritative evidence:

- `persona_engine/evidence/mvi/NON_USER_MEMORY_CONSUMER_AUDIT.md`
- `persona_engine/evidence/mvi/NON_USER_MEMORY_POLICY.md`
- `persona_engine/evidence/mvi/PRODUCTION_RESIDENT_PLATEAU.md`
- `persona_engine/evidence/mvi/SEMANTIC_MEMORY_RECOVERABILITY.md`

Current production policy is `semantic-residency-v1`, based on demonstrated consumer role and recoverability rather than a global item count.

The production-only 5,000-turn plateau used no experimental projection helper. Active serialized state measured `12,573 B` at turn 250 and `12,707 B` at turn 5,000, a `134 B` increase while canonical biography/storage continued to grow. The fixture had seven resident memories at turn 5,000; seven is an observed outcome, not a capacity rule.

## Developmental replay

Authoritative evidence:

- `persona_engine/evidence/mvi/DEVELOPMENTAL_CONTINUITY.md`
- `persona_engine/evidence/mvi/DEVELOPMENTAL_CONTINUITY_FIXED.md`

The controlled pre-fix case showed two identity-violation evidence windows consolidated separately reaching `trust_user=-0.4`; replaying only inputs reconstructed `0.0`, while one consolidation at the end reconstructed `-0.2`. A threshold-miss control showed that two no-change consolidation boundaries could also change later outcomes relative to grouping evidence into one pass.

The fixed production contract records rule-relevant `belief_consolidation` boundaries as compact causal roots. The demonstrated live, restart, and canonical replay belief all reconstruct to `-0.4`.

## Research interpretation at this date

Wayfarer has strong **internal causal engineering evidence** for several continuity mechanisms, including negative pre-fix demonstrations and targeted ablations. It does **not** yet have a systematic independent held-out adversarial evaluation program, nor sufficient human-visible renderer-swap evidence to support a broad thesis claim that users perceive one invariant individual across heterogeneous language models.

That distinction should remain explicit in later scholarly writing.
