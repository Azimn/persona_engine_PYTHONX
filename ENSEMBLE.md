# Project Ensemble

Status: active experimental successor line to Project Wayfarer

Primary branch: `ensemble`

Parent checkpoint: `wayfarer-local-model-hardening` at `76e054d9c232d55c0163cfd5816fa527033c62c2`

## Current verified checkpoint

Verified code checkpoint: `29a6d29c19ed1d5c530513629cbaa1846ff444fa`

GitHub Actions run: `33778972790`

GitHub Actions is green on Python 3.11 and 3.12.

Python 3.11 verification at this checkpoint:

```text
Full deterministic suite: 466 passed, 1 skipped, 2 dependency warnings
Focused Ensemble architecture suite: 60 passed
Ensemble evaluation entry points: passed
Deterministic offline Scene Lab scenario: passed
```

The two warnings are existing FastAPI/Starlette/anyio dependency deprecations, not behavioral failures.

The durable evidence record for this checkpoint is:

`persona_engine/evidence/mvi/ENSEMBLE_CAUSAL_ARCHITECTURE_CHECKPOINT.md`

## Core research position

Project Ensemble preserves the strongest result from Wayfarer: the language model should not own the simulated individual.

Identity, canonical biography, memory provenance, relationships, commitments, authored values, world truth and final semantic decisions remain outside the model.

Ensemble broadens the other side of that design. A strong language model should be allowed to do the things it is unusually good at: interpret context, improvise, choose wording, vary syntax and rhythm, make local conversational connections, ask a natural question, use metaphor, and realize the same character moment in many different ways.

The working metaphor is:

> The LLM is an organ, not the organism.

The aim is not to constrain the language model into a template engine. The aim is to prevent known model weaknesses from becoming the authority that defines the person.

## Current architecture

```text
                         PERSISTENT SUBJECT
                                |
       identity / history / relationships / commitments
                                |
            +-------------------+-------------------+
            |                                       |
     semantic event                           conversational turn
            |                                       |
    typed event annotation                    current character state
            |                                       |
    subject-relative appraisal                 resolved decision
            |                                       |
     memory salience / pressure                ExpressionRequest
            |                                       |
            +-------------------+         character-owned agenda
                                |                 |
                                |       +---------+---------+
                                |       |         |         |
                                |    direct   contextual initiative
                                |       |         |         |
                                |       +---------+---------+
                                |                 |
                                |       sparse authored landmarks
                                |                 |
                                |          CANDIDATE ECOLOGY
                                |                 |
                                |       live engine-authority gate
                                |                 |
                                |       surface-diversity ranking
                                |                 |
                                |          selected speech
                                |                 |
                                |       engine consistency re-check
                                |                 |
                                |        intended expression
                                |                 |
                                |        host/world delivery
                                |                 |
                                |          delivery receipt
                                |                 |
                                +------ lived delivery memory
```

A second evidence path now separates:

```text
testimony / observation / world authority / model inference
                         |
                 epistemic evidence
                         |
                 explicit revision
                         |
              UUID-scoped subject belief
                         |
             topic-relevant projection
                         |
          noncanonical interpretation
```

The candidate pool is noncanonical. A candidate can be generated, rejected or forgotten without rewriting the subject.

## Implemented components

### 1. Multi-candidate realization

`persona_engine/core/ensemble_renderer.py`

`EnsembleLLMRenderer` generates several performances of the same immutable `ExpressionRequest`. The default is three model candidates with deterministic seed separation.

The original `LocalLLMRenderer` remains available as the single-shot control.

### 2. Distinct performance modes

The three default model candidates are not merely seed variations.

They rotate through:

- `direct`: fresh, specific realization of the current act;
- `contextual`: may let relationship, affect, habit, shared symbols and unresolved threads shape emphasis;
- `initiative`: may contribute one short question, observation or topic connection when a character-owned agenda actually supports initiative.

All three still receive the same decision and evidence authority.

### 3. Live engine-authority candidate admission

`persona_engine/core/ensemble_validation.py`

`persona_engine/core/ensemble_engine_gate.py`

Normal `CharacterAgent` integration now binds `EnsembleLLMRenderer` to the live `InteriorEngine` before candidate generation begins.

