# Wayfarer Consistency Layer Contract

This document freezes the interface between character resolution, renderer output, and pre-exposure validation.

The consistency layer is not a second planner. It does not decide what the character wants to say. It evaluates whether a renderer's candidate text faithfully realizes a decision that already exists.

## Normative input

`ValidationRequest` is the validation boundary.

It contains:

- `candidate_text`: renderer output. This is always noncanonical until accepted.
- `identity_constraints`: character-owned self-model restrictions. These have higher authority than renderer text.
- `interpretive_state`: current noncanonical subjective readings. These may guide consistency checks but do not become world truth.
- `relevant_history`: only memories selected by the character core. The validator does not independently retrieve history.
- `decision_payload`: the already-resolved dialogue/action intent that the candidate is supposed to realize.
- `canonical_context`: explicit high-authority constraints supplied by World Authority or another canonical owner.
- `authorization`: bounded deception/fabrication authority where a scenario explicitly permits it.
- `deception_ledger`: existing consistency obligations created by prior authorized deception.

The validator may not invent additional identity rules, world facts, memories, goals, commitments, or preferred conduct.

## BehavioralContract

`BehavioralContract` is the minimum renderer-independent conduct projection derived from `decision_payload`.

It currently carries:

- the resolved `dialogue_act`;
- whether the candidate must visibly signal noncompliance;
- whether explicit compliance would contradict the decision;
- whether the decision represents identity-boundary protection;
- active typed commitment kind and target when the decision already contains that evidence.

The contract is not persisted as a second decision and it does not compete with the character core. It exists only so the consistency layer can ask whether surface language implemented the decision that already exists.

The first production behavioral checks are deliberately narrow. `decline` and `protect_boundary` must visibly remain noncompliant. `decline`, `protect_boundary`, `withdraw`, `deflect`, and `redirect` may not contain an explicit positive offer to perform, reveal, obey, submit, or accept the conduct the resolved act rejected.

More nuanced acts should not be added through broad sentiment or role-play heuristics. They require concrete failure cases showing that a deterministic realization check can protect character fidelity without turning the validator into a second planner.

## Normative output

`ValidationResult` contains the original candidate, the currently usable output text, typed issues, and a recommended action.

Severity is explicit:

| Severity | Meaning | Default action |
|---|---|---|
| `soft` | wording wobble that does not invalidate the underlying decision | sanitize locally and continue |
| `hard` | candidate is incomplete or contains an unsupported claim that warrants one bounded regeneration | regenerate under tighter semantic constraints |
| `critical` | candidate directly conflicts with a higher-authority source such as self-model, World Authority, or the resolved character decision | do not trust ordinary regeneration; fall back to minimum identity-safe expression |

Current critical examples include self-model conflicts, explicit World Authority conflicts, and `decision_reversal`, where the renderer explicitly offers to comply with conduct that the character core resolved as noncompliant.

Current hard examples include false-memory claims, unauthorized fabrication, unsupported claims about another person's private state, deception-ledger contradictions, and `decision_omission`, where a `decline` or `protect_boundary` response fails to express the resolved noncompliance at all.

Unsupported conversational absolutes such as `you always` and `you never` remain soft unless another authority layer escalates them.

## Retry and fallback policy

A hard `decision_omission` produces a machine-facing retry constraint such as `require:dialogue_act:decline`. This carries the already-resolved conduct into the one bounded retry rather than asking the model to reconsider the decision.

A critical `decision_reversal` does not enter an ordinary retry loop. The engine uses the established minimum-authority offline fallback because the candidate has directly contradicted character-owned decision authority.

Passing validation never gives renderer text canonical write authority.

## Compatibility status

`OutputValidator.check()` and `sanitize()` remain the production detector/sanitizer seam for pre-Wayfarer callers. `ConsistencyLayer` wraps those legacy checks and adds the typed behavioral realization contract rather than moving decision authority into `OutputValidator`.

The behavioral layer uses deterministic, conservative surface cues for the currently demonstrated refusal and boundary cases. It intentionally does not call a second LLM judge. A model-based evaluator may be useful in research evaluation, but it must not silently become a second hidden decision authority in production.

## Why this exists

The pre-Wayfarer regression where a test patched `generate()` while production had moved to `generate_expression()` demonstrated that an implicit assembly seam is too easy to break. The later external adversarial review exposed a second issue: internal semantic continuity can remain perfectly intact while an LLM says something that directly contradicts the resolved character decision.

A contributor changing renderer or validation behavior should be able to answer four concrete questions from types and tests alone:

1. What evidence was the consistency layer allowed to inspect?
2. What authority did each piece of that evidence have?
3. What conduct had the character already resolved before rendering?
4. What action did the layer take when the renderer omitted or reversed that conduct?

If those answers are not explicit, the change is incomplete.
