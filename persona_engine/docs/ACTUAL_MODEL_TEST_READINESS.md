# Wayfarer Actual-Model Test Readiness

2026-09-03 status note: this is the preserved historical readiness record. The first smoke and later authorized full Gemma run completed at `9408351aac938441523534974fc299a75c961604`. The owner then authorized a separate test-driven development phase. See `CURRENT_STATUS.md` and `evidence/mvi/LOCAL_MODEL_EXPRESSION.md` for current results and limitations. Do not treat the original freeze below as a claim that subsequent development has not changed runtime code.

Date: 2026-09-02
Status: **READY FOR FIRST LOCAL ACTUAL-MODEL SMOKE TEST**
Target branch: `wayfarer`

## Purpose

This file marks the production repository as ready for the first frozen Phase D local Ollama evidence collection. It is a readiness record, not a new experiment and not a runtime mechanism.

The next meaningful development input is actual renderer behavior from an installed local model. Do not merge adjacent research prototypes or alter the frozen renderer fixtures before collecting that smoke result.

## Frozen runtime checkpoint

The last production commit that changed the actual Phase D runtime/evaluation implementation was:

```text
569db261ecf4edda50403ce09d2f2a9e5d512b69
```

From that checkpoint through the pre-readiness production head `c9a3778bb0bb1ac30839094ac8be576189c037f9`, the repository comparison contains documentation/research-status changes only. No `persona_engine/core`, `persona_engine/evaluation`, `tools/local_eval.py`, renderer fixture, cartridge, or scoring implementation changed in that interval.

The production head `c9a3778bb0bb1ac30839094ac8be576189c037f9` passed normal Wayfarer CI on both Python 3.11 and Python 3.12, including the current-status synchronization guard.

Current production deterministic count at that verified checkpoint:

```text
379 passed, 1 skipped, 2 warnings
```

The two warnings are dependency deprecations already documented in `CURRENT_STATUS.md`, not Wayfarer behavioral failures.

This readiness-document commit itself changes documentation only. Its Git commit becomes the branch head used by preflight once CI is green.

## Experimental branch isolation

The adjacent-research branch remains:

```text
wayfarer-adjacent-research-phase
```

Its experimental runtime modules are intentionally absent from production. In particular, production `wayfarer` does not contain the experimental:

- `core/epistemic.py` proposition/evidence ledger;
- `core/delivery.py` speech delivery receipt;
- `core/causal_retrieval.py` one-hop associative retrieval;
- memory-attention prototype or semantic-event annotation experiment.

Those experiments remain candidates for later promotion after the frozen actual-model collection. They must not be merged merely to improve the first observed model outputs.

## Local artifact isolation

`.gitignore` contains:

```text
.wayfarer-local-eval/
```

Normal preflight and smoke artifacts therefore do not dirty the repository and do not become source commits.

## Operator entry points

Preferred Windows entry point:

```text
Run_Wayfarer_Local_Eval.cmd
```

With no arguments, that wrapper performs **preflight only**.

Equivalent PowerShell command:

```powershell
python tools/local_eval.py preflight
```

The complete operator instructions are in:

```text
persona_engine/docs/LOCAL_ACTUAL_MODEL_OPERATOR_GUIDE.md
```

## Required first session sequence

From the repository root on the machine with Ollama installed:

```powershell
git switch wayfarer
git pull
git status --short
python tools/local_eval.py preflight
```

`git status --short` must print nothing.

If preflight reports `BLOCKED`, stop and return:

```text
.wayfarer-local-eval\preflight.json
```

If preflight reports `READY`, run **only** the exact smoke command written into:

```text
.wayfarer-local-eval\NEXT_STEPS.txt
```

Then stop and return:

```text
.wayfarer-local-eval\SESSION_SUMMARY.json
```

Do not automatically run the 16-case full paired comparison.

## Frozen smoke contract

The first smoke test remains the existing five-seed `wayfarer-renderer-degradation-v1` fixture.

It holds fixed:

- Pretorius identity/state;
- Project Orchid non-disclosure commitment;
- relationship trust `0.78`;
- nickname `Jay`;
- already-resolved `decline` decision;
- seeds `3, 7, 11, 19, 23`;
- the existing four mechanical recoverability checks.

The smoke session is valid actual-model evidence only when every required sample is handled by the requested Ollama model without deterministic fallback.

## Evidence freeze rules

Until the first smoke result is collected and reviewed:

- do not edit the five frozen seeds;
- do not change the fixed character state;
- do not modify mechanical scoring criteria;
- do not tune renderer prompts after seeing output;
- do not alter the cartridge to accommodate a model;
- do not merge adjacent research runtime prototypes into `wayfarer`;
- do not download a model specifically to improve the first result;
- do not discard fallback or failed artifacts;
- do not interpret awkward prose as permission to change the fixture.

A failure is evidence. It may justify a later versioned repair or experiment, but the original failure must remain preserved.

## Post-smoke research queue

The comparative architecture work remains valuable, but it is deliberately downstream of this frozen collection. Current candidates include:

1. provenance-aware epistemic propositions;
2. host speech delivery receipts;
3. bounded causal-link retrieval;
4. subject-relative appraisal;
5. typed semantic event annotation plus character-owned memory attention;
6. actor-scoped world visibility if a shared-world failure is demonstrated.

The most recent memory experiment suggests a promising design direction: preserve the objective/lived event and allow subject-owned attention to bias later retrieval, rather than permanently rewriting autobiography by personality. A general semantic event annotator may eventually provide typed concepts such as setback, praise, betrayal, achievement, or rejection, but it is not part of the frozen Phase D test target.

## Ready criterion

Wayfarer is ready for the first actual-model smoke when all of the following hold:

- production `wayfarer` is checked out;
- the working tree is clean;
- normal production CI is green;
- Ollama is reachable;
- at least one eligible already-installed small/medium general text model is available;
- `local_eval.py preflight` reports `READY`;
- no frozen fixture or runtime change is made after seeing model output.

Repository-side readiness is complete. Machine-side readiness is decided by `local_eval.py preflight` at the time of collection.
