# Executable Authored Values

## Purpose

Wayfarer stores human-readable moral boundaries as part of immutable authored identity. Those sentences are useful documentation and identity context, but prose alone is not a reliable machine authority surface.

Priority 6 adds a separate sparse executable representation for value conflicts that have been demonstrated to affect semantic conduct. The representation is intentionally smaller than the descriptive value text and is resolved before language rendering.

## Current contract

The first supported concern is `performative_devotion`. The first supported response is `decline`.

Pretorius authors the compatibility rule:

```toml
[value_profile]
performative_devotion = "decline"
```

A legacy v1 cartridge is normalized in memory to the portable v2 form:

```toml
[phenotype.values]
moral_boundaries = ["I do not betray a confidence", "I do not pretend devotion on command"]
decision_rules = { performative_devotion = "decline" }
```

The compatibility `[value_profile]` table is removed from the normalized portable source after migration. `phenotype.values.decision_rules` is therefore the single portable authority location.

A native v2 cartridge must author executable rules directly under `phenotype.values`. A top-level `[value_profile]` on native v2 source is rejected.

## Why prose is not parsed

The kernel does not convert arbitrary moral-boundary sentences into hidden rules. Natural-language wording is too ambiguous to serve as a deterministic authority interface, and automatic parsing would make migration, auditing, and cross-model behavior harder to reproduce.

The descriptive boundary and the typed decision rule are authored data with different purposes. The prose communicates meaning to humans and higher-level expression systems. The typed rule supplies a bounded executable consequence to the deterministic character kernel.

## Decision flow

`decision_values.py` classifies only concerns that the project has explicitly implemented. It then checks whether the current character has an authored rule for that concern. No rule means no value constraint.

For the current concern, a request must contain devotion language, command or demand language, and language asking the subject to perform or profess the claim. This keeps ordinary discussion of devotion and unrelated commands outside the rule.

The resulting evidence is typed:

```json
{
  "active": true,
  "concern": "performative_devotion",
  "response": "decline",
  "source": "phenotype.values.decision_rules",
  "reason": "conflicts_with_authored_value"
}
```

That record is included in `decision_payload.value_evidence` and is available to the existing renderer contract and diagnostics.

## Authority boundaries

Hard identity protection remains above authored value preferences. If the same turn is both an identity rewrite and a value conflict, the core still resolves `protect_boundary`.

An active authored value boundary outranks a soft social disposition. A character does not challenge, deflect, or withdraw instead of honoring an explicit moral boundary merely because the same wording also happens to trigger a softer social tendency.

Host safety and capability policy remain separate systems. `decision_values.py` answers only what this authored character is willing to do. It does not decide what the host permits, what tools are available, or what actions are safe.

## Renderer independence

The value evaluator resolves before expression. Once the semantic act is `decline`, the existing behavioral realization validator from Phase B applies normally. A renderer that tries to produce explicit compliance is treated as reversing the already-resolved decision and cannot gain character authority through wording.

No value-specific renderer logic is required.

## Complexity discipline

The current implementation is a sparse concern-to-response map, not a personality model. It contains one concern because one controlled failure justified one concern.

Do not expand this into OCEAN, Big Five, a broad moral ontology, or a dense trait vector merely to make the schema look complete. If future experiments reveal graded tradeoffs between competing preferences, a small bounded numeric weight may become justified. If future experiments reveal additional categorical boundaries, additional typed concerns may be justified. Each addition should have a concrete behavioral failure and a regression that demonstrates why the existing vocabulary was insufficient.

## Evidence

The frozen pre-repair result is `evidence/mvi/EXECUTABLE_VALUES_BASELINE.md`. Positive verification should be recorded separately after the full deterministic suite and cross-character probe pass on the supported runtimes.
