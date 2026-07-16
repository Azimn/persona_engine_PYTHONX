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

## Stage 1: Behavioral Proof

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

## Stage 2: Performance Separation

Complete the existing seam:

```text
intrinsic motivation -> intention -> ActionDecision -> PerformancePlan
```

`ActionDecision` remains cognitive and portable. `PerformancePlan` realizes it
as speech, gesture, expression, delay, continued activity, or silence. A model
is called only when language is required.

## Stage 3: Compact Semantic Affordances

Add a bounded semantic-knowledge adapter only after behavioral tests identify
a visible knowledge or relevance failure. A minimal record should contain:

- concept ID;
- property or affordance ID;
- value: true, false, or unknown;
- confidence;
- provenance;
- verification state;
- source tier;
- optional supersession reference.

Use sparse arrays or relational rows, deterministic lookup, and small weighted
association lists. Do not build a general knowledge graph.

## Stage 4: Curiosity From Uncertainty

Unknown high-value distinctions may create a bounded question proposal. That
proposal enters the existing intention and synthesis systems and competes with
current activity, pressure, habits, and relationship context. It does not gain
automatic permission to interrupt or speak.

## Stage 5: Long Duration And Port Fixtures

- Run month-scale summarized simulation without per-second ticks.
- Measure event, memory, and knowledge growth.
- Verify bounded forgetting and supersession.
- Export fixed, versioned JSON fixtures for C99 reproduction.
- Compare offline and Ollama behavior from identical causal records.

Each stage must demonstrate a visible behavioral gain before the next one adds
runtime structure.
