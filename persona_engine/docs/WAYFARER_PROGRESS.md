# Project Wayfarer Live Progress

This is the short-form operational source of truth for the `wayfarer` branch. The detailed roadmap remains `WAYFARER_MASTER_PLAN.md`. A new ChatGPT, Codex, Claude Code, or human development session should read this file before inferring project state from older chat history.

Last updated: 2026-08-28

## Current branch and lineage

Project: **Project Wayfarer**  
Repository: `Azimn/persona_engine_PYTHONX`  
Development branch: `wayfarer`  
Frozen pre-Wayfarer branch: `main`  
Frozen baseline commit: `65df9144e7f0876b6e61e28d6446c50f283f9db4`

A normal clone may still land on `main`. Use:

```bash
git switch wayfarer
```

Do not move the frozen baseline merely to make it look current.

## Current runtime checkpoint

Latest integrated runtime commit before this documentation refresh:

```text
d4eda44380a186cbd1da208dbf983213a9425f17
Integrate consistency severity and renderer-independent decision effects
```

The immediately preceding consistency-contract commit was:

```text
25a0f4eaa46d99afc2960bc2dc9558ad10b77135
Formalize consistency layer and early invariance tests
```

That first consistency commit intentionally exposed a real long-silence semantic bug: generic high arousal was being converted into `protect_boundary`, so eight hours of bounded idle catch-up followed by `...` produced an identity-erasure refusal even though there was no identity threat. CI at that checkpoint reported `233 passed, 1 failed, 1 skipped, 1 warning` on Python 3.11, with the same new scenario failing on Python 3.12.

The runtime integration commit fixes the defect at the decision layer rather than relaxing the simulator oracle. High arousal now changes expression bandwidth but does not by itself define the semantic dialogue act. `character_refusal` resolves to `protect_boundary`, `challenge` remains challenge, `go_quiet` resolves to `withdraw`, `deflect` resolves to deflect, and `shift_topic` resolves to redirect. The offline renderer explicitly honors `withdraw` as quiet behavior.

The targeted integration workflow completed successfully before pushing `d4eda443...`. The normal Python 3.11/3.12 Wayfarer CI is triggered by this documentation commit and is the final verification for this checkpoint.

## Frozen baseline findings

The pre-Wayfarer documentation claimed `171 passed, 1 skipped`; that count was stale. Clean GitHub-hosted execution of the frozen baseline found:

```text
Python 3.11: 177 passed, 2 failed, 1 skipped, 1 warning
Python 3.12: 178 passed, 1 failed, 1 skipped, 1 warning
```

One shared failure was a stale renderer test patching `generate()` after production had moved to `generate_expression()`. Python 3.11 also exposed a brittle lexical simulator expectation. These findings are preserved as baseline history rather than rewritten away.

## M0: baseline and durable project memory

**Status: COMPLETE for deterministic/offline evidence.**

Completed:

- [x] Frozen pre-Wayfarer baseline commit recorded.
- [x] Wayfarer CI established for Python 3.11 and 3.12.
- [x] Architecture charter, authority matrix, baseline manifest, AI handoff rules, master roadmap, live tracker, and root `AGENTS.md` established.
- [x] All documented deterministic simulators captured through the evidence workflow.
- [x] Deterministic Pretorius session/state evidence captured.
- [x] Offline-renderer defect found by that evidence was preserved before repair.
- [x] Simulator semantic oracles stabilized so valid repair/apology language does not fail on incidental wording.
- [D] A local-model evidence transcript is useful but does not block M0.

## M1: ownership, canonicality, renderer independence, ontology

**Status: COMPLETE.**

Key completed contracts:

- [x] Production validator test exercises `generate_expression()`, the actual renderer seam.
- [x] Explicit noncanonical markers fail closed.
- [x] Interpretive belief, private cognition, renderer speech, UI/avatar/voice output remain noncanonical.
- [x] Renderer/model selection is not identity state.
- [x] `InteriorEngine` does not consult `identity.model_name`.
- [x] Generic engine code no longer assumes every character must deny being an AI or language model.
- [x] Self-model restrictions are character-owned.
- [x] Artificial-self and human-self characters coexist under the same generic engine.

