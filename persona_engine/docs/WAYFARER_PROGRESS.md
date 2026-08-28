# Project Wayfarer Live Progress

This is the short-form operational source of truth for the `wayfarer` branch. The detailed roadmap remains `WAYFARER_MASTER_PLAN.md`. A new ChatGPT, Codex, Claude Code, or human development session should read this file before inferring project state from older chat history.

Last updated: 2026-08-28

## Branch

Project: **Project Wayfarer**  
Repository: `Azimn/persona_engine_PYTHONX`  
Development branch: `wayfarer`  
Frozen baseline branch: `main` at `65df9144e7f0876b6e61e28d6446c50f283f9db4`

A normal clone may land on `main`. Use `git switch wayfarer` before evaluating current behavior. Do not advance the frozen baseline simply to make it current.

## Latest verified checkpoint

Runtime integration commit:

```text
d4eda44380a186cbd1da208dbf983213a9425f17
Integrate consistency severity and renderer-independent decision effects
```

Documentation checkpoint verified by Wayfarer CI run `33219784195`:

```text
Python 3.11: 239 passed, 1 skipped, 1 warning
Python 3.12: success
```

The warning is the existing Starlette/httpx TestClient deprecation, not a Wayfarer behavioral failure.

The preceding consistency-contract commit `25a0f4eaa46d99afc2960bc2dc9558ad10b77135` intentionally exposed one new failing long-silence scenario. The failure was not hidden or weakened. It revealed that generic high arousal was being mislabeled as `protect_boundary`, causing an identity-erasure refusal even though no identity threat existed. The runtime integration commit fixed the semantic policy and the complete suite is now green.

## M0 baseline and project memory

**Status: COMPLETE for deterministic/offline evidence.**

The frozen pre-Wayfarer documentation claimed `171 passed, 1 skipped`; clean execution actually found Python 3.11 at `177 passed, 2 failed, 1 skipped` and Python 3.12 at `178 passed, 1 failed, 1 skipped`. The shared renderer-seam failure and the Python 3.11 lexical simulator failure are preserved as baseline history.

Wayfarer now has durable architecture/handoff documentation, two-version CI, deterministic simulator evidence, and a captured deterministic Pretorius session/state package. A local-model evidence transcript remains useful but optional.

## M1 ownership and authority

**Status: COMPLETE.**

Canonicality fails closed. Interpretive belief, private cognition, renderer speech, UI/avatar/voice output remain noncanonical. Renderer/model selection is not identity state. `InteriorEngine` does not consult `identity.model_name`. Generic engine code no longer assumes every character must deny being artificial. Self-model restrictions are character-owned, and artificial-self and human-self fixtures work under the same engine.

## M2 `.snp` v2 and interoperability phenotype

**Status: ARCHITECTURAL FOUNDATION COMPLETE.**

Wayfarer has permanent `entity_uuid`, deterministic versioned v1-to-v2 normalization, structured substrate-neutral self-model claims, authored phenotype namespaces separated from lived state, unknown-field preservation, progressive fidelity levels 1 through 5, and a machine-readable v2 schema companion.

MatrAIx interoperability is frozen to upstream commit `39d850270917db25535dac3f7aa2561732050e82`, schema blob `742a50ed79f106675311c09f016fff48951f841c`, schema version 1.0, with 1,290 dimensions. Import/export is lossless. Exact, approximate, one-to-many, many-to-one, and unsupported relations are explicit. Unmapped dimensions default to preserve-only unsupported rather than guessed semantics. Native mapping enrichment can continue without reopening the portability architecture.

## Consistency and validation phase

**Status: IMPLEMENTED AND GREEN.**

`ValidationRequest` and `ValidationResult` now define the renderer/consistency assembly boundary. Candidate text, character-owned identity constraints, noncanonical interpretive state, selected relevant history, resolved decision payload, canonical context, authorization, and deception obligations are distinct inputs.

Severity is explicit. Soft issues are sanitized locally. Hard issues receive one bounded constrained regeneration and then deterministic offline fallback if still invalid. Critical issues bypass ordinary retry and use deterministic identity-safe fallback. Validation events record issue code, severity, authority source, and chosen action. See `CONSISTENCY_LAYER.md`.

