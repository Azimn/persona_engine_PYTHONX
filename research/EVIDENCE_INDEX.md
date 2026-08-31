# Research-Facing Evidence Index

This is a map for future thesis/paper work. It is **not** the authoritative current-status document. Always inspect the linked evidence and current code before making a claim.

## Canonical continuity and replay

- `persona_engine/evidence/mvi/CANONICAL_ROOT_PROJECTION.md`
  - controlled evidence that routine derived events can be omitted from permanent biography while preserving the tested semantic replay contract;
  - useful for claims about causal-root representation and storage reduction.
- `persona_engine/evidence/mvi/ROOT_ONLY_CONTINUITY_STORAGE.md`
  - 1,000-turn production storage accounting separated by state, diagnostics, evidence, continuity roots, and checkpoints.
- `persona_engine/evidence/mvi/ROOT_ONLY_PRODUCTION_PLATEAU.md`
  - earlier long-horizon production plateau under root-only continuity.

## Path-dependent development

- `persona_engine/evidence/mvi/DEVELOPMENTAL_CONTINUITY.md`
  - pre-fix evidence showing inputs alone cannot reconstruct the demonstrated slow-belief trajectory and that even no-change consolidation boundaries can be causal.
- `persona_engine/evidence/mvi/DEVELOPMENTAL_CONTINUITY_FIXED.md`
  - post-fix evidence showing live, restart, and canonical replay agree for the demonstrated belief-rule contract.

Research use: supports a path-dependence claim for the specific implemented consolidation rules. It does not establish a general psychological theory of personality development.

## Memory, recoverability, and causal residency

- `persona_engine/evidence/mvi/SEMANTIC_MEMORY_RECOVERABILITY.md`
  - separates resident causal evidence from recoverable autobiographical wording across restarted histories and distractor conditions.
- `persona_engine/evidence/mvi/NON_USER_MEMORY_CONSUMER_AUDIT.md`
  - maps current memory families to actual production consumers and reconstruction status.
- `persona_engine/evidence/mvi/NON_USER_MEMORY_POLICY.md`
  - adversarial ablations supporting `semantic-residency-v1`; negative controls lose the targeted experiential/conduct contracts.
- `persona_engine/evidence/mvi/PRODUCTION_RESIDENT_PLATEAU.md`
  - production-only 5,000-turn plateau with `134 B` active-state growth from turn 250 to turn 5,000 and no experimental projection helper.

Research use: supports investigation of a bounded causally sufficient present versus broad resident autobiography. It does not justify a universal memory capacity number.

## Commitments and causal conduct

- `persona_engine/evidence/mvi/COMMITMENT_GAP.md`
  - pre-fix demonstration that a durable selected intention could survive restart yet fail to alter later conduct.
- `persona_engine/evidence/mvi/COMMITMENT_CONSTRAINT.md`
  - post-fix evidence that an explicitly self-adopted non-disclosure commitment survives restart and changes later semantic action from response to decline.

Research use: useful example of the difference between persistence and causal efficacy.

## Cross-host continuity

- `persona_engine/evidence/mvi/CROSS_HOST_WRITER_HANDOFF.md`
  - pre-fix dual-writer falsification and post-fix shared-store `writer-handoff-v1` evidence;
  - covers host identity, writer generation, stale-writer failure, exact state-digest handoff, subject UUID/order, commitment, relationship scope, clock, and earned-state preservation.

Research limitation: this is one shared canonical SQLite authority store. Disconnected copies, explicit branching, and reconciliation remain open and must not be claimed solved.

## Resource-bounded execution

- `persona_engine/evidence/mvi/ACTIVE_STATE_GROWTH.md`
- `persona_engine/evidence/mvi/PRODUCTION_RESIDENT_PLATEAU.md`
- `persona_engine/evidence/mvi/ROOT_ONLY_CONTINUITY_STORAGE.md`

These can support later engineering analysis of the distinction between growing biography and bounded active state. Renderer/model resource costs must be reported separately from the character kernel.

## Current evidence-quality tiers

**Tier A: internal causal engineering evidence**

Deterministic tests, controlled ablations, negative controls, restart/replay checks, and recorded probes generated during development.

**Tier B: held-out independent adversarial evidence**

Not yet established as a systematic program. This should be added before strong robustness claims.

**Tier C: human-visible evaluation**

Not yet sufficient for a broad claim that Wayfarer preserves perceived identity across heterogeneous renderers. Future blind evaluation is appropriate if that becomes the thesis question.