The model may generate expressive possibilities, but the renderer does not decide which possibilities are semantically admissible. Each candidate is evaluated before diversity ranking with the current engine's:

- forbidden self claims;
- resolved semantic decision;
- selected memory evidence;
- recall contract;
- current interpretation state;
- world state;
- deception ledger.

Hard and critical candidates are excluded before surface ranking. Examples include:

- decision reversal;
- unsupported confident claims about the user's private mental state;
- forbidden self-model claims;
- unsupported or contradictory recall;
- failure to preserve a required refusal or boundary.

Soft sanitizer repairs may survive as repaired candidates.

A regression deliberately omits a forbidden self claim from the renderer-side `ExpressionRequest` and submits a candidate containing that claim. It is still rejected because the gate obtains the constraint from the live subject authority.

Standalone renderer and evaluation-tool use remains portable. Without a live engine binding, candidate validation falls back to request reconstruction. Runtime status and candidate traces identify which authority path was used.

The final engine consistency pass remains in place after selection. Candidate admission does not replace it.

### 4. Sparse authored landmark candidates

Authored relationship examples selected upstream from typed act/stance context are no longer shown to V3 model prompts as sentences to imitate.

In Ensemble they may instead enter the candidate ecology as `AUTHORED` candidates.

They are peers, not automatic winners. They pass the same candidate authority gate as model output and then compete with surviving model candidates.

This preserves the strongest lesson from legacy conversational systems without returning to giant response banks.

### 5. Noncanonical surface memory

`persona_engine/core/ensemble_realization.py`

A small recent-surface window supports anti-repetition ranking. Current penalties include:

- exact duplicate wording;
- normalized duplicates;
- high textual similarity;
- repeated openings;
- repeated five-word phrases.

This cache is expression state, not biography. Losing it can reduce variety but cannot alter identity or history.

### 6. Character-owned conversational agenda

`persona_engine/core/conversational_agenda.py`

The agenda projects already-owned subject state into an inspectable reason for conversational initiative.

Current sources include:

- selected intention;
- unresolved open loop;
- shared symbol;
- active habit;
- relationship familiarity and attachment;
- guardedness;
- tension when unresolved business already exists.

The result includes an explicit `initiative_pressure` and `initiative_allowed` flag.

There is deliberately no reward for conversation length, retention, engagement or eliciting another response.

The agenda is currently rebuildable projection state rather than a separate persistence authority.

### 7. Typed subject-relative appraisal with causal memory effects

`persona_engine/core/subject_appraisal.py`

`CharacterAgent.observe_semantic_event(...)`

Ensemble separates:

```text
what happened
    from
what this event means to this subject
```

`SemanticEventAnnotation` contains bounded event features. `SubjectAppraisalContext` contains current character-owned sensitivities. The resulting `SubjectRelativeAppraisal` includes:

- goal relevance;
- relationship relevance;
- identity relevance;
- controllability;
- threat/opportunity direction;
- uncertainty;
- salience;
- social meaning;
- provenance.

This is a causal path rather than a representation-only experiment. A host can submit a typed semantic event through the public agent API. The subject's current relationship and explicit goal preference determine appraisal, which then changes:

- episodic memory emotional valence;
- emotional intensity;
- relationship relevance;
- identity relevance;
- unresolved status;
- bounded existing pressure vessels.

The same cancellation event is regression-tested to leave an unresolved negative relational memory with fear in one subject context and a positive relief-oriented trace with curiosity in another. The source event remains identical in both cases. The resulting memory survives restart.

The typed path does not replace the older lexical interaction-signal appraisal. It is an additional explicit host/sensor semantic path.

### 8. Provenance-aware subject epistemics

`persona_engine/core/epistemic.py`

`CharacterAgent.record_epistemic_evidence(...)`

`CharacterAgent.revise_belief(...)`

`CharacterAgent.epistemic_state(...)`

Ensemble explicitly distinguishes:

- evidence that somebody told the subject X;
- direct observation relevant to X;
- world-authority evidence about X;
- model or self inference about X;
- the subject's current stance toward X.

`EpistemicStance` supports:

- `UNKNOWN`;
- `TENTATIVE`;
- `BELIEVED`;
- `DISBELIEVED`.