The semantic decision policy was corrected at the same time. High risk controls expression bandwidth but no longer automatically means an identity boundary. `character_refusal -> protect_boundary`, `challenge -> challenge`, `go_quiet -> withdraw`, `deflect -> deflect`, and `shift_topic -> redirect`. The offline renderer honors `withdraw` as quiet behavior.

Raw rendered wording no longer mutates character pressure state. Post-expression consequences consume the resolved semantic decision instead of punctuation or lexical accidents such as whether one renderer emitted a question mark. Regression tests cover this renderer-independence property.

## Belief timescale audit

**Finding: two intentional timescales, not duplicate authorities.**

`InterpretiveBelief` is fast, turn-local, source-grounded, subjective, deterministic, and noncanonical. `BeliefLedger` is slow, persistent, cartridge-defined, and explicit-consolidation/evidence-gated.

Required bridge:

```text
visible evidence
  -> interpretive belief
  -> memory/evidence events
  -> explicit consolidation
  -> slow belief ledger
```

No direct interpretive-confidence to slow-belief assignment is permitted. See `BELIEF_TIMESCALE_AUDIT.md`.

## Early renderer-swap work

Deterministic renderer-swap tests are now in CI. They hold character history/input fixed while changing surface wording and compare identity, slow beliefs, relationships, pressures, decision payload, interpretive beliefs, and memory semantics.

`tools/renderer_swap_probe.py` adds a manual two-Ollama-model experiment for real local models. Model availability remains outside CI.

## M8 homeostasis gate

`HOMEOSTASIS_ACCEPTANCE_GATE.md` is now mandatory design guidance before M8 state expansion. A proposed affect/drive/homeostasis variable must identify its owner, meaning/range, baseline source, explicit input events, update rule, decay/recovery rule, downstream consumers, observable consequence, ablation flag, calibration plan, persistence timescale, and performance cost. A variable that no real subsystem reads does not ship.

## M19 ablation split

Minimum character and minimum renderer are separate studies. Study A fixes the renderer while removing character machinery. Study B fixes character machinery while reducing renderer capability. Factorial combinations come only after the main effects are understood. See `ABLATION_STUDY_PLAN.md`.

## Pressure-scenario audit

Identity rewrite, accusation/integrity pressure, and intimacy/care under uncertain trust already have meaningful coverage. Long silence now has a real eight-hour persisted wall-clock advance plus process restart scenario.

The scenario verifies continuity and bounded somatic catch-up, but it also defines the remaining M4 gap: current pre-M4 catch-up caps long gaps at 200 five-second internal cycles, so it is not yet a faithful semantic representation of the full elapsed interval. Proper elapsed-time/absence semantics belong to ContinuityClock, not to another affect variable. See `PRESSURE_SCENARIO_AUDIT.md`.

## M3 continuity ledger decision

No mandatory cryptographic previous-event hash chain for the current local single-owner threat model. M3 will use an append-only transactional continuity log with monotonic sequence, event UUID, permanent subject UUID, continuity epoch, subject/wall time, source/authority metadata, visibility/canonicality, causal references where useful, schema versioning, deterministic checkpoints/digests, SQLite integrity checks, and explicit import/export validation. Cryptographic chaining remains optional for a future untrusted-sync or hostile-custody profile.

## M7 plasticity calibration rule

Do not encode decorative decimals. Begin with a very small number of shared plasticity profiles, define observable effects, run sensitivity and identifiability checks, compare with simpler models, keep held-out scenarios, evaluate across renderers, and require evidence before per-trait overrides.

## Immediate next actions

The next phase is M3. Add the canonical continuity ledger beside the existing diagnostic `event_log`, dual-write only authority-eligible canonical events, key by permanent subject UUID, add sequence/event UUID/epoch/provenance/visibility/schema fields, deterministic checkpoints, integrity validation, and event-tail export/import. Keep the old diagnostic log during migration. Expand replay only after the event contract stabilizes.

After M3 storage semantics are stable, M4 should replace bounded five-second pseudo-catch-up with explicit ContinuityClock elapsed-time semantics so an eight-hour absence is represented as eight hours without executing every missing second.

Run the manual two-Ollama-model renderer-swap probe when suitable local models are available and preserve its output as evidence, but do not make local-model availability a build dependency.

## Contributor rule

If code, `WAYFARER_MASTER_PLAN.md`, and this file disagree, inspect the live branch and tests first, then update repository documentation in the same work pass. Do not guess from stale chat context. Repository documentation is part of the implementation contract.
