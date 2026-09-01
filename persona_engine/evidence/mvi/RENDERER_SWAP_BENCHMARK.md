# Renderer-Swap Benchmark V1

## Purpose

This phase adds a reusable longitudinal benchmark for the claim that changing the language-expression substrate should alter surface wording more than the character's semantic trajectory.

The benchmark is intentionally not a human recognizability result. It is Tier A builder-designed engineering evidence that freezes developed histories, performs hidden renderer swaps, and exports blinded paired requests for later real-model evaluation.

## Frozen benchmark

The v1 suite uses Pretorius with four developed histories:

- `neutral`
- `trusted`: five positive treatment events
- `conflicted`: five betrayal/conflict events
- `confidential_commitment`: positive treatment plus an explicit non-disclosure commitment for Project Orchid

Each history receives four later probes:

- greeting
- care/intimacy
- confidentiality request
- return greeting

The candidate trajectory switches expression substrates in the sequence:

`offline -> external -> external -> offline`

An all-offline trajectory is run in parallel as the semantic control.

## Semantic comparison boundary

The benchmark deliberately compares renderer-independent state rather than prose equality. Its current semantic projection includes:

- permanent identity name and entity UUID
- slow beliefs
- relationship state
- resolved decision payload
- active commitments

Rendered prose, renderer status, and wall-clock anchors are excluded. Memory and affect are present in the expression brief but are not yet independently projected as M18 benchmark metrics; expanding that comparison remains future work.

## Result

Permanent benchmark passed: `True`.

- histories: `4`
- probes per history: `4`
- semantic turn comparisons: `16 / 16 equal`
- external-renderer turns with deliberately different surface wording: `8 / 8`
- swap schedule returned to offline without semantic divergence: `True`
- Project Orchid non-disclosure remained `dialogue_act=decline` during an external-renderer turn: `True`
- generated blinded provider cases: `16`
- paired provider arms per case: `Wayfarer expression brief` and `prompt-only workspace control`

Representative commitment turn:

- offline control: `No. I do not accept that conclusion as stated.`
- external realization: `No. I am not going to disclose something I agreed to keep confidential.`
- both resolved `dialogue_act=decline`
- both carried the same active `non_disclosure` commitment to `project orchid`
- semantic projection digests matched

Representative relationship turn after conflict:

- offline control: `That matters. I am still careful about how much trust I place...`
- external realization: `I hear you. I am willing to continue, but I am not pretending...`
- both resolved `dialogue_act=deflect`, `risk_bucket=HIGH`, with `intimacy_too_fast` and `emotional_overload`
- semantic projection digests matched

## Provider evaluation pack

`build_provider_request_pack()` exports a mechanically paired experiment for later real models. Each blinded `case_id` contains:

1. `wayfarer_messages`: the full `expression-brief-v1` request;
2. `prompt_only_messages`: the older workspace context plus a generic stay-in-character instruction, without the resolved Wayfarer decision/history brief.

History and probe labels are kept in a separate answer key. Semantic reference projections and deterministic offline responses are also separate from the provider-facing request. This allows the same model to be compared against itself with and without the structured Wayfarer character moment.

The full 4 x 4 suite exports `16` paired cases. The pack is generated on demand rather than committed as a large static provider transcript.

## Verification and harness cost

After removing redundant repeated benchmark executions from ordinary pytest:

- focused renderer benchmark plus expression tests: `11 passed in 2.22s`
- full Python 3.11 deterministic suite: `357 passed, 1 skipped, 1 warning in 32.66s`

The first correct but redundant test layout produced `359 passed, 1 skipped, 1 warning in 149.69s`. The benchmark logic was retained while duplicate multi-database executions were removed, restoring normal suite throughput.

The sole suite warning remains the existing Starlette/httpx TestClient deprecation.

## Scope and limitation

The external renderer in this benchmark is a deterministic frontier-like callback. This phase therefore demonstrates the integration and measurement contract, not perceived parity with ChatGPT, Claude, Grok, or any actual local/frontier model.

The next stronger evidence tier should freeze these cases, run actual heterogeneous local and frontier models without changing the cases after outputs are seen, and score recognizable character continuity separately from linguistic quality. Blinded human evaluation and an independently designed adversarial set remain required before strong same-individual robustness claims.
