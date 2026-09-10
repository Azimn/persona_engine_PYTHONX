# ADR-001 — Shared DUCK vs Deep Individual Organization vs Bespoke Character Organism

Status: **PROVISIONAL / EXPERIMENT REQUIRED**

Date: 2026-09-10

Frozen production reference: `86db5344e093a8f516fd2f9ec26d866d29bed019`

## Decision question

What architecture best preserves strong individual behavioral/developmental continuity while retaining model independence, embodiment independence, inspectability, portability and reuse?

Three candidate boundaries are under direct comparison.

## Option A — reusable shared DUCK + ordinary structured subject specification

### Definition

All subjects share the same cognitive mechanisms. Character-specific authored information enters through the existing `.snp` and Wayfarer subject state. Character effects arise through identity, disposition, values, phenotype, sensory/interpretation profiles, biography, relationships and accumulated history.

### Strengths

- simplest architecture and authoring model;
- strongest portability and maintainability;
- easiest mechanism-level validation and ablation;
- no per-character code forks;
- current evidence already proves some pre-renderer behavioral divergence;
- mature continuity, authority and migration behavior already exists;
- easiest model/body swapping;
- lowest risk that character identity becomes entangled with one provider or bespoke policy.

### Weaknesses / risks

- character organization may be underexpressive relative to rich authored descriptions;
- generic appraisal/motivation/workspace/action parameters may cause convergence;
- sparse current executable value mappings may leave much character material renderer-only;
- different people may require different couplings among otherwise shared mechanisms;
- a shared policy can preserve broad persona labels while still flattening developmental trajectories.

### Evidence that would select A

A performs within the pre-registered noninferiority margin of C across core renderer-independent and longitudinal individuality dimensions, produces no hard authority failures, and B does not earn its extra complexity through meaningful improvements.

## Option B — reusable DUCK + deep individual organization

### Definition

Subjects share the same mechanisms, but the origin specification can sparsely reorganize how those mechanisms couple. Examples include authored sensitivities, inhibitory/excitatory routing, salience priors, motive/value relevance, memory-attention biases, procedural tendencies, expression tendencies and plasticity constraints.

Current state is **not** placed into the origin specification. Wayfarer continues to own lived state. The organization representation is initially representation-neutral; graph topology is one later candidate encoding.

### Strengths

- preserves reusable cognitive mechanisms while allowing much deeper individuality;
- fits the biological engineering lesson that common mechanisms can behave differently under different organization;
- compatible with model/body replacement because subject authority remains external to the model;
- character-specific effects remain declarative/inspectable rather than hard-coded into engine branches;
- can potentially compile from `.snp` plus sparse organization data;
- authored structural priors and learned deltas can remain separable.

### Weaknesses / risks

- more authoring complexity;
- may become a disguised second cognitive architecture if organization hooks are too powerful;
- risks duplicated authority if graph nodes copy memories, relationships or beliefs;
- organization weights can become magic numbers with unclear semantics;
- graph/topology representation could create false biological confidence;
- maintaining parity/migration semantics is harder.

### Evidence that would select B

B materially improves one or more pre-registered individuality dimensions over A while preserving hard authority invariants, and B is engineering-noninferior to C on the primary dimensions. Later topology ablation must demonstrate that any graph representation contributes beyond a simpler sparse parameter/coupling representation.

## Option C — bespoke/specialized character organism

### Definition

Each subject may have substantial character-specific policy, tuning, specialist components or custom adapters. Shared infrastructure may remain, but the character implementation is free to specialize mechanism behavior much more aggressively.

### Strengths

- maximum expressive capacity;
- useful experimental upper bound for character-specific behavior;
- can reveal which generic interfaces suppress important individual effects;
- may be appropriate for a small number of high-value characters if shared abstraction imposes a large penalty.

### Weaknesses / risks

- maintenance and portability cost;
- high authoring/engineering burden;
- character-specific bugs and difficult cross-character validation;
- greater risk that identity becomes entangled with provider/model-specific behavior;
- harder embodiment/model swaps;
- hard to distinguish genuine cognitive individuality from designer-authored scenario policies;
- weak scalability to many individuals.

### Evidence that would select or partially select C

C consistently and substantially exceeds B on core longitudinal individuality dimensions, and analysis attributes the gap to a real suppressive generic interface rather than to unfair access to scenario labels, future outcomes or canonical authority.

