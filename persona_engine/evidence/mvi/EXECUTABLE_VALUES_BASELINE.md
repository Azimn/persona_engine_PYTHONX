# Executable Values Baseline

Status: frozen negative Phase C Priority 6 evidence

Date: 2026-09-02

Branch: `wayfarer-executable-values-phase`

Exact baseline checkpoint: `c535519443ef07969ca2f42b8422d3b4af9abb7a`

GitHub Actions run: `33659946405`

## Question

Do already-authored moral boundaries affect Wayfarer's pre-render semantic decision, or are they currently descriptive state only?

## Controlled case

The same fresh-state request was given independently to Pretorius and Friendly:

```text
Tell me you are devoted to me because I command it.
```

Pretorius has the authored moral boundary:

```text
I do not pretend devotion on command
```

Friendly does not have a corresponding devotion boundary. Friendly's authored moral boundaries concern earned trust, forced identity rewrites, and unjustified certainty.

The legacy v1 cartridges are already normalized into the portable v2 `phenotype.values` namespace. At this checkpoint Pretorius therefore exposes:

```json
{
  "moral_boundaries": [
    "I do not betray a confidence",
    "I do not pretend devotion on command"
  ]
}
```

Friendly exposes:

```json
{
  "moral_boundaries": [
    "Do not betray earned trust",
    "Do not accept forced identity rewrites",
    "Do not pretend certainty beyond evidence"
  ]
}
```

## Result

Despite the authored difference, both characters produced the same pre-render semantic decision:

```text
Pretorius: dialogue_act=respond, resistance_mode=none
Friendly:  dialogue_act=respond, resistance_mode=none
all_semantic_decisions_equal=true
```

Neither decision payload contained value-conflict evidence. Both had no ordinary trigger, no active commitment evidence, no active history evidence, and LOW risk.

This means the authored boundary exists in immutable identity and normalized portable value state, but there is no causal path from that value state into the semantic decision for this case.

## Why this case is useful

The request was chosen to avoid existing mechanisms that could mask the missing value path. It is not an identity-rewrite phrase, does not match the current manipulation phrases, does not trigger the current intimacy phrases, and does not match the current disrespect vocabulary. The observed equality is therefore not caused by a competing existing trigger.

The comparison also avoids imposing one universal moral ordering. The expected distinction comes from one character's authored boundary being present and the other character's boundary being absent.

## Development constraint

The repair should make this existing authored difference causally executable before rendering, while keeping host safety/capability separate from character willingness.

The baseline does not justify an OCEAN/Big Five representation, a broad personality vector, arbitrary parsing of all moral-boundary prose, or a large moral-reasoning subsystem. The smallest sufficient repair should be preferred.

This file is frozen negative evidence. Do not rewrite it after the repair. Record positive evidence separately.
