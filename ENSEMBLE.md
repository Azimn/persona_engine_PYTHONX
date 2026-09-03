# Project Ensemble

Status: active experimental successor line to Project Wayfarer

Primary branch: `ensemble`

Parent checkpoint: `wayfarer-local-model-hardening` at `76e054d9c232d55c0163cfd5816fa527033c62c2`

## Current verified checkpoint

Verified code checkpoint: `7fe01fb55fa358e1bf9a46ecace005d24cfc01f0`

GitHub Actions is green on Python 3.11 and 3.12.

Python 3.11 verification at this checkpoint:

```text
Full deterministic suite: 455 passed, 1 skipped, 2 dependency warnings
Focused Ensemble architecture suite: 49 passed
Ensemble CLI entry points: passed
Deterministic offline Scene Lab scenario: passed
```

The two warnings are existing FastAPI/Starlette/anyio dependency deprecations, not behavioral failures.

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
                 identity / history / relationships
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
                                |       deterministic prevalidation
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
              current subject belief
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

### 3. Candidate prevalidation before ranking

`persona_engine/core/ensemble_validation.py`

Every candidate can be evaluated using the same deterministic `ConsistencyLayer` contracts used by the engine.

Hard and critical candidates are excluded before surface ranking. Examples include:

- decision reversal;
- unsupported confident claims about the user's private mental state;
- forbidden self-model claims;
- unsupported or contradictory recall;
- failure to preserve a required refusal or boundary.

Soft sanitizer repairs may survive as repaired candidates.

The final engine consistency pass remains in place after selection. Prevalidation does not replace it.

### 4. Sparse authored landmark candidates

Authored relationship examples selected upstream from typed act/stance context are no longer shown to V3 model prompts as sentences to imitate.

In Ensemble they may instead enter the candidate ecology as `AUTHORED` candidates.

They are peers, not automatic winners. They pass the same deterministic candidate validation as model output and then compete with surviving model candidates.

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

This is now a causal path rather than a representation-only experiment. A host can submit a typed semantic event through the public agent API. The subject's current relationship and explicit goal preference determine appraisal, which then changes:

- episodic memory emotional valence;
- emotional intensity;
- relationship relevance;
- identity relevance;
- unresolved status;
- bounded existing pressure vessels.

The same cancellation event is regression-tested to leave an unresolved negative relational memory with fear in one subject context and a positive relief-oriented trace with curiosity in another. The source event remains identical in both cases. The resulting memory survives restart.

The typed path does not replace the older lexical interaction-signal appraisal yet. It is an additional explicit host/sensor semantic path.

### 8. Provenance-aware epistemic state

`persona_engine/core/epistemic.py`

Ensemble now explicitly distinguishes:

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

Evidence is append-only. Recording testimony does not automatically create belief or world truth. Non-unknown revision requires explicit evidence references. Cross-proposition evidence fails closed. Corrections can change the current stance without rewriting the original evidence. Model inference retains its source class and uncertainty after round-trip serialization.

This closes the conceptual gap between “I remember being told X” and “I believe X.”

The next integration step for epistemics is subject persistence/replay and explicit host/world evidence admission, not natural-language parsing.

### 9. Speech delivery receipts and lived delivery consequence

`persona_engine/core/delivery.py`

`CharacterAgent.record_delivery_receipt(...)`

Ensemble distinguishes generated/intended speech from what actually happened in the host environment.

V1 records:

- fully delivered speech;
- prefix/partial delivery;
- no delivery.

A failed delivery stores the intended text digest and length but not the undelivered plaintext.

Delivery is now connected to the continuing subject. A host receipt becomes episodic evidence of what the subject actually managed to say. Partial or failed delivery becomes unresolved lived experience and can add bounded startle pressure.

An interrupted sentence is regression-tested across restart so the subject retains the delivered prefix and interruption while the undelivered remainder is absent from that lived memory.

The core renderer's original full response remains only noncanonical speech evidence in the diagnostic event stream.

