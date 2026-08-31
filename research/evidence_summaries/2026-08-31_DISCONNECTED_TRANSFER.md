# Research Checkpoint: Disconnected Authority-Store Transfer

Date: 2026-08-31

This is a research-facing snapshot, not the engineering authority. Authoritative evidence is `persona_engine/evidence/mvi/DISCONNECTED_STORE_TRANSFER.md` plus its JSON probe and test suite.

## Result worth preserving

Before this phase, two separate SQLite stores could each instantiate the same permanent subject UUID and independently consider themselves writable at generation 1. The established continuity export was intentionally per-interlocutor and omitted the subject-wide canonical ordinal, so it could not constitute a whole-individual migration package.

The new internal engineering contract demonstrates a cooperative staged move in which the source is quiesced, the target stages read-only, the source store is permanently retired, and only then can the target activate the next writer generation. The probe also preserves two interlocutor-specific relationship states, subject-owned earned state, commitment state, subject-wide event ordering, and pending slow-consolidation evidence.

Targeted verification: `38 passed in 2.78s`. Full deterministic suite: `346 passed, 1 skipped, 1 warning in 31.81s`.

## Potential thesis relevance

This creates an operational distinction between a supported **move** and an unsupported **copy**. Under the supported protocol, the old authority store is explicitly retired and cannot be revived through host-id reuse. That is stronger evidence for substrate/host continuity than merely loading the same persona data in a second process.

The result remains Tier A internal engineering evidence. The fixtures and probe were designed inside the same development loop that built the mechanism. It should not be described as independent validation.

## Important limitation

Two maliciously duplicated disconnected databases that both impersonate the same target host cannot detect each other without an additional coordination or trust mechanism. The project therefore still lacks explicit intentional-branch semantics and does not claim global uniqueness or reconciliation of divergent descendants.