## M2: `.snp` v2 and interoperability phenotype

**Status: ARCHITECTURAL FOUNDATION COMPLETE.**

Completed:

- [x] Permanent `entity_uuid` separate from display name.
- [x] Deterministic, versioned v1-to-v2 normalization.
- [x] Structured substrate-neutral self-model claims with certainty and mutability semantics.
- [x] Authored phenotype namespaces separated from lived mutable state.
- [x] Unknown portable data must be preserved.
- [x] Progressive fidelity levels 1 through 5 defined.
- [x] Machine-readable Wayfarer v2 schema companion added.
- [x] MatrAIx reference frozen to upstream commit `39d850270917db25535dac3f7aa2561732050e82`, schema blob `742a50ed79f106675311c09f016fff48951f841c`, schema version 1.0, 1,290 dimensions.
- [x] Lossless MatrAIx import/export layer implemented.
- [x] Exact, approximate, one-to-many, many-to-one, and unsupported mapping relations represented explicitly.
- [x] Every unmapped MatrAIx dimension has defined `preserve_only_unsupported` behavior rather than guessed native semantics.
- [x] Offline crosswalk/catalog audit can validate a local copy of the frozen upstream schema.

Native crosswalk enrichment can continue later without reopening the underlying portability architecture.

Last fully green pre-consistency CI checkpoint: Python 3.11 `224 passed, 1 skipped, 1 warning`; Python 3.12 also green.

## Consistency/validation checkpoint pulled forward from later milestones

This phase implemented several load-bearing contracts earlier than originally scheduled.

### Explicit consistency interface

- [x] Added typed `ValidationRequest` and `ValidationResult` assembly boundary.
- [x] Validation input explicitly distinguishes candidate text, character-owned identity constraints, noncanonical interpretive state, selected relevant history, resolved decision payload, canonical context, authorization, and deception obligations.
- [x] Added `CONSISTENCY_LAYER.md` so a future contributor cannot silently change the renderer/validator seam without changing the contract.

### Severity and response policy

- [x] `soft` issue: local sanitize-and-continue.
- [x] `hard` issue: one bounded constrained regeneration, followed by deterministic offline fallback if still invalid.
- [x] `critical` issue: skip ordinary retry and use deterministic identity-safe fallback.
- [x] Self-model and explicit World Authority conflicts are critical.
- [x] False-memory, unauthorized-fabrication, private-user-state, and deception contradictions are hard.
- [x] Validation events now record issue code, severity, authority source, and chosen response action.

### Renderer output no longer writes affect through wording

- [x] Removed raw response-text/punctuation feedback from character pressure updates.
- [x] Post-expression consequences now consume the resolved semantic `decision_payload` rather than whether a renderer happened to use `?`, `no`, or `won't`.
- [x] Added regression proving two renderers with different punctuation cannot create different pressure trajectories from the same resolved turn.

### Early renderer-swap invariance

- [x] Added deterministic renderer-swap contract tests holding character input/history fixed while changing surface wording.
- [x] Tests compare identity, slow beliefs, relationship state, pressures, decision payload, interpretive beliefs, and memory semantics.
- [x] Added manual `tools/renderer_swap_probe.py` for a real two-Ollama-model local experiment when suitable models are available.

## Belief-structure audit

**Finding: two structures exist intentionally, at different timescales. They are not duplicate authorities.**

`InterpretiveBelief` is fast, turn-level, source-grounded, subjective, deterministic, and noncanonical. `BeliefLedger` is slow, persistent, cartridge-defined, and consolidation/evidence-gated. The required causal bridge is:

```text
visible evidence
  -> interpretive belief
  -> memory/evidence events
  -> explicit consolidation
  -> slow belief ledger
```

