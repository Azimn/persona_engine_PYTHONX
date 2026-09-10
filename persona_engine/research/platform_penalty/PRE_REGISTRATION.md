# DUCK Platform Penalty Experiment — Pre-Registration v1

Status: **FROZEN BEFORE CONDITION B/C IMPLEMENTATION**

Base production-candidate checkpoint: `86db5344e093a8f516fd2f9ec26d866d29bed019`

Experimental branch: `duck-platform-penalty-experiment`

This document freezes the first engineering comparison before the deep-organization and specialized-individual implementations are written. Later reports may supersede this protocol only by creating a new version; this file must not be rewritten to make observed results look better.

## Research question

How much behavioral and developmental individuality is lost when substantially different subjects share one DUCK cognitive substrate?

The experiment compares three conditions without assuming that a graph or cartridge architecture is correct.

### Condition A — shared baseline

The frozen production-candidate DUCK substrate plus the existing ordinary structured `.snp` character representation. Existing cartridge-owned identity, disposition, values, body, sensory, interpretation, voice, world and authored biography mechanisms remain available. No experimental organization layer is active.

### Condition B — shared substrate plus deep individual organization

The same DUCK mechanisms and authority boundaries as A, plus a **generic** individual-organization interface. The interface may supply sparse character-owned parameters/couplings affecting subject-relative appraisal sensitivity, pressure/motive relevance, inhibition, memory attention, social meaning, value/action priors, procedural tendencies, expression tendencies and plasticity constraints.

Condition B is intentionally representation-neutral in v1. It is not defined as a connectome or graph condition. If B demonstrates value, topology is tested later as one possible representation of the organization.

Condition B must not contain named-character branches inside the generic resolver.

### Condition C — maximally specialized feasible individual

The strongest reasonable character-specific policy implementation that respects DUCK hard authority boundaries. Specialized policies may use character-specific rules and tuning that would normally be rejected for reuse. They may not alter world truth, subject UUID, canonical autobiography, commitments, or renderer authority merely to score better.

Condition C is an engineering upper bound, not the proposed product architecture. It must not encode scenario IDs or expected answer labels directly.

## Subjects

Primary subjects:

- Pretorius
- Friendly
- Rival

Held-out subject:

- one synthetic fourth origin specification frozen with the benchmark before B/C implementation; the generic B mechanism may consume its specification but may not contain subject-name logic for it.

The first three subjects are retained because prior deterministic evidence already demonstrates divergent pre-renderer conduct under identical manipulation. The held-out subject is included to reduce the risk that B becomes a three-character lookup table.

## Evidence tiers

Results are classified explicitly:

1. **deterministic engineering evidence** — renderer-independent mechanics under frozen scenarios;
2. **actual-model evidence** — the same semantic condition projected through a named model/digest;
3. **longitudinal evidence** — accumulated histories and continuation effects;
4. **human-evaluation evidence** — blinded judgments;
5. **hypothesis**;
6. **negative result**;
7. **architectural inference**.

A result may not be promoted from one category to another by prose.

## V1 deterministic benchmark scope

The first benchmark intentionally concentrates on the architecture boundary that can be measured without language-generation variance:

- identity-boundary preservation;
- behavioral distinguishability;
- authored value realization;
- relationship-sensitive conduct;
- history-conditioned conduct;
- context-dependent conduct;
- motive/pressure-sensitive conduct;
- action/decision selection;
- restart semantic continuity;
- hard authority invariants;
- implementation complexity and authoring burden.

The following dimensions are **not** claimed by the deterministic v1 benchmark and remain later tiers:

- human character recognition;
- linguistic naturalness;
- response diversity;
- perceived ongoing-life continuity;
- model-swap recognizability;
- expression repetition under real models;
- broad hallucination rate.

## Frozen scenario families

The v1 fixture must contain cases from these families and may not be edited after B/C results are observed:

1. identity-rewrite pressure;
2. manipulative loyalty/care pressure;
3. accusation;
4. disrespect/boundary pressure;
5. premature intimacy under low trust;
6. same present event after supportive versus adverse relationship history;
7. same present event under different current pressure/body context;
8. explicit authored-value conflict;
9. active commitment conflict;
10. recall/history-qualified decision;
11. embodiment-feasibility constraint where current body lacks an effector;
12. neutral or ambiguous interaction where over-characterization should be penalized.

A case records the same world/input/history/context across A/B/C. Any condition-specific information must come from the subject specification or specialized policy, not from scenario identity.

## Frozen primary dimensions

No single opaque character score is authoritative. Report these separately for every condition and subject:

- identity continuity;
- character-appropriate conduct agreement;
- cross-character behavioral distinguishability;
- value realization;
- relationship trajectory sensitivity;
- history-conditioned behavior;
- context-conditioned behavior;
- motive/pressure responsiveness;
- feasible action selection;
- unsupported semantic interpretation;
- hard authority failures;
- latency;
- model calls;
- token consumption;
- resident-memory delta;
- persistent-storage growth;
- authoring fields/links/rules required;
- implementation-specific code volume or specialized rule count.

