# Adjacent Research Experiment Status

Date: 2026-09-02
Production branch: `wayfarer`
Experimental branch: `wayfarer-adjacent-research-phase`

## Why this file exists

`ADJACENT_CHARACTER_ARCHITECTURES_2026-09-02.md` identified several mechanisms from current character-agent, memory, appraisal, game-agent, and companion research that might transfer cleanly to Wayfarer.

Rather than merge those ideas directly into the character kernel, Wayfarer is applying the normal minimum-mechanism discipline: freeze the current production evidence, isolate candidate representations, test their authority semantics, and promote only mechanisms that later demonstrate a missing longitudinal behavior.

The first actual-model Phase D renderer collection remains frozen against the current production runtime. The experiments below are **not** merged into the production turn loop.

## Experimental branch status

### Epistemic proposition/evidence representation

Status: **isolated representation verified; production integration not justified yet**

The experimental `core/epistemic.py` fills a specific ownership gap between experience memory, turn-local interpretation, slow cartridge-defined developmental beliefs, and objective World Authority.

It can separately represent:

- evidence that Alice told the subject X;
- a current subject-owned stance toward X;
- later contradictory/corrective evidence;
- a causal revision certificate;
- deterministic first-person status derived from typed state.

Recording testimony does not automatically create a belief and does not create objective world truth. A current stance requires an explicit typed revision citing evidence for the same proposition.

Verified isolated checkpoint:

```text
Python 3.11 focused epistemic tests: 6 passed
Python 3.12 focused epistemic tests: 6 passed
Python 3.11 full experimental suite: 385 passed, 1 skipped, 1 warning
Python 3.12 full experimental suite: 385 passed, 1 skipped, 1 warning
```

Evidence and design on the experimental branch:

- `persona_engine/docs/EPISTEMIC_PROPOSITION_EXPERIMENT.md`
- `persona_engine/evidence/mvi/EPISTEMIC_PROPOSITION_GAP.md`
- `persona_engine/evidence/mvi/EPISTEMIC_PROPOSITION_PROTOTYPE.md`

Next gate: causal integration/replay with explicit typed semantic input. Do not add automatic free-form proposition extraction or universal testimony weighting merely because the representation exists.

### Speech delivery receipt

Status: **isolated host-boundary contract verified; production integration not justified yet**

The experimental `core/delivery.py` distinguishes renderer-generated intended speech from what a host actually delivered.

V1 supports:

- exact full delivery;
- interrupted strict-prefix delivery;
- complete delivery failure.

The receipt stores only delivered text plus a SHA-256 digest and length for the intended utterance. When nothing was delivered, a protected value present in generated text is not copied into the serialized delivery receipt.

Combined adjacent-prototype checkpoint:

```text
Python 3.11 focused adjacent tests: 12 passed
Python 3.12 focused adjacent tests: 12 passed
Python 3.11 full experimental suite: 391 passed, 1 skipped, 1 warning
Python 3.12 full experimental suite: 391 passed, 1 skipped, 1 warning
```

Evidence and design on the experimental branch:

- `persona_engine/docs/SPEECH_DELIVERY_RECEIPT_EXPERIMENT.md`
- `persona_engine/evidence/mvi/SPEECH_DELIVERY_RECEIPT_PROTOTYPE.md`

Next gate: explicit host acknowledgement plus canonical replay. Renderer output that was never delivered must not become evidence that the interlocutor heard it.

### Subject-relative appraisal

Status: **gap demonstrated; no new appraisal subsystem implemented**

The literature review initially suggested appraisal as a potentially important missing mechanism. Source inspection showed that Wayfarer already has a deterministic appraisal stage in `core/relationship.py`.

The existing layer identifies interaction signals such as accusation, threat, repair, intimacy, boundary violation, manipulation, contradiction, and disrespect. It should therefore not be replaced merely to imitate another cognitive architecture.

The narrower gap is that `appraise_event(text)` receives only the event text. It cannot condition the meaning of an event on the particular subject's current relationship, goal, values, identity relevance, or intentions.

An experimental baseline holds one cancellation event constant while varying three very different subject contexts. The workflow asserts:

```text
case_count = 3
unique_appraisal_count = 1
all_appraisals_identical = true
subject_context_is_input = false
```

The baseline step passed on Python 3.11 and 3.12. This proves only that the current upstream appraisal is context-invariant with respect to subject state. It does not prescribe what the correct emotional meaning of cancellation should be.

Evidence on the experimental branch:

- `persona_engine/evaluation/appraisal_subjectivity.py`
- `persona_engine/evidence/mvi/APPRAISAL_SUBJECTIVITY_GAP.md`

Next gate: demonstrate a downstream behavior that requires subject-relative appraisal. If earned, preserve the existing interaction-signal detector and add only the minimum second-stage subject meaning needed to produce the missing behavior.

## Deliberately not implemented yet

The comparative review also identified potentially useful future tests for character-mediated subjective memory encoding, bounded associative retrieval over existing causal links, and witness/POV scope.

Those remain research candidates rather than code. The current work does not justify adding a graph database, a general OCEAN/Big Five runtime, a large cognitive stack, many new affect variables, or automatic persona rewriting.

## Promotion rule

A green isolated data structure is not enough for production adoption.

A candidate mechanism should move into `wayfarer` runtime only when:

1. a frozen baseline demonstrates a behavior the current production system cannot produce or preserve;
2. the candidate fixes that behavior with a smaller or comparably simple mechanism than plausible alternatives;
3. authority and replay semantics are explicit;
4. resident-state/resource cost is measured where relevant;
5. relevant deterministic tests and cross-version CI are green;
6. the pending renderer/model evidence is not retrospectively contaminated;
7. repository evidence and status documentation state exactly what was and was not demonstrated.

This preserves Wayfarer's central research discipline: external ideas are inputs to experiments, not reasons to accumulate architecture.