No direct `InterpretiveBelief.confidence -> BeliefRecord.value` assignment is permitted. See `BELIEF_TIMESCALE_AUDIT.md`.

## M8 homeostasis acceptance gate

The homeostasis milestone may not add variables simply because they sound psychologically plausible.

`HOMEOSTASIS_ACCEPTANCE_GATE.md` now requires every proposed state variable to declare its owner, semantic range, baseline source, explicit input events, deterministic/calibrated update rule, decay/recovery rule, downstream consumers, observable consequence, ablation flag, calibration plan, persistence timescale, and performance cost.

A state variable that no real decision, interpretation, memory, relationship, consistency, or speech-planning path reads does not ship.

## M19 ablation split

The Minimum Viable Individual work is now explicitly two studies:

```text
Study A: hold renderer fixed, remove character machinery
Study B: hold character machinery fixed, reduce renderer capability
```

Only after the main effects are understood should reduced character kernels and reduced renderers be combined factorially. See `ABLATION_STUDY_PLAN.md`.

## Pressure-scenario audit

Identity rewrite, accusation/integrity pressure, and intimacy/care under uncertain trust already have meaningful existing coverage.

Long silence was only partially covered before this phase. Wayfarer now has a real eight-hour persisted wall-clock advance plus process restart scenario. It verifies that identity persists and bounded idle catch-up materially changes somatic state rather than resetting it.

The test exposed a genuine semantic bug, now repaired: overload no longer masquerades as an identity boundary.

Important remaining limitation: the current pre-M4 catch-up still caps long gaps at 200 five-second internal cycles. Because `WorldState.idle_events()` receives five-second slices, this is not a complete representation of eight hours of subject time and does not yet generate correct long-gap absence semantics. That belongs to M4 ContinuityClock, not to another affect variable. See `PRESSURE_SCENARIO_AUDIT.md`.

## Design decision: M3 continuity ledger remains simple

No mandatory cryptographic previous-event hash chain for the local single-owner prototype.

M3 target remains an append-only transactional continuity log with monotonic sequence, event UUID, permanent subject UUID, continuity epoch, subject/wall time, source/authority metadata, visibility/canonicality, causal references where useful, schema versioning, deterministic state checkpoints/digests, SQLite integrity checks, and explicit import/export validation.

Cryptographic chaining is deferred unless Wayfarer later gains a real untrusted-sync or hostile-custody threat model.

## Design decision: M7 plasticity parameters require calibration

Wayfarer must not encode aesthetic decimal precision as scientific validity. Start with a very small number of shared plasticity profiles, define observable effects, run sensitivity/identifiability checks, compare against simpler models, hold out scenarios from tuning, evaluate across renderers, and require evidence before adding per-trait overrides.

## Immediate next actions

1. Confirm the normal Python 3.11/3.12 CI for the integrated consistency checkpoint is green and record the exact count here.
2. Begin M3 as a phase-sized ledger implementation: add the canonical continuity table beside the existing diagnostic `event_log`, dual-write only authority-eligible canonical events, key by permanent subject UUID, add sequence/event UUID/epoch/provenance/visibility/schema fields, deterministic checkpoints, integrity validation, and event-tail export/import.
3. Keep legacy `event_log` during M3 migration rather than rewriting persistence in one destructive step.
4. Expand replay only after the ledger event contract is stable.
5. In M4, replace bounded five-second pseudo-catch-up with explicit elapsed-time/ContinuityClock semantics so an eight-hour absence is represented as eight hours without executing every missing second.
6. Run the manual two-Ollama-model renderer-swap probe when local models are available and preserve its output as evidence, but do not make model availability a CI requirement.

## Contributor rule

If code, `WAYFARER_MASTER_PLAN.md`, and this file disagree, inspect the live branch/tests first and then update repository documentation in the same work pass. Do not guess from stale chat context. Repository documentation is part of the implementation contract.