The response need not be all-or-nothing. A C advantage may justify narrowly scoped per-subject specialists inside an otherwise shared architecture.

## Option D — architecture discovered during investigation

The A/B/C framing is not exhaustive. If the benchmark exposes a better boundary, this ADR may be superseded by a new ADR. Examples might include:

- a shared substrate plus learned per-subject policy adapters rather than authored topology;
- a shared substrate with multiple species/family-level mechanism profiles;
- a developmental compiler that progressively proceduralizes subject-specific behavior;
- a modular mixture where only appraisal/world-model components become subject-specialized.

A discovered option must be compared against the same authority, continuity and Platform Penalty criteria rather than adopted for novelty.

## Current source-based assessment before benchmark results

### What is already established

The current shared substrate does **not** erase individuality completely. Existing deterministic regressions show the same manipulation resolving to different semantic conduct for Pretorius, Friendly and Rival before rendering. Different semantic conduct can then produce different relationship trajectories.

This makes a fully bespoke architecture carry a burden of proof: it must produce an incremental benefit beyond already-demonstrated differentiation.

### What is not established

The current shared boundary has not been compared fairly with a strong specialized upper bound. Human recognition is not established. Real-model failures can hide or distort valid canonical differences. Several generic transforms may still cause convergence, and `.snp` currently provides limited ways to author deep coupling among mechanisms.

Therefore A cannot yet be declared sufficient.

### Why B is plausible but unproven

Multiple independent lines support the hypothesis that shared mechanisms plus richer individual organization can work:

- existing DUCK cross-character divergence;
- shared-architecture persona research such as PersonaForge;
- graph-structured persona grounding in ThinkPersona;
- work separating stable identity from accumulated/current state;
- shared persona-conditioned policy results in the lower-evidence `One Policy, Infinite NPCs` preprint;
- biological connectome evidence that topology and routing matter while mechanisms are broadly shared;
- effectome evidence warning that structure alone does not determine causal dynamics.

None of those establish that a DUCK graph is necessary or that B beats A/C.

## Architectural guardrails during the experiment

All conditions preserve these non-negotiable boundaries unless the experiment is explicitly testing the consequence of removing one:

1. renderer/model output is proposal/realization, not automatic canonical authority;
2. Wayfarer owns the continuing subject;
3. world truth remains separate from subject belief;
4. evidence history is not retroactively rewritten after reinterpretation;
5. current embodiment constrains feasible intention before commitment;
6. generated speech is not proof of delivery/action;
7. internal modularity does not imply multiple selves;
8. Condition B generic code contains no named-character branching;
9. C may specialize behavior but may not gain forbidden canonical/world authority;
10. old evidence and failures remain preserved.

## Representation decision

No mandatory connectome/graph package is adopted by this ADR.

The Persona Connectome artifact suggests a possible representation of individual organization, but its current database/store/activation design mixes authored prior, transient activation, relationship state and learned history. It is not suitable as the DUCK authority model.

If B earns continuation, the first representation prototype must compile existing character semantics with topology effects disabled and pass a parity test before topology is enabled.

## Complexity accounting

Architecture quality is not measured only by character score.

For A/B/C we also record:

- character-specific authored fields/links/rules;
- generic experimental code volume;
- character-specific executable code volume;
- runtime state growth;
- persistent storage growth;
- latency;
- model/token calls;
- migration burden;
- inspectability of learned changes.

A one-point quality gain bought with hundreds of per-character rules may be a worse architecture than a three-point gain from a sparse reusable organization layer.

## Decision status

**No permanent architecture decision is made yet.**

The working hypothesis is B/C-hybrid (shared mechanisms plus deep individual organization), but the project will preserve A if the measured Platform Penalty is negligible and will move toward greater specialization if C exposes a persistent material deficit that B cannot close.

## Falsification criteria

The working B hypothesis is falsified or weakened by any of these results:

- A is already noninferior to C and B adds no meaningful downstream individuality;
- B's gains disappear when topology/organization is ablated or when held-out subjects are used;
- B requires duplicating canonical memory/relationship/identity authority to outperform A;
- B only improves renderer wording while semantic decisions/trajectories are unchanged;
- C maintains >10-point advantages on core longitudinal individuality dimensions after fair control of information and complexity;
- B cannot preserve same-origin/different-life divergence across restart/model/body swaps;
- the representation requires dense hand-authoring or character-specific engine branches to work.
