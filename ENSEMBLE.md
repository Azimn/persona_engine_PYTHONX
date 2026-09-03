# Project Ensemble

Status: active experimental successor line to Project Wayfarer

Primary branch: `ensemble`

Parent checkpoint: `wayfarer-local-model-hardening` at `76e054d9c232d55c0163cfd5816fa527033c62c2`

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
                    identity / history / world
                                |
                     current character state
                                |
                        resolved decision
                                |
                       ExpressionRequest
                                |
                  character-owned agenda view
                                |
          +---------------------+---------------------+
          |                     |                     |
     model/direct         model/contextual       model/initiative
          |                     |                     |
          +---------------------+---------------------+
                                |
                     sparse authored landmarks
                                |
                        CANDIDATE ECOLOGY
                                |
                  deterministic prevalidation
                hard/critical candidates removed
                                |
                     soft repair where allowed
                                |
                  surface-diversity competition
                                |
                         selected speech
                                |
                   engine consistency re-check
                                |
                       intended expression
                                |
                       host/world delivery
                                |
                     delivery receipt / effect
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

Every candidate can now be evaluated using the same deterministic `ConsistencyLayer` contracts used by the engine.

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

### 7. Typed subject-relative appraisal

`persona_engine/core/subject_appraisal.py`

Ensemble now has a typed experimental appraisal layer that separates:

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

The same event can therefore appraise differently for two subjects without changing the event record itself.

This layer intentionally does not assign a canned emotion label and is not yet a replacement for the existing production interaction-signal appraisal path.

### 8. Speech delivery receipts

`persona_engine/core/delivery.py`

Ensemble distinguishes generated/intended speech from what actually happened in the host environment.

V1 records:

- fully delivered speech;
- prefix/partial delivery;
- no delivery.

A failed delivery stores the intended text digest and length but not the undelivered plaintext. This prevents a sentence that nobody heard from silently becoming evidence that it was spoken.

### 9. Scene Lab

`persona_engine/evaluation/scene_lab.py`

Scene Lab is now an implemented sibling host experiment rather than a future idea.

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
- execution through the normal public `CharacterAgent.say()` API.

This provides a bounded environment for testing whether the same persistent subject becomes more life-like when language participates in an ongoing causal situation.

### 10. Public Ensemble activation

`CharacterAgent.use_ensemble_renderer(...)` enables the Ensemble Ollama path through the public agent API.

Hosts no longer need to reach into `agent.engine` internals to select the candidate-ecology renderer.

Renderer selection remains host policy and does not mutate character identity or continuity.

### 11. Actual-model comparison tools

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
5. Which subject-relative appraisal dimensions causally change useful downstream behavior?
6. Does interrupted or failed delivery materially change later memory, relationship and action once delivery receipts are connected to the subject loop?
7. Does the same subject feel more coherent and alive in Scene Lab than in isolated chat?
8. Which mechanisms survive cross-model and cross-character ablation?

## Immediate implementation frontier

The major remaining architectural work is no longer “build candidate selection.” That exists.

The next frontier is causal integration:

### A. Full engine-owned candidate orchestration

Candidate prevalidation currently reconstructs the authority available in `ExpressionRequest` and then the engine validates the winner again.

The stronger endpoint is for the engine itself to own candidate orchestration so each candidate receives the exact complete live validation context, including authorities that should never be copied into renderer state.

### B. Appraisal consumers

Subject-relative appraisal should earn production integration by changing an observable downstream consumer such as:

- attention;
- memory salience;
- retrieval;
- persistent pressure;
- disclosure;
- semantic decision;
- relationship consequence.

Do not add appraisal dimensions that never change behavior.

### C. Delivery consequence integration

The subject loop should eventually record what was actually delivered rather than assuming selected renderer output was fully spoken.

### D. Persistent agenda development

If experiments show that pending questions, intended disclosures or topics-to-return-to require state not represented by existing intentions/open loops/symbols/habits, promote only those demonstrated fields into canonical subject state.

### E. Real-model and human evaluation

Run matched Qwen/Gemma and later heterogeneous-model comparisons, then paired human recognition tests.

The target is not maximal textual variation.

The target is:

> more expressive possibility, more initiative and more situated causal behavior with equal or better subject continuity.

## Relationship to Wayfarer

Do not rewrite Wayfarer history.

Wayfarer remains the control-plane research line and a useful comparison condition. Ensemble is intentionally freer and more synthetic: it inherits Wayfarer's authority boundaries while testing candidate ecology, initiative, situated interaction and richer model participation.

If Ensemble ultimately wins the comparative evidence, validated mechanisms can be folded into `main`. If it fails, the Wayfarer line remains intact.
