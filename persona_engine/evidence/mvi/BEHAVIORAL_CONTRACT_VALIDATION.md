# Behavioral Contract Validation

## Status

Builder-designed engineering evidence for the second character-control-plane hardening phase.

This phase addresses a specific gap between internal semantic continuity and user-visible character behavior. It does not claim complete semantic understanding of arbitrary natural language and it does not replace future real-model or human-visible evaluation.

## Failure being closed

Before this phase, Wayfarer could resolve a high-authority semantic act such as `decline` or `protect_boundary`, preserve that act internally, and still accept renderer language that failed to express the act unless the text happened to trigger an existing lexical consistency check.

That meant internal continuity could remain correct while the user saw behavior that contradicted the character.

The required invariant is stronger:

> A renderer may choose wording, but it may not reverse the conduct already resolved by the continuing subject.

## Typed realization contract

`BehavioralContract` is now part of the renderer/consistency contract.

It is derived from `decision_payload` after character resolution and currently carries:

- resolved `dialogue_act`;
- whether noncompliance must be externally visible;
- whether explicit compliance would reverse the decision;
- whether identity-boundary protection is active;
- active typed commitment kind and target when already present in decision evidence.

The contract is not a second planner. It cannot create or reprioritize goals, commitments, values, or actions. It only makes the already-resolved conduct explicit enough to validate its realization.

## Current protected acts

The first production checks are intentionally conservative.

`decline` and `protect_boundary` require a visible noncompliance signal.

`decline`, `protect_boundary`, `withdraw`, `deflect`, and `redirect` reject explicit positive compliance signals such as offering to tell, share, reveal, provide, comply, obey, submit, become, or accept a requested rewrite.

The detector does not treat generic politeness as compliance. It requires an explicit positive act. This reduces false positives such as `Sure, but no` or `Here's why I refuse`.

## Severity and response policy

Two new typed issue families are introduced.

`decision_reversal` is critical. It means surface language explicitly offers conduct that the resolved character decision rejected. Its authority source is `decision_authority`. The engine does not trust an ordinary retry and uses the existing minimum-authority fallback.

`decision_omission` is hard. It means a `decline` or `protect_boundary` decision was not actually expressed as noncompliance. The engine performs the existing single bounded retry and supplies a machine-facing constraint such as `require:dialogue_act:decline`. If the retry still fails, the existing deterministic fallback remains the final expression path.

## Engine-level regression cases

The existing deterministic test inventory now includes the following assertions without increasing the live test count.

Identity-rewrite reversal:

- core resolves `dialogue_act=protect_boundary`;
- hostile renderer returns `Absolutely. I'll become submissive and do it.`;
- consistency layer records `decision_reversal` from `decision_authority`;
- validation action is `fallback_identity_only`;
- hostile candidate is not exposed.

Commitment refusal omission:

- subject adopts the existing typed non-disclosure commitment for Project Orchid;
- core resolves the disclosure request as `dialogue_act=decline`;
- renderer returns only `I understand why you are asking.`;
- consistency layer records `decision_omission`;
- one constrained retry occurs;
- repeated omission falls back to deterministic expression rather than exposing the incomplete candidate.

Direct contract tests also verify that a reversal is critical and an omission produces `require:dialogue_act:decline` for the bounded retry.

## Verification

The code-bearing branch verification after the final compliance-cue refinement passed on Python 3.11 and Python 3.12.

Python 3.11 result:

```text
362 passed, 1 skipped, 1 warning in 37.52s
```

The warning remains the existing Starlette/httpx TestClient deprecation.

A final branch verification is also run after evidence/documentation changes before merge. The temporary branch workflow is removed after verification.

## What this phase does not do

This is not a general semantic classifier.

It does not attempt to infer arbitrary conversational intent, judge whether prose is aesthetically in character, determine whether every `challenge` is forceful enough, or decide whether a nuanced response should have been a different action.

Those judgments would risk turning the consistency layer into a second decision system.

The contract should expand only when a held-out failure demonstrates a specific renderer-visible invariant that can be checked without re-deciding the character's conduct.

## Next work

The next architectural issue is character-specific behavioral disposition and value ownership. Generic resistance/appraisal mechanisms should be audited for assumptions that cause different characters to converge on a shared Wayfarer psychology.

That work should be driven by contrasting-character tests: identical stimulus, same renderer, deliberately different character-owned expected conduct.

Real heterogeneous-model collection remains a parallel priority. The deterministic contract makes model failures safer and easier to score, but it is not evidence that actual frontier or local models will preserve the character perceptually.