Evidence is append-only. Recording testimony does not automatically create belief or world truth. Non-unknown revision requires explicit evidence references. Cross-proposition evidence fails closed. Corrections can change the current stance without rewriting the original evidence. Model inference retains its source class and uncertainty after serialization.

The epistemic ledger is persisted through UUID-scoped `subject_state`. Regression coverage verifies:

- same-stream restart persistence;
- continuity across different interlocutor `user_id` streams for the same permanent subject UUID;
- correction without evidence erasure;
- testimony without explicit revision remains `UNKNOWN`;
- model inference or testimony does not create a world-authority proposition.

This closes the gap between “I remember being told X” and “I believe X” while keeping both separate from “X is objectively true.”

A dedicated canonical event-replay schema for epistemic revisions remains a future durability question. Current evidence demonstrates subject-scoped snapshot persistence, not independent event-log reconstruction of the ledger.

### 9. Subject belief as a bounded interpretation prior

`persona_engine/core/interpretation.py`

Settled subject beliefs can now affect turn-level interpretation without becoming environment truth.

`CharacterAgent` binds a read-only epistemic provider to `InterpretationEngine`. Non-UNKNOWN propositions are exposed as a distinct `subject_epistemic` source family containing the proposition text, stance, confidence and evidence references.

A subject prior is admitted only when it is lexically relevant to the current visible topic. The resulting interpretive belief:

- remains `canonical=False`;
- carries `subject_epistemic:<proposition_key>` provenance;
- carries the subject's proposition confidence;
- survives restart and interlocutor change because its source ledger belongs to the subject UUID;
- does not activate on unrelated topics;
- does not activate when testimony exists but no explicit belief revision has occurred;
- does not create a corresponding `WorldAuthority` proposition.

An ordinary turn may record the current `user_text` as hidden input evidence in World Authority. That is distinct from promoting the subject's belief into objective truth.

This gives lived belief a causal route into reasoning while preserving the fact/belief boundary.

### 10. Speech delivery receipts and lived delivery consequence

`persona_engine/core/delivery.py`

`CharacterAgent.record_delivery_receipt(...)`

Ensemble distinguishes generated/intended speech from what actually happened in the host environment.

V1 records:

- fully delivered speech;
- prefix/partial delivery;
- no delivery.

A failed delivery stores the intended text digest and length but not the undelivered plaintext.

Delivery is connected to the continuing subject. A host receipt becomes episodic evidence of what the subject actually managed to say. Partial or failed delivery becomes unresolved lived experience and can add bounded startle pressure.

An interrupted sentence is regression-tested across restart so the subject retains the delivered prefix and interruption while the undelivered remainder is absent from that lived memory.

The core renderer's original full response remains only noncanonical speech evidence in the diagnostic event stream.

### 11. Scene Lab

`persona_engine/evaluation/scene_lab.py`

Scene Lab is an implemented sibling host environment.

It supports:

- named actors;
- locations and movement;
- actor presence;
- public and actor-specific facts;
- complete server truth separated from character-visible context;
- recent scene events;
- spoken input;
- full or interrupted output delivery;
- speech delivery receipts;
- automatic delivery writeback to real `CharacterAgent` subjects;
- execution through the normal public `CharacterAgent.say()` API.

A character can therefore be interrupted and subsequently possess a different lived speech history than the original renderer intention.

### 12. Public Ensemble activation and evaluation tools

`CharacterAgent.use_ensemble_renderer(...)` enables the Ensemble Ollama path through the public agent API and automatically binds live engine candidate authority.

`CharacterAgent.set_renderer(...)` remains a generic host seam and binds the same authority gate when the renderer supports candidate evaluation.

`tools/run_ensemble_scene_lab.py` runs a three-turn situated scene with Pretorius, Jay and a Rival actor. With no model argument it runs deterministically offline; with `--model` it activates the public Ensemble Ollama renderer.

`tools/ensemble_relationship_probe.py` runs the matched-history relationship expression experiment with the Ensemble renderer.

`tools/compare_ensemble_reports.py` compares matched single-shot and Ensemble report artifacts and measures:

