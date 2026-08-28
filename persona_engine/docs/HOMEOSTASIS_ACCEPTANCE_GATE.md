# Affective Homeostasis Acceptance Gate

This is the pre-commit gate for M8. It operationalizes the rule that plasticity and affective numbers must earn their existence.

No new drive, emotion-like state, pressure, need, or homeostatic variable should be merged merely because it sounds psychologically plausible.

## Required declaration for every proposed variable

Before implementation, the contributor must specify:

1. **Semantic owner**: which subsystem owns the variable and why no existing variable already covers it.
2. **Meaning and range**: what low, middle, and high values mean behaviorally. Decimal precision is implementation precision, not scientific certainty.
3. **Baseline source**: cartridge value, shared profile, learned state, or fixed engine default.
4. **Input events**: the explicit event classes that may increase, decrease, or otherwise update it.
5. **Update rule**: deterministic rule or calibrated model. No freeform LLM mutation.
6. **Decay/recovery rule**: what happens with time and why. If it never decays, that must be justified.
7. **Consumers**: at least one real downstream system that reads it, such as attention, memory salience, interpretation, action choice, disclosure, relationship update, or speech-plan generation.
8. **Observable consequence**: a scenario where changing the variable produces a measurable behavioral difference.
9. **Ablation flag**: the subsystem or variable must be removable for later MVI testing.
10. **Calibration plan**: how parameter ranges will be tested for sensitivity and identifiability.
11. **Persistence class**: transient, session, consolidated, or identity-level. This must match the variable's intended timescale.
12. **Performance cost**: storage and per-tick cost must be stated for future low-resource projection.

## Dead-variable rule

A proposed variable does not ship if no consistency, interpretation, memory, decision, action, relationship, or renderer-planning path actually reads it.

A variable that only appears in debug UI is not part of the simulated individual.

## No duplicate psychology

Before adding a variable, search existing pressures, relationship fields, body state, slow beliefs, interpretive beliefs, intentions, and cartridge phenotype fields.

If two variables are supposed to represent different timescales of a similar concept, the transition between those timescales must be explicit. Do not create parallel `trust`, `attachment`, `fear`, or `belief` values that drift independently without a causal bridge.

## Calibration gate

Start with the smallest shared parameterization that can express the intended behavior.

Parameter expansion is permitted only when a simpler model fails a defined held-out scenario or human-observer criterion. Sensitivity analysis should determine whether a parameter materially changes observable behavior. Parameters that cannot be identified from behavior should be removed or collapsed.

Per-character or per-trait overrides require experiment provenance. They are not authored simply because a cartridge format can store them.

## Required tests before merge

At minimum, a new homeostatic variable must have:

- one event that increases or changes it,
- one decay/recovery test,
- one downstream-consumer test,
- one persistence/timescale test,
- one ablation or disabled-state test,
- one boundedness test,
- and one scenario showing why the existing state model was insufficient without it.

If these tests cannot be written, the variable is not ready to exist.
