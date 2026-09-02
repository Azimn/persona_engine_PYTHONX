# Typed Memory Attention Prototype

Date: 2026-09-02
Branch: `wayfarer-adjacent-research-phase`
Status: isolated alternative to subjective memory rewriting

## Why this experiment exists

The `authored-memory-bias-baseline-v1` freezes a concrete character-level mismatch. Rival's cartridge says `I remember losses better than compliments`, but the current generic memory ranking receives no subject profile. With an older loss and a newer compliment under a neutral recall cue, generic recency favors the compliment.

The preceding character-relative encoding baseline also showed that neutral `USER_TOLD` memories are written with the same typed salience fields across Friendly, Pretorius, and Rival.

That does not prove the solution should be personality-conditioned encoding. A smaller alternative is to preserve the lived record unchanged and let the subject apply a bounded attention bias when retrieving it.

## Prototype

`core/memory_attention.py` introduces an isolated `MemoryAttentionProfile` and a pure `rank_with_memory_attention()` function.

The profile maps explicit semantic memory tags to bounded author-owned retrieval bonuses. The experiment translates Rival's authored loss preference into the typed fixture:

```text
loss -> +0.5
compliment -> +0.0
```

With no profile, the newer compliment remains first. With the experimental Rival attention profile, the older loss becomes first.

## Authority boundaries

This prototype deliberately does not:

- parse natural-language core beliefs;
- infer whether text is a loss or compliment;
- mutate `MemoryUnit`;
- rewrite the original experience;
- change canonical continuity;
- create another memory store;
- invoke a model;
- recursively spread activation.

Semantic tags are assumed to have been supplied by some already-authorized upstream source. Production has **not** yet earned such a general tag-production path, so the prototype is not wired into `InteriorEngine` or `MemoryStore.retrieve()`.

## Regressions

`tests/test_memory_attention.py` freezes six properties:

- generic ranking remains recency-first without a profile;
- a typed loss-attention bonus can flip the Rival fixture to loss-first;
- ranking does not mutate lived memory;
- unknown tags have no effect;
- combined bonuses are globally bounded;
- a profile may impose a stricter local cap.

## Existing semantic-feature audit

`EventClassifier` already provides a character-agnostic typed classification seam before memory formation. It can identify current families such as conflict, repair, symbolic events, environmental/somatic evidence, relational input, and interpretive events. `AppraisalResult` independently exposes social interaction signals such as accusation, threat, repair, intimacy, manipulation, contradiction, and boundary violation.

Neither existing layer currently produces the `loss` / `compliment` distinction required by the frozen Rival property. Extending either classifier with those categories solely to make this prototype work would be new semantics rather than reuse of an existing authority contract.

Therefore no semantic classifier was added in this pass. The prototype demonstrates a viable **consumer** of typed salience features, not a justified producer of them.

## Interpretation

If this prototype remains green, it is evidence that Wayfarer may not need to encode the same event into permanently different autobiographical records merely to realize character-specific memory attention. A revisable retrieval-time profile can preserve the immutable event while changing what is salient to the current subject.

This is architecturally attractive because later development can change attention without rewriting history. It also keeps the character-relative layer outside World Authority and outside the renderer.

## Remaining blocker

The semantic-tag authority problem is unresolved. A mechanism that relies on `loss`, `compliment`, `betrayal`, `achievement`, or similar tags is incomplete until Wayfarer can state who is allowed to attach those tags, with what provenance, and how replay reproduces them.

The next useful comparison should prefer already-owned typed features before adding a new classifier. For example, a future longitudinal failure involving conflict, repair, manipulation, or identity pressure could test memory attention using current appraisal/classification signals without inventing new semantic categories.

Production integration is not justified merely because the isolated ranking works.
