# DUCK Future Product Specification

Status: experimental production target
Branch: `duck-future-build`
Baseline: `duck-organism` at `f36e72f31a8127f7f779a8946e1777d8ad842bd4`

> The experiment is deliberately ambitious. The fallback branch is deliberately boring. Both are features.

## 1. Purpose

This document describes DUCK as if the project had already received roughly two additional years of integration, testing, operational hardening, and usability work. It is not an MVP specification and it is not permission to claim evidence that has not been collected. It is the target shape of the finished product.

The experiment asks whether the current mature Wayfarer and DUCK codebase is already close enough to that target that the missing layers can be composed now, tested as one system, and then repaired by evidence rather than implemented strictly milestone by milestone.

The known-good `duck-organism` branch remains the rollback point. All future-product experimentation occurs on `duck-future-build` until the future branch earns promotion through tests and review.

## 2. Product definition

The finished DUCK product is a local-first, model-agnostic, embodiment-agnostic runtime for persistent artificial individuals. A DUCK individual retains a stable subject identifier, autobiography, relationships, commitments, developmental state, learned expectations, values, motivations, habits, and action history while language models, renderers, tools, interfaces, environments, and bodies may be replaced.

A language model is a replaceable semantic and expressive service. It can interpret, hypothesize, simulate, summarize, deliberate, and render language. It cannot silently become the identity authority, memory authority, world authority, relationship authority, or canonical state writer.

Wayfarer remains the canonical persistent-subject authority. DUCK is the cognitive-organism layer that decides what becomes salient, what matters, what may happen next, what action to commit to, and how outcomes alter future cognition.

## 3. Production invariants

The future product is accepted only if these remain true under ordinary use, failure, restart, service substitution, and body substitution.

1. `subject_id` never changes merely because an LLM, renderer, process, host, or body changes.
2. Canonical state changes have typed authority, evidence, provenance, and an auditable transition.
3. Generated prose is never the sole canonical representation of identity or lived history.
4. LLM services return proposals. Canonical writes occur through deterministic or explicitly authorized reducers and subject APIs.
5. The global workspace remains a small causal broadcast bottleneck, not the LLM context window.
6. Motivation is closed-loop regulation whose deficits influence attention, memory, goals, simulation, and action.
7. Internal reflection does not imply outward speech. Outward communication is an action and must pass normal action selection.
8. Simulation predicts both likely world consequences and likely subject consequences before commitment where feasible.
9. Action success is established by outcome evidence, not by the executor declaring that it worked.
10. Exact replay never depends on an unrecorded wall clock, network response, random UUID, filesystem path, or unordered iteration.
11. A body is replaceable through an embodiment port. Cognition must not assume that the world is a chat window.
12. Tool and effector access is capability-declared and policy-gated.
13. Failure of an optional model or service degrades that service rather than corrupting the subject.
14. Code completeness and evidence completeness are tracked separately.

## 4. Finished system architecture

```text
WORLD / BODY / SERVICES
        |
        v
EmbodimentPort + Event Gateway
        |
        v
Situation Construction + Subject Attribution
        |
        +-------------------------+
        |                         |
        v                         v
Homeostatic Motivation      Wayfarer Subject
        |                   identity, autobiography,
        |                   relationships, beliefs,
        |                   commitments, development
        +-----------+-------------+
                    v
           Cognitive Candidate Field
 perception, memory, drives, private reflection,
 prediction error, social concerns, procedures,
 temporal expectations, optional LLM hypotheses
                    |
                    v
              Global Workspace
                    |
          +---------+----------+
          |                    |
          v                    v
    Memory activation     World + Self Simulation
          |                    |
          +---------+----------+
                    v
             Candidate Actions
                    |
                    v
              Action Selection
                    |
                    v
                 Intention
                    |
                    v
        Capability / Safety Firewall
                    |
                    v
              EmbodimentPort
                    |
                    v
                  WORLD
                    |
                    v
          Outcome + Prediction Error
                    |
                    v
 learning / metacognition / subject update / memory
                    |
                    v
               next moment
```

## 5. Subject and identity layer

Wayfarer is not duplicated inside DUCK. Identity, biography, episodic/autobiographical memory, relationship history, belief provenance, commitments, continuity time, renderer-independent developmental state, and subject-scoped epistemic state remain behind the subject port.

DUCK may activate or propose changes concerning those domains only through public subject APIs. It must not keep a shadow biography or a second competing identity model.

A future body transfer therefore attaches a new embodiment to the same subject authority. A model transfer attaches new cognitive/renderer services to the same subject authority. Neither operation creates a new individual by default.

## 6. Temporal architecture

