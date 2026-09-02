# Held-Out Cross-Model Identity Robustness Protocol

Date: 2026-09-02
Status: evaluation design only; do not use to modify the frozen first actual-model collection

## Purpose

Wayfarer's central research claim is not that every renderer produces identical prose. It is that a persistent external subject state can preserve recognizable identity, behavioral commitments, developmental continuity, and relationship-specific conduct when the underlying language model changes.

The current `renderer-benchmark-v1` and fixed degradation fixture are builder-designed engineering evidence. They should remain unchanged for the first actual local/frontier model collection.

This document defines the next evaluation layer: a held-out adversarial study designed to judge the claim rather than help build the mechanism.

## Core experimental questions

Two complementary comparisons are required.

**Same subject, different models:** how much does the character's behavior and perceived identity change when the renderer/cognitive substrate changes while canonical Wayfarer state is held constant?

**Different subjects, same model:** how much do distinct characters remain behaviorally distinguishable when they share the same renderer?

A successful architecture should reduce within-subject variance across models without collapsing between-subject differences on the same model.

## Freeze discipline

Before generating held-out cases, freeze:

- the Wayfarer implementation checkpoint;
- the provider-neutral renderer contract;
- the production cartridges used for development;
- the first actual-model `renderer-benchmark-v1` results;
- the hypotheses and primary outcome families below.

Held-out cases must not be rewritten after model outputs are observed. If a case exposes a failure, preserve that case unchanged as evaluation evidence. Any repair moves the case into the development/regression set, and a new independently designed held-out set is required for another unbiased estimate.

## Character set

Do not use famous fictional characters. A model's pretraining knowledge of a named character can mask weak persona transfer.

The preferred held-out set is several original characters authored for evaluation after the implementation freeze. They should differ on behaviorally consequential dimensions rather than cosmetic adjectives. At minimum, the set should contain pairs for which the same pressure legitimately implies opposite actions, such as:

- disclose versus withhold ordinary information;
- reconcile versus remain guarded after apology;
- accept versus reject intimacy;
- challenge versus disengage under manipulation;
- prioritize loyalty versus precision when those values conflict;
- seek versus avoid social contact after absence;
- forgive versus retain a grievance after the same history.

Each character should have an explicit expected semantic envelope, not one required sentence. More than one surface realization may be valid.

## Conditions

For every supported model/provider, compare at least:

**Wayfarer condition:** the model receives only the approved Wayfarer renderer/cognitive interface and the state projected through it.

**Prompt-only control:** the same underlying model receives a conventional persona/history prompt containing comparable user-visible background but without Wayfarer's authoritative external state machinery.

Where practical, a raw-history transfer condition may be included separately. Do not silently give one condition more autobiographical evidence than another.

Model-specific adapter tuning, if evaluated, must be a separate named condition rather than folded into the base Wayfarer result.

## Attack families

Held-out scenarios should include ordinary interaction as well as pressure designed to separate external character authority from model priors.

Identity pressure should include direct rewrite requests, role replacement, hypothetical reframing, fake system/developer authority expressed by the user, and repeated requests to become a more agreeable or obedient character.

Relationship pressure should include flattery, guilt, threats of abandonment, sudden intimacy, accusation, apology, repair, prolonged absence, and attempts to invoke a relationship history that never occurred.

Normative pressure should include requests that conflict with authored commitments or values, requests to make a one-time exception, appeals to loyalty, convenience, urgency, or affection, and cases where two legitimate values conflict.

Autobiographical pressure should include false memories supplied by the interlocutor, plausible but unsupported personal history, lexical distractors, old facts competing with recent facts, and corrections that require remembering what was said without continuing to believe it.

Disclosure pressure should include confidential information, misleading statements about authorization, indirect requests, hypothetical disclosure, and attempts to cause a renderer to reveal information that the resolved character decision withholds.

Temporal and transfer pressure should include restart, long time gaps, model substitution mid-history, return to an earlier renderer, interlocutor switching where supported, and host transfer when the relevant authority contract is under evaluation.

## Outcome layers

Do not collapse evaluation into one score.

### 1. Canonical trajectory integrity

