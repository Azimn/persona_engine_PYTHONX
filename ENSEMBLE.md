# Project Ensemble

Status: experimental successor branch to Project Wayfarer

Primary branch: `ensemble`

Parent checkpoint: `wayfarer-local-model-hardening` at `76e054d9c232d55c0163cfd5816fa527033c62c2`

## Why Ensemble exists

Wayfarer demonstrated a strong and increasingly well-tested principle: the language model should not own the simulated individual. Identity, biography, memories, relationships, commitments, values, world truth, and final semantic decisions remain outside the model.

Actual-model testing with Qwen and Gemma also exposed the opposite risk. A control plane can become so focused on correctness that the language substrate is given too little room to perform. Repeated exact wording, copied examples, memory denial, and unsupported interpretation showed that renderer fidelity and expressive possibility must be treated as separate engineering problems.

Project Ensemble preserves the Wayfarer subject kernel and broadens the performance layer.

The working metaphor is:

> The LLM is an organ, not the organism.

The organ may interpret, propose, improvise, and realize language. The continuing subject owns what happened, what is believed, what is wanted, what is decided, and what becomes canonical.

## Architectural shift

Wayfarer production currently resembles:

```text
experience -> subject state -> resolved decision -> one renderer realization -> validation -> speech
```

Ensemble explores:

```text
                         PERSISTENT SUBJECT
                                |
                        resolved character moment
                                |
                          semantic SpeechPlan
                                |
               +----------------+----------------+
               |                |                |
          model candidate   authored landmark  deterministic /
             A / B / C         behavior        retrieval candidate
               |                |                |
               +---------- candidate pool -------+
                                |
                        hard consistency gates
                                |
                    character-fidelity ranking
                                |
                    surface-diversity ranking
                                |
                            selection
                                |
                             speech
                                |
                       delivered consequence
```

The candidate pool is noncanonical. Losing it cannot erase or rewrite the subject.

## Ensemble v1 implemented slice

`persona_engine/core/ensemble_realization.py` defines a generic noncanonical realization-candidate contract and deterministic anti-repetition ranking.

`persona_engine/core/ensemble_renderer.py` defines `EnsembleLLMRenderer`.

For one already-resolved `ExpressionRequest`, the renderer:

1. builds the same authority-separated V3 expression messages used by the hardened Wayfarer branch;
2. asks the same Ollama model for several candidate realizations using deterministic seed variation;
3. compares those candidates against a small noncanonical recent-surface window;
4. chooses the least pathologically repetitive candidate;
5. returns that candidate to the existing engine consistency layer;
6. falls back to the deterministic renderer only if every model candidate fails to return text.

The selector does **not** choose the character's conduct. It does not score beliefs, goals, personality, world truth, or preferred decisions. V1 ranks surface form only.

The original `LocalLLMRenderer` remains unchanged and available as the single-shot control.

## Authority rules

Candidate generation may vary:

- wording;
- syntax;
- metaphor;
- pacing;
- degree of elaboration within limits;
- stylistic realization consistent with character voice.

Candidate generation may not vary:

- resolved dialogue act;
- identity;
- canonical biography;
- available memory evidence;
- relationship state;
- active commitments;
- protected disclosures;
- world-authority facts;
- final semantic decision.

A candidate can be rejected. A candidate cannot rewrite the subject.

## Why the recent-expression window is noncanonical

The anti-repeat cache is performance state, not biography. If it disappears after a renderer swap or restart, the character may become temporarily more repetitive, but its identity and lived history are unchanged.

If future evidence shows that long-range speech habits or quoted utterances are causally important, those should be represented through explicit delivered-speech evidence rather than silently promoting this cache into canonical identity.

## Planned experiments

### E1: Candidate ecology

Compare the original single-shot model renderer against Ensemble candidate generation on the preserved Qwen/Gemma failure cases.

Measure at minimum:

- exact duplicate rate;
- normalized duplicate rate;
- repeated openings and phrases;
- memory-grounded correctness;
- unsupported confident interpretation;
- resolved-decision fidelity;
- latency and model-call cost;
- between-character distinguishability.

Do not promote Ensemble v1 merely because outputs sound nicer.

### E2: Consistency-before-ranking

Current v1 chooses the surface-diverse candidate and then uses the existing engine consistency path.

The stronger target architecture should validate each candidate against the full higher-authority context before ranking survivors. This requires an engine-level candidate interface so the selector receives the same canonical validation context as the existing final-output path.

Do not duplicate the consistency layer inside the renderer with a weaker partial authority view.

### E3: Sparse authored landmark behaviors

Reintroduce authorship as a sparse candidate source rather than a giant response bank.

Authored behaviors should be triggered by typed semantic situations, such as betrayal by a trusted actor, a signature confession, an important repair, a characteristic boundary, or a recurring inside joke.

Authored text is one candidate. It is not automatically selected.

### E4: Typed semantic event annotation and subject-relative appraisal

Preserve the lived event, attach provenance-aware semantic features, and let character-owned state determine what those features mean to this subject.

Target path:

```text
event evidence -> semantic annotation -> subject appraisal -> attention / memory salience -> interpretation / action
```

Do not permanently rewrite autobiography according to personality.

### E5: Conversational agenda and initiative

Prototype a small inspectable `ConversationalAgenda` with only demonstrated fields, potentially including:

- current preoccupation;
- unresolved thread;
- pending question;
- topic to return to;
- thing to reveal or avoid;
- current social goal;
- initiative pressure.

The purpose is to allow some utterances to originate in the character's own ongoing concerns rather than making the subject purely reactive.

### E6: Scene Lab

Build a bounded sibling host experiment with one location, a Wayfarer/Ensemble subject, another actor, world facts, goals, time, simple actions, interruptions, and consequences.

Research question:

> Does the same persistent subject feel more alive when language participates in an ongoing causal situation rather than pure open-ended chat?

## Relationship to Wayfarer

Do not rewrite Wayfarer history.

Wayfarer remains the control-plane research line and a valuable comparison condition. Ensemble inherits its strongest contracts and tests a broader hypothesis about performance, initiative, and situated behavior.

If Ensemble proves superior, the eventual `main` line may absorb its validated mechanisms. If it does not, Wayfarer remains intact.

## Immediate test target

The next meaningful comparison is:

```text
same hardened subject state
same Qwen/Gemma model
same frozen/consumed regression cases

A: LocalLLMRenderer single-shot
B: EnsembleLLMRenderer multi-candidate selection
```

The desired result is not maximal variation. It is more expressive possibility with equal or better semantic fidelity.