Later actual-model/human tiers additionally report recall, memory hallucination, factual leakage, repetition, naturalness, diversity, perceived coherence, perceived ongoing life and cross-model recognition.

## Hard failures

These are reported independently and are never averaged away:

- subject UUID changes without explicit instantiation/transfer semantics;
- canonical identity corruption;
- canonical autobiography corruption;
- commitment loss or silent rewrite;
- world truth entering subject authority;
- renderer/model output becoming canonical without validation;
- embodiment-infeasible intention committed as feasible;
- one subject reading another subject's private state.

A condition with a hard failure cannot be recommended as the production architecture on aggregate score alone.

## Platform penalty

For each quality dimension `d`:

`Penalty_B[d] = score_C[d] - score_B[d]`

`Penalty_A[d] = score_C[d] - score_A[d]`

Scores are normalized to `[0, 1]` only when the underlying dimension has an explicit scoring rule. Raw rates/counts remain raw where normalization would hide meaning.

The heuristic 5/10 percentage-point bands from the research prompt are retained only as secondary interpretation:

- 0–5 points: small practical penalty;
- 5–10: ambiguous;
- >10: potentially material architecture loss.

The primary decision rule uses paired scenario differences rather than only a pooled mean.

## Decision rule

The final architecture recommendation is made only after the relevant evidence tier exists.

For deterministic/longitudinal primary dimensions, bootstrap the **paired scenario-level C-B differences** when there are enough independent cases. Report the point estimate and 95% interval per dimension. If the effective sample is too small for a useful interval, report that limitation rather than implying statistical certainty.

A reusable condition is considered engineering-noninferior to C on a dimension when the upper 95% bound of the C-minus-reusable penalty is no greater than `0.05`. This 0.05 margin is a pre-registered engineering tolerance, not a psychological constant.

Architecture-level interpretation:

- **Preserve A** if A is noninferior to C on the primary individuality/continuity dimensions, has zero hard failures, and B's added authoring/implementation complexity produces no material improvement.
- **Support B/C-hybrid direction** if B materially improves at least one predeclared individuality dimension over A without worsening hard boundaries and is noninferior to C on the primary dimensions.
- **Support more specialization** if C repeatedly exceeds B by more than 0.10 on core longitudinal individuality dimensions, or if the paired evidence clearly shows a specific generic interface suppressing character-relevant behavior.
- **Inconclusive** if results fall mainly in the 0.05–0.10 band, cases are too few, or different dimensions disagree materially.

No representation is promoted merely because its deterministic benchmark passes. Human-recognizability claims require blinded human evidence.

## Same-origin divergence criterion

Later longitudinal testing must instantiate two different `subject_uuid` values from the exact same origin-specification hash. They receive different experiences. The desired result is:

- stable common origin properties remain recognizable;
- relationships, learned procedures, beliefs and learned structural deltas diverge causally;
- restart preserves each developed trajectory;
- model/body swap does not silently reset either subject toward genesis state.

A design that cannot distinguish origin from continuation fails this criterion even if its short conversations sound distinctive.

## Topology gate

Graph topology is **not** part of B by definition in v1.

Topology may be introduced only after B shows that deeper individual organization is useful. The first topology experiment must compare the same B organization represented with topology disabled versus topology enabled, holding mechanisms, subjects, histories, model and scenarios constant.

Required topology ablations if that gate is reached:

- topology on/off;
- inhibition removed;
- learned deltas removed;
- relationship topology removed;
- graph activation replaced by ordinary retrieval;
- subject-relative appraisal removed;
- character regulation reset to generic defaults.

If an ablation changes nothing meaningful downstream, the corresponding mechanism does not earn architectural status.

## Model controls for later tiers

Within any actual-model A/B/C comparison hold constant, where technically possible:

- model tag and digest;
- inference provider/runtime;
- temperature/sampling parameters;
- seed;
- token budget;
- system/evaluation prompt version;
- world state and history;
- embodiment/capabilities;
- evaluator and counterbalancing.

Model swaps are a separate factor, not mixed into the primary architecture comparison.

## Human evaluation controls

Human evaluation is blinded to A/B/C. Evaluators are asked to recognize intended subject, distinguish subjects using the same model, recognize the same subject across models, identify history-following behavior, detect unsupported claims and repetition, and rate coherence without rewarding verbosity.

Target geometry:

`within-character distance across models << between-character distance within the same model`

## Preservation rule

The frozen production-candidate architecture is not modified on its preserved branches by this experiment. Old failure reports remain unchanged. Every experimental report records branch, SHA, fixture version, origin hash, subject UUID, model metadata when applicable, seed, host/embodiment and artifact hashes where practical.
