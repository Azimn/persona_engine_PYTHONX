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

### Bounded causal associative retrieval

Status: **isolated one-hop retrieval contract verified; link-production policy not yet justified**

The continuity schema already contains `causal_parents`, and persistence already stores, transfers, and reloads those links. Resident memory and cold-biography retrieval currently use semantic/topical relevance and do not traverse canonical causal links. The normal `InteriorEngine` also does not populate causal parents during ordinary turn writes.

The experimental `core/causal_retrieval.py` therefore tests only whether Wayfarer can reuse links it already owns as a bounded retrieval primitive. It does not infer new associations.

V1 guarantees:

- one-hop traversal only;
- direct parent and direct child recovery;
- same-subject filtering;
- canonical-event filtering;
- deterministic bounded output;
- no graph database;
- no recursive spreading activation;
- no resident-memory promotion;
- no authority mutation.

Verified checkpoint after adding this prototype:

```text
Python 3.11 focused adjacent tests: 18 passed
Python 3.12 focused adjacent tests: 18 passed
Python 3.11 full experimental suite: 397 passed, 1 skipped, 2 warnings
Python 3.12 full experimental suite: 397 passed, 1 skipped, 2 warnings
```

Evidence on the experimental branch:

- `persona_engine/core/causal_retrieval.py`
- `persona_engine/tests/test_causal_retrieval.py`
- `persona_engine/evidence/mvi/CAUSAL_ASSOCIATIVE_RETRIEVAL_PROTOTYPE.md`

Next gate: freeze a longitudinal counterexample in which ordinary semantic retrieval misses behaviorally relevant evidence but a previously authorized causal link recovers it. Only then decide whether production should create causal links, and at which authority boundary. Renderer text must not be allowed to invent causal parents.

### Witness / point-of-view scope

Status: **existing architecture covers the single-subject case; possible multi-subject gap identified; no code added**

Source inspection showed that Wayfarer already separates objective world truth from character-visible context. `WorldFact.visible_to_character` controls whether a fact enters the subject-visible projection, sensor observations pass through World Authority, and subjective interpretation reads visible sources rather than hidden server truth.

A separate witness-memory subsystem would therefore duplicate existing authority boundaries.

The narrower unresolved issue is multi-subject visibility. `WorldFact.visible_to_character` is currently a single boolean, and `WorldAuthority.get_visible_context(actor_id)` accepts an actor identifier but does not use it to filter facts. That is sufficient for the current single-subject host profile but may be insufficient if a future Society Lab or shared-world host uses one World Authority for multiple subjects with different observations.

Evidence on the experimental branch:

- `persona_engine/evidence/mvi/WITNESS_SCOPE_GAP.md`

Next gate: demonstrate an actual shared-world failure where subject A witnesses an event, subject B does not, and B nevertheless receives the event through the current visibility projection. If that occurs, extend World Authority minimally with actor-scoped visibility or observation receipts rather than creating another memory store.

### Character-relative autobiographical encoding

Status: **write-time convergence demonstrated; no subjective encoding mechanism implemented**

Wayfarer already allows characters to diverge after an event through relationship state, pressures, behavioral dispositions, private cognition, retrieval, decision constraints, and rendering. The ordinary autobiographical write itself is narrower. `InteriorEngine._post_speech_update` constructs `USER_TOLD` memories from the incoming event, appraisal/risk values, and identity-violation status; it does not consult cartridge temperament, values, goals, cognitive themes, or a character-owned encoding profile. `private_cognition.validate_and_apply` explicitly does not mutate memory.

The experimental `memory-encoding-subjectivity-baseline-v1` sends the same neutral event to Friendly, Pretorius, and Rival:

```text
I found a small silver locket in the hallway.
```

All three stored the same typed autobiographical signature, excluding generated IDs and timestamps:

```text
case_count = 3
unique_memory_signatures = 1
all_memory_signatures_identical = true
character_profile_is_encoding_input = false
```

The shared record was `I heard you say: I found a small silver locket in the hallway.` with emotional intensity `0.0`, valence `0.2`, identity relevance `0.2`, relationship relevance `0.6`, source `user_told`, and the generic `canonical_user_statement` tag. This remained identical for Friendly (`Warm, patient, grounded`), Pretorius (`Melancholic and defensive`), and Rival (`Competitive, sharp, unsentimental`). The baseline and the complete experimental workflow passed on Python 3.11 and 3.12. The experimental suite remained `397 passed, 1 skipped, 2 warnings` on each runtime.

Evidence on the experimental branch:

- `persona_engine/evaluation/memory_encoding_subjectivity.py`
- `persona_engine/evidence/mvi/MEMORY_ENCODING_SUBJECTIVITY_GAP.md`

This result establishes a representation fact, not a defect by itself. Different characters may already diverge sufficiently through later appraisal, retrieval, cognition, and decision layers. A personality-conditioned encoder would therefore be premature.

Next gate: freeze a longitudinal case in which two contrasting subjects experience the same event, substantial unrelated interference follows, and current later behavior converges because the original record preserved no subject-relative salience or interpretation. Only if that behavioral failure appears should the smallest subject-relative encoding projection be tested. The immutable experience must remain separate from any revisable interpretation or salience annotation.

## Deliberately not implemented yet

Subject-relative appraisal has a demonstrated gap but no replacement subsystem. Character-relative autobiographical encoding now has a demonstrated write-time convergence baseline but no demonstrated longitudinal behavioral failure. Witness scope has a plausible multi-subject limitation but no demonstrated shared-world failure. Causal associative retrieval has a verified read-only primitive but no production link-creation policy.

The current work does not justify adding a graph database, a general OCEAN/Big Five runtime, a large cognitive stack, many new affect variables, per-actor visibility ACL machinery before a shared-world failure exists, recursive spreading activation, personality-weighted memory rewriting, or automatic persona rewriting.

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