- exact duplicate rate;
- normalized duplicate rate;
- repeated openings;
- output length;
- narrow predeclared symptoms;
- provider/fallback counts;
- candidate survival;
- prevalidation rejection count;
- selected candidate source;
- selected performance mode;
- initiative availability;
- matched output changes;
- symptom improvements/regressions.

These surface metrics are not treated as proof of identity fidelity.

## Authority matrix

### The model may propose or vary

- wording;
- syntax;
- metaphor;
- pacing;
- local elaboration;
- conversational connection;
- tentative interpretation;
- questions and observations supported by the current agenda;
- stylistic realization consistent with the character.

### The model may not canonically decide

- who the character is;
- what actually happened;
- which memory is true;
- whether a user statement is world truth;
- what the subject currently believes without an explicit epistemic revision path;
- relationship state;
- active commitments;
- authored values;
- protected disclosures;
- world-authority facts;
- final semantic conduct.

A model proposal can influence later character state only through an explicit validated causal path.

## Current research questions

The central question is now broader than renderer substitution:

> How much semantic and conversational freedom can a replaceable language model be given while a persistent external subject still preserves identity, lived history, authority boundaries and recognizable development across model changes and environments?

Supporting questions:

1. Does candidate ecology reduce model-specific repetition and stiffness without increasing semantic drift?
2. Do direct/contextual/initiative modes improve naturalness and character distinction compared with single-shot generation?
3. When do sparse authored landmark candidates outperform model realization, and when should they lose?
4. Does character-owned agenda pressure create believable initiative without becoming engagement optimization?
5. Which typed appraisal dimensions continue to matter under actual model interaction and situated scenes?
6. How should subject belief update when testimony, observation and world authority conflict over longer histories?
7. Does delivery-aware lived history materially change later recall, relationship and action after interruptions or failed speech?
8. Does the same subject feel more coherent and alive in Scene Lab than in isolated chat?
9. Which mechanisms survive cross-model and cross-character ablation?

## Immediate frontier: return to empirical testing

The basic causal mechanisms are now implemented and compose under deterministic tests. The next step is not another speculative architecture layer.

### A. Matched actual-model collection

When the local Ollama environment is available, run matched single-shot and Ensemble collections with already-installed Qwen/Gemma-class general models.

Measure at minimum:

- exact and normalized repetition;
- recurring openings and phrases;
- candidate rejection/survival;
- selected source and performance mode;
- initiative use;
- semantic validation failures;
- model fallback;
- relationship-language differentiation;
- behavior/decision preservation.

Freeze the raw artifacts before changing mechanisms.

### B. Cross-model continuity

After one model path is stable, repeat matched histories across heterogeneous installed models while holding the external subject state fixed.

Score persona enactment separately from accumulated-history correctness. Do not collapse those into one identity metric.

### C. Situated Scene Lab collection

Use the same subject in bounded scenes involving:

- actor arrival/departure;
- hidden information;
- interruptions;
- conflicting testimony;
- corrections;
- unresolved plans;
- relationship-relevant events.

Observe whether the existing appraisal, epistemic, agenda and delivery mechanisms produce useful later behavior before adding new state.

### D. Human evaluation

Once real-model artifacts exist, use paired/blinded human comparisons for recognizable identity, naturalness, initiative, continuity and contextual appropriateness.

### E. Only then promote another mechanism

Candidate next mechanisms are evidence-dependent, not scheduled:

- dedicated canonical event replay for epistemic revision;
- recipient-side relationship consequence based on delivered speech;
- additional subject-relative appraisal consumers;
- persistent agenda fields;
- associative retrieval beyond current bounded recall.

Add one only if the model or Scene Lab collections demonstrate a failure that the existing architecture cannot produce or preserve.

The target is not maximal textual variation.

The target is:

> more expressive possibility, more initiative and more situated causal behavior with equal or better subject continuity.

## Relationship to Wayfarer

Do not rewrite Wayfarer history.

Wayfarer remains the control-plane research line and a useful comparison condition. Ensemble is intentionally freer and more synthetic: it inherits Wayfarer's authority boundaries while testing candidate ecology, initiative, subject-relative experience, explicit epistemics, situated interaction and richer model participation.

If Ensemble ultimately wins the comparative evidence, validated mechanisms can be folded into `main`. If it fails, the Wayfarer line remains intact.