DUCK uses four noninterchangeable temporal concepts.

`logical_tick` establishes deterministic causal order inside the cognitive organism.

Wayfarer's `ContinuityClock` owns monotonic elapsed subject time. Host clock regressions cannot make the subject's accumulated duration run backward.

Observed UTC is environmental evidence. It enters explicitly through an event or host adapter and is recorded when relevant. Replay never silently asks the current machine for the time.

Swatch Internet Time is the portable subject-facing civil clock. Each civil-time observation can derive `bmt_date` plus `@beat`. One day contains 1000 beats and one beat equals 86.4 seconds. Beat Time is a representation of civil time, not a substitute for causal ticks or elapsed-duration arithmetic.

Temporal pattern learning may later infer expectations such as a person's typical interaction interval or arrival band. A deviation becomes prediction evidence, not a hardcoded "three hours of silence" rule.

## 7. Endogenous cognition and proactivity

Background cognition and proactive action are separate mechanisms.

An unresolved issue, active drive, approaching obligation, prediction error, relationship concern, salient memory, or stalled goal can request an internal cognitive cycle. Internal specialists can produce private workspace candidates. These candidates may alter attention, retrieval, simulation, goals, or future action proposals.

No reflection engine gets a direct `send_message()` path.

If internal pressure makes communication useful, communication is represented as a candidate action. It must win workspace relevance, survive simulation and action scoring, pass capability/policy constraints, and then execute through the current body or interface. Being ignored or receiving an unexpected response becomes outcome evidence and can alter future social predictions.

## 8. Motivation

The production drive system remains homeostatic rather than decorative. Core regulatory domains include viability, affiliation, competence, certainty, autonomy, integrity, and exploration unless a cartridge or research configuration specifies a smaller validated set.

Drive deficit changes attentional and behavioral pressure. Actions produce predicted self effects. Observed self effects satisfy or frustrate drives. The result updates later cognition. Biological labels are used only when a mechanism justifies them. DUCK does not need fictional dopamine merely to make a state variable sound organic.

## 9. Memory

The finished product exposes distinct functional memory contracts while allowing shared physical storage. Required functions are sensory/transient context, working episode, episodic history, autobiography, semantic knowledge, social/person models, procedures/skills, prospective commitments, and derived narrative summaries.

Narrative summaries are caches. They can be regenerated and can never become the sole surviving record of canonical events.

Retrieval combines semantic similarity with recency, self relevance, affective salience, drive relevance, goal relevance, relationship relevance, temporal links, causal links, and workspace reinforcement. Temporal facts distinguish when a proposition was believed or valid from when the database recorded it, so correction does not require historical amnesia.

## 10. Global workspace

DUCK has one authoritative workspace. Parallel specialists can propose candidates, but a bounded competition determines the dominant coalition or item for the cycle. The broadcast must change downstream computation. If removing the workspace has no measurable downstream effect, the implementation has failed its architectural purpose.

The workspace is never a synonym for the prompt context. LLM context is a task-specific projection built after authority filtering.

## 11. Simulation and planning

The simulator is independent of language generation. It predicts `World(t+n)` and `Self(t+n)` for bounded action branches. Early branches can use learned action-effect rules and deterministic environment models. Optional semantic services may propose uncertain open-world consequences, but their provenance and confidence remain explicit.

Longer planning may use bounded search, procedural decomposition, or external planners. The planner proposes. The action selector commits.

## 12. Action, agency, and learning

Every outward behavior is a candidate action, including speaking, waiting, asking, looking, moving, using a tool, checking memory, or declining to act.

An intention creates expected world and self effects before execution. Execution occurs through an embodiment/capability boundary. The observed result is compared with expectations. Prediction error updates world-model reliability, procedure confidence, agency estimates, metacognitive calibration, drive regulation, and relevant subject history.

The architecture therefore learns not only "what tends to happen" but "what tends to happen when this subject acts this way in this context."

## 13. Embodiment

The body contract is present even when the first deployment is text-only. `EmbodimentPort` exposes a stable body identifier, body snapshot, sensors, effectors, observations, affordances, and execution outcomes.

Reference bodies should include a deterministic MockPond/test body, text/voice companion body, desktop tool body, game-engine body, XR body, and eventually robot adapters. The low-level body may run faster controllers than DUCK's global cognitive cycle. DUCK does not need to micromanage a robot's motor stabilization or a game's animation blend tree.

A body-transfer test attaches a new body to the same `subject_id` and checks continuity, capability adaptation, self-location/ownership updates, and behavior under changed affordances.

## 14. LLM and model services