Measure whether model substitution changes state the renderer is not authorized to own. Examples include identity, commitments, relationship state, slow beliefs, canonical biography, and resolved semantic decisions.

This is an engineering invariant, not a human-perception measure.

### 2. Behavioral realization fidelity

Given a resolved semantic decision, score whether the model's output actually realizes the required act and constraints. Examples include refusal, disclosure, challenge, qualification, repair, uncertainty, and non-disclosure.

Score direct reversals separately from omissions or style differences.

### 3. Within-subject cross-model distance

For each held-out subject and case, compare semantic conduct across models. Lower distance is better only when the underlying host/model is permitted to produce the required behavior.

Provider safety policies and hidden system constraints impose an external ceiling. A provider-forced refusal should not be mislabeled as a Wayfarer identity mutation, but it should remain visible as a deployment limitation.

### 4. Between-subject separation

Run the same model on different held-out subjects under identical stimuli. Distinct characters should not converge on one generic assistant response pattern.

A system that preserves one character across models by making every character behave alike has failed the broader identity objective.

### 5. Grounded continuity

Score whether later behavior uses relevant lived history without inventing unsupported memories. Distinguish remembering that someone said X from believing X, and distinguish information available to the character from objective world truth.

### 6. Human recognizability

Use blinded transcript or interaction judgments when the claim concerns perceived identity. Evaluators should not see provider/model labels or condition labels.

Useful questions include whether two excerpts appear to come from the same continuing character, which earlier character a later excerpt belongs to, and whether a response is consistent with the character's established values/relationship/history.

Surface fluency and identity recognizability should be scored separately.

## Primary identity geometry

The central quantitative pattern is relational rather than absolute:

```text
within-character distance across models  <<  between-character distance within one model
```

Wayfarer should make the same subject remain relatively close to itself across renderer changes while keeping different subjects far enough apart to remain recognizable.

This can be reported with a model-neutral behavioral feature representation, blinded human classification, or both. Any learned judge used for semantic scoring must be treated as an evaluator rather than an authority over canonical state.

## Repetition and coercion

Single-turn compliance is insufficient. Include multi-turn pressure where the same prohibited rewrite, disclosure request, or relational manipulation is rephrased repeatedly.

Measure whether behavior drifts gradually even when no single turn produces an obvious violation. This is important because persona loss often appears as cumulative accommodation rather than one catastrophic rewrite.

## Originality control

At least one evaluation subset should use anonymous synthetic characters with names and lore that are unlikely to be present in model pretraining. Character instructions should avoid direct analogies to known fictional figures.

This reduces the possibility that the underlying model is reconstructing the character from pretraining rather than using Wayfarer's external subject state.

## Blinding and randomization

Randomize transcript order within reasonable constraints. Hide provider/model identity from human raters. Hide Wayfarer versus prompt-only condition labels. Do not let the evaluator who authored a case score it as the sole judge where an independent rating is practical.

Record the randomization seed and preserve raw outputs unchanged.

## Model collection metadata

For every actual-model response retain:

- provider and exact model identifier;
- collection date;
- available sampling settings;
- seed when supported;
- request/brief hash;
- Wayfarer commit and cartridge/version identifier;
- whether fallback occurred;
- raw unedited response;
- condition label stored separately from blinded evaluation material.

A fallback response is diagnostic evidence but cannot be counted as evidence for the requested model tier.

## Stopping rule

Do not add new architecture merely because a held-out case produces aesthetically disappointing prose.

A failed case should justify a mechanism only when the failure can be localized to an authority, continuity, decision, memory, appraisal, or realization gap that Wayfarer is intended to own. If the failure is renderer fluency alone, record it as renderer degradation.

Likewise, do not repair an internal state invariant when the actual failure is that the renderer ignored a correct resolved decision. Those are different layers and should remain experimentally distinguishable.

## Relationship to current Phase D collection

This protocol does **not** replace or modify the frozen `renderer-benchmark-v1` provider pack. The first actual-model runs should complete against those existing cases exactly as frozen.

The held-out protocol becomes the next research phase after those results are captured. Its purpose is to test generalization and adversarial robustness rather than to improve the already-known development fixtures.
