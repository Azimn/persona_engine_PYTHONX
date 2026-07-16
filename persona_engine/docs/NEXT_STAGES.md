# Next Stages

This roadmap prioritizes visible life, behavioral proof, and C99 portability.
It is informed by the current Python engine, the older PersonaConsole society
probe, and *Towards Avatars with Artificial Minds: Role of Semantic Memory*
(Duch, Szymanski, and Sarnatowicz, 2006).

## Paper Assessment

The paper's useful lesson is not that Persona Engine needs a large ontology.
Its useful lesson is that simple task-specific representations can outperform
more ambitious knowledge structures when latency and practical behavior matter.

Ideas worth carrying forward:

- Distinguish verified false from unknown.
- Store confidence and provenance with conceptual knowledge.
- Prefer compact concept-property records for bounded tasks.
- Retrieve associations quickly enough to affect current behavior.
- Let missing distinctions propose relevant questions.
- Preserve the difference between semantic knowledge and episodic experience.

Ideas not justified for this project now:

- A general-purpose semantic network or graph database.
- Automatic ingestion of large external ontologies.
- Unvalidated extraction of canonical facts from free text.
- A separate avatar mind or dialogue controller.
- Avatar technology that can mutate organism state.

## Stage 1: Behavioral Proof (Implemented)

Build a generic evaluation harness that:

- runs one or two isolated character sessions;
- captures only visible speech and actions for blind review;
- exports matching synthesis, memory retrieval, world events, intrinsic
  decisions, randomness provenance, and action outcomes separately;
- checks repetition, assistant drift, identity bleed, and continuity;
- supports offline and model-backed renderers through the same engine path.

The first paired scenario is Pretorius and Kiki because their motives and
performance constraints stress different failure modes. The host may pass
observable speech between them but may never share private state.

## Stage 2: Performance Separation (Implemented)

Complete the existing seam:

```text
intrinsic motivation -> intention -> ActionDecision -> PerformancePlan
```

`ActionDecision` remains cognitive and portable. `PerformancePlan` realizes it
as speech, gesture, expression, delay, continued activity, or silence. A model
is called only when language is required.

## Stage 3: Compact Semantic Affordances (Pilot Implemented)

The current bounded semantic adapter contains:

- concept ID;
- explicit features, relations, and candidate affordances;
- value: true, false, unknown, usually, or sometimes;
- confidence;
- provenance;
- verification state;
- source tier;
- direct-over-inherited resolution.

It uses sparse explicit profiles, deterministic one-hop activation, and small
top-k lists. It does not build a general knowledge graph or accept prose as
semantic authority.

## Stage 4: Curiosity From Uncertainty

Fallible self-monitoring is now implemented before this stage. Actual engine
diagnostics produce character-shaped perceived diagnostics and regulation
candidates that compete in situated synthesis. The next cognitive slice is
bounded social attribution, but only where its hypotheses can visibly affect
clarification, concealment, anticipation, delay, repair, withdrawal, or
performance.

Unknown high-value distinctions may create a bounded question proposal. That
proposal enters the existing intention and synthesis systems and competes with
current activity, pressure, habits, and relationship context. It does not gain
automatic permission to interrupt or speak.

## Stage 5: Long Duration And Port Fixtures

The first long-duration proof is implemented. Original subjective experience
survives fourteen-day decay, missed corrective evidence is deferred, calm
reconsideration appends a new meaning, and C99-oriented JSON preserves the
two-version chain.

- Run month-scale summarized simulation without per-second ticks.
- Measure event, memory, and knowledge growth.
- Verify bounded forgetting and supersession.
- Export fixed, versioned JSON fixtures for C99 reproduction.
- Compare offline and Ollama behavior from identical causal records.

Each stage must demonstrate a visible behavioral gain before the next one adds
runtime structure.