LLMs are optional service providers behind typed contracts. Production services include semantic interpretation, social inference, bounded deliberation, open-world simulation hypotheses, memory abstraction, private-cognition proposals, and language rendering.

Every service has a purpose-built context projection, schema validation, timeout, model/provider identity, provenance, and replay strategy. Model failure can fall back to another provider, a smaller local model, deterministic logic, or no proposal depending on the service.

Model substitution must preserve canonical subject state. Differences in language quality are acceptable. Unexplained reset of relationship, commitments, biography, identity, or learned state is not.

## 15. Capabilities, tools, and self-extension

Tools and effectors are declared capabilities. Each declaration identifies action type, provider, enablement, confirmation policy, risk class, and metadata. Capability state does not grant an LLM kernel-write authority.

A future tool-maker may generate extension source code, but generated code is treated as an untrusted artifact. Production installation requires static validation, isolated execution, tests, a capability manifest, permission review, and registration through the capability system. Generated extensions run outside the trusted cognitive kernel whenever practical.

DUCK may learn to use a new tool without being allowed to rewrite DUCK.

## 16. Persistence and replay

Wayfarer persists the subject. DUCK persists operational cognitive state, action/prediction ledgers, learned procedure/world-model state, scheduler state, traces, configuration fingerprints, and recorded service outputs needed for exact replay.

Writes are crash-safe and checkpoints are validated. An append-only history allows reconstruction and diagnosis. Exact replay uses recorded model/service outputs. Counterfactual replay intentionally swaps a model or policy while holding canonical history fixed.

Production replay diagnostics report the first divergent tick and the state domains responsible.

## 17. Security and failure isolation

The trusted computing base is deliberately small: subject authority, typed contracts, reducer/authority rules, persistence/replay machinery, execution policy, and capability checks.

Network services, generated text, model proposals, plugins, sensors, and external tools are untrusted inputs. Tool permissions follow least authority. High-impact actions can require confirmation. Optional subsystems fail closed or degrade locally. A malformed LLM output does not get to repair itself by rewriting canonical state.

## 18. Observability

Every cycle emits a structured trace answering: what happened, what became salient, what was remembered, what was predicted, what was selected, what actually occurred, what changed, why was the change authorized, and can it be replayed?

Operational telemetry is separated from canonical subject history. Human-readable dashboards should render causal traces without exposing or depending on hidden model chain of thought.

## 19. Product interfaces

The core ships headless first. Stable interfaces include the Python API, a local service API for companion/game integrations, checkpoint/replay tooling, trace inspection, body adapters, model-provider adapters, and a CLI for deterministic probes.

A polished desktop interface, voice/avatar layer, game-engine plugins, and remote clients are distribution layers around the same organism rather than alternate implementations of the character.

## 20. Validation program

Code-complete does not mean research-complete. The future product requires multiple evidence layers.

Deterministic engineering gates cover unit tests, mutation authority, serialization, crash recovery, replay identity, service failure isolation, model replacement, body replacement, security policy, and long-run resource stability.

Longitudinal machine evaluations cover memory accuracy, temporal reasoning, commitment completion, agency calibration, prediction calibration, developmental stability, relationship discrimination, proactive-behavior precision, and catastrophic drift.

Adversarial probes target prompt injection against canonical state, manipulative user pressure, contradictory memories, service hallucinations, corrupted checkpoints, repeated model swaps, body loss, clock regression, stale tools, and failed effectors.

Human studies evaluate recognizable individual continuity, earned developmental change, appropriate initiative, history sensitivity, relationship specificity, coherent surprise, repetition, and overall believability. These remain empirical results to be collected, not claims created by code.

## 21. Promotion gates for the future-build experiment

`duck-future-build` is not promoted because it looks architecturally impressive. It earns promotion only after it returns the original DUCK suite to green, adds green tests for its new interfaces, passes replay and model-swap regressions, survives a long deterministic run, demonstrates body-port execution, demonstrates background cognition without direct-speech bypass, and receives an external adversarial review.

If integration repeatedly breaks the authority model, deterministic replay, subject continuity, or testability, the experiment is frozen and development returns to the milestone plan from the untouched `duck-organism` branch.

## 22. Definition of finished

The code can eventually be called production-candidate complete when every architecture box has a real interface and implementation, all persistent writes have authority and migration rules, optional external services can fail without subject corruption, at least one real local LLM and one alternate model can be swapped, at least two bodies/interfaces can be swapped, replay is deterministic where promised, and operational documentation can reproduce installation, tests, migration, backup, recovery, and probes from a clean machine.

The research can be called well validated only after longitudinal and human evidence supports the intended behavioral claims.

Those are deliberately different finish lines.

The duck may be code-complete before the duck has tenure.