### 10. Scene Lab

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

### 11. Public Ensemble activation

`CharacterAgent.use_ensemble_renderer(...)` enables the Ensemble Ollama path through the public agent API.

`CharacterAgent.set_renderer(...)` remains a generic host seam.

Hosts no longer need to reach into `agent.engine` internals to select the candidate-ecology renderer.

Renderer selection remains host policy and does not mutate character identity or continuity.

### 12. Runnable Scene Lab and actual-model comparison tools

`tools/run_ensemble_scene_lab.py`

Runs a three-turn situated scene with Pretorius, Jay and a Rival actor. It includes actor movement, actor-specific hidden information, and optional interruption. With no model argument it runs deterministically offline; with `--model` it activates the public Ensemble Ollama renderer.

`tools/ensemble_relationship_probe.py`

Runs the matched-history relationship expression experiment with the Ensemble renderer.

`tools/compare_ensemble_reports.py`

Compares matched single-shot and Ensemble report artifacts and measures:

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
2. Do direct/contextual/initiative modes improve naturalness and character distinction compared with seed-only variation?
3. When do sparse authored landmark candidates outperform model realization, and when should they lose?
4. Does character-owned agenda pressure create believable initiative without becoming engagement optimization?
5. Which typed appraisal dimensions change useful downstream behavior across held-out events and characters?
6. How should subject belief update when testimony, observation and world authority conflict?
7. Does delivery-aware lived history materially change later recall, relationship and action after interruptions or failed speech?
8. Does the same subject feel more coherent and alive in Scene Lab than in isolated chat?
9. Which mechanisms survive cross-model and cross-character ablation?

## Immediate implementation frontier

The major remaining work is now integration, replay and evaluation rather than creating the basic mechanisms.

### A. Full engine-owned candidate orchestration

Candidate prevalidation currently reconstructs the authority available in `ExpressionRequest` and then the engine validates the winner again.

The stronger endpoint is for the engine itself to own candidate orchestration so each candidate receives the exact complete live validation context, including authorities that should never be copied into renderer state.

### B. Epistemic persistence and replay

The epistemic ledger representation is deterministic and round-trippable, but it is not yet installed as a canonical subject-state family in `InteriorEngine` persistence/replay.

The next step is to persist append-only evidence and current proposition projection with replay-equivalent revisions, then connect explicit testimony/observation/world-authority admission paths.

Do not infer propositions by unrestricted free-form parsing merely to populate the ledger.

### C. More appraisal consumers

Memory salience and pressure are now real consumers. Next experiments should test whether subject-relative appraisal must also affect:

- attention;
- retrieval;
- disclosure;
- semantic decision;
- relationship consequence.

Only promote effects that improve controlled held-out behavior.

### D. Delivery-aware social consequence

Delivery now changes the subject's own lived speech memory. The next situated experiments should determine whether the recipient's relationship update and shared-world evidence should be based on delivered content rather than intended content.

### E. Persistent agenda development

Current agenda is a rebuildable projection. If scenes demonstrate that pending questions, intended disclosures or topics-to-return-to cannot be represented by existing intentions/open loops/symbols/habits, promote those demonstrated fields into canonical subject state.

### F. Real-model and human evaluation

Run matched Qwen/Gemma and later heterogeneous-model comparisons, then paired human recognition tests.

The target is not maximal textual variation.

The target is:

> more expressive possibility, more initiative and more situated causal behavior with equal or better subject continuity.

## Relationship to Wayfarer

Do not rewrite Wayfarer history.

Wayfarer remains the control-plane research line and a useful comparison condition. Ensemble is intentionally freer and more synthetic: it inherits Wayfarer's authority boundaries while testing candidate ecology, initiative, subject-relative experience, explicit epistemics, situated interaction and richer model participation.

If Ensemble ultimately wins the comparative evidence, validated mechanisms can be folded into `main`. If it fails, the Wayfarer line remains intact.
