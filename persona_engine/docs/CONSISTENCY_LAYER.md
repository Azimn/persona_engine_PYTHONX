# Wayfarer Consistency Layer Contract

This document freezes the interface between character resolution, renderer output, and pre-exposure validation.

The consistency layer is not a second planner. It does not decide what the character wants to say. It evaluates whether a renderer's candidate text faithfully realizes a decision that already exists.

## Normative input

`ValidationRequest` is the contract.

It contains:

- `candidate_text`: renderer output. This is always noncanonical until accepted.
- `identity_constraints`: character-owned self-model restrictions. These have higher authority than renderer text.
- `interpretive_state`: current noncanonical subjective readings. These may guide consistency checks but do not become world truth.
- `relevant_history`: only memories selected by the character core. The validator does not independently retrieve history.
- `decision_payload`: the already-resolved dialogue/action intent that the candidate is supposed to realize.
- `canonical_context`: explicit high-authority constraints supplied by World Authority or another canonical owner.
- `authorization`: bounded deception/fabrication authority where a scenario explicitly permits it.
- `deception_ledger`: existing consistency obligations created by prior authorized deception.

The validator may not invent additional identity rules, world facts, memories, or goals.

## Normative output

`ValidationResult` contains the original candidate, the currently usable output text, typed issues, and a recommended action.

Severity is explicit:

| Severity | Meaning | Default action |
|---|---|---|
| `soft` | wording wobble that does not invalidate the underlying decision | sanitize locally and continue |
| `hard` | candidate makes an unsupported claim that should not be repaired by casual string substitution | regenerate under tighter semantic constraints |
| `critical` | candidate conflicts with a higher-authority source such as self-model or World Authority | do not trust ordinary regeneration; fall back to minimum identity-safe expression |

Initial code classification is deliberately conservative.

Critical examples include self-model conflicts and explicit World Authority conflicts. Hard examples include false-memory claims, unauthorized fabrication, unsupported claims about another person's private state, and deception-ledger contradictions. Unsupported conversational absolutes such as `you always` / `you never` are soft unless another authority layer escalates them.

## Compatibility status

`OutputValidator.check()` and `sanitize()` remain the production detector/sanitizer seam for pre-Wayfarer callers. `ConsistencyLayer` wraps those methods in the typed contract rather than duplicating their detection logic.

This phase deliberately freezes the interface before changing the engine's response policy. The next engine integration may consume `ValidationAction` to perform a single constrained retry or minimum-authority fallback. That integration must preserve the rule that renderer text never writes canonical state merely because it passed validation.

## Why this exists

The pre-Wayfarer regression where a test patched `generate()` while production had moved to `generate_expression()` demonstrated that an implicit assembly seam is too easy to break. From this point forward, a contributor changing renderer or validation behavior should be able to answer three concrete questions from types and tests alone:

1. What evidence was the consistency layer allowed to inspect?
2. What authority did each piece of that evidence have?
3. What action did the layer recommend for the detected problem?

If those answers are not explicit, the change is incomplete.
