# Current DUCK Architecture Audit for the Platform-Penalty Study

Evidence class: **architectural inference grounded in source inspection and frozen deterministic evidence**

Frozen DUCK checkpoint: `86db5344e093a8f516fd2f9ec26d866d29bed019`

Experimental branch: `duck-platform-penalty-experiment`

## Baseline verification

The frozen checkpoint already has a complete green CI baseline. The exact-head workflow passed on Python 3.11 and 3.12. The 3.11 job recorded `534 passed, 1 skipped` for the inherited deterministic suite and `58 passed` for the focused DUCK organism subset. This audit therefore treats `86db5344` as a stable experimental reference rather than silently substituting a moving branch.

The DUCK-specific branches `duck-export-package`, `duck-future-build`, `duck-refactor-v2`, and `duck-subjective-access-v0.1` converge on this checkpoint. `duck-organism` is older. Several later Wayfarer research branches diverge from earlier bases and are therefore donor/evidence lines, not later compatible DUCK production checkpoints.

## Current macroarchitecture

The present system is already substantially more than a renderer/persona wrapper:

```text
HOST / WORLD AUTHORITY
       |
       v
observation + canonical elapsed time
       |
       v
Wayfarer continuing subject authority
  identity / biography / relationships / beliefs / commitments
       |
       v
DUCK interaction cycle
  organism tick
  appraisal + pressure state
  interpretation
  memory retrieval
  private cognition proposal / validation
  intentions / habits / values / commitments
  decision semantics
  expression workspace
       |
       v
renderer / model realization
       |
       v
consistency validation + delivery evidence
       |
       v
canonical outcome / memory / relationship / learning updates
```

The production-candidate architecture already includes persistent subject identity, autobiographical and relationship continuity, epistemic evidence/revision, situation construction, self-attribution, homeostatic/body regulation, memory activation, limited workspace competition, simulation, action selection, embodiment feasibility, execution/delivery evidence, learning, metacognition, endogenous cognition, renderer isolation, persistence, backup/restore, CLI and local API.

The Platform Penalty experiment therefore **must not introduce duplicate modules merely because an external architecture uses different terminology**.

## Current authority boundary

### Wayfarer

Wayfarer remains the long-term continuing-subject authority. `duck.subject_adapter.SubjectPort` exposes a narrow snapshot/retrieval/relationship/event interface to DUCK. The subject ID resolves from Wayfarer writer/identity custody rather than from a DUCK-local persona object.

Wayfarer owns continuity-critical state including permanent identity, authored/lived biography, relationships, subject-scoped belief provenance, commitments and developmental history.

### DUCK

DUCK owns reusable cognitive mechanisms and current mechanistic state required to transform the continuing subject plus current world/body conditions into cognition and action. DUCK is not supposed to create a second canonical identity/memory/relationship database.

### Cartridge / `.snp`

The current `.snp` format already distinguishes authored phenotype from mutable lived state. Its phenotype is explicitly a baseline. Runtime memory, developed relationships and current affect are not supposed to be written back into the cartridge.

The current architecture lock says all character-specific content belongs in `.snp`. That statement is useful as an anti-hardcoding constraint but is precisely one of the abstraction claims under experiment: a future compiled origin specification may need character-specific **organization**, not merely descriptive content, while still remaining distinct from continuation state.

### Renderer/model

Renderer output is realization/proposal evidence, not canonical subject authority. Existing real-model evidence demonstrates why this boundary matters: model runs have denied available memories, invented interpretations, flattened relationship differences, copied examples, produced repetitive language and exhibited model-specific behavior while canonical state remained available outside the model.

### Host/body/world

Current sensors/effectors and world truth are host authority. Embodiment capabilities filter feasible action candidates before commitment and execution checks feasibility again. A subject may know or remember a procedure that its current embodiment cannot perform.

## Where character-specific information currently enters

### Identity and authored biography

`CoreIdentity` and the identity ledger receive cartridge-authored name, core beliefs, temperament, moral boundaries, speech constraints, prohibited mutations, forbidden self-claims and biography/resource material.

These are already strong identity anchors and should not be duplicated in an experimental graph.

### Appraisal

Character effects enter through several paths:

- `BehavioralDispositionProfile` affects resistance selection.
- cartridge interpretation bias and subject appraisal context can alter meaning.
- current relationship trust/attachment/guardedness affects subject-relative semantic appraisal.
- current pressure state influences interpretation and risk.

However, some general appraisal machinery remains globally parameterized. The experimental question is whether richer character-owned sensitivities/couplings materially improve behavior over these existing disposition pathways.

### Drives / homeostasis / affective pressure

Body profiles and current organism state differ by character, but several DUCK pressure/drive targets, decay rates, gains and action consequences remain shared generic constants. This is a plausible convergence pressure: different subjects may begin from different physical/sensory baselines yet still transform events into motivational pressure through mostly common mathematics.

### Memory

Autobiographical memory is subject-owned and history-specific. Retrieval uses existing memory-store mechanics and explicit cold-biography/read-through paths. Affect and relevance already modulate retrieval.

What is not yet strongly character-owned is a reusable declarative specification of **which semantic pathways preferentially cue which memories** beyond existing tags, biography, values and lived association. This is one place where an organization/topology prior could add value if empirical evidence supports it.

### Workspace / global competition

DUCK has a bounded current workspace and current situation construction. The competition mechanism is generic. Character state changes the candidate material that reaches the workspace, but there is no general origin-specification layer that says, for example, this individual reliably gives autonomy-related evidence higher access while another gives affiliation evidence higher access under the same current state.

That is a candidate Condition-B seam, not proof that a graph is needed.

### Simulation / prediction

World/self simulation uses shared mechanisms over current subject/world/body state. Character-specific differences mainly arise indirectly from current beliefs, relationships, body and motive state. There is limited authored support for character-specific predictive models of consequences.

### Action scoring / semantic conduct

This is one of the clearest current character-conditioning points and one of the clearest limits.

Existing behavior profiles can make identical manipulation produce different resistance modes. Existing deterministic evidence shows Pretorius, Friendly and Rival resolving the same manipulation differently before rendering. Value rules can also constrain ordinary conduct.

At the same time, the semantic conduct resolver remains mostly a shared priority/rule cascade and the general action selector uses shared utility mathematics. Character-owned executable value rules are intentionally sparse. This may make the ordinary `.snp` representation underpowered relative to the generic engine rather than showing a necessary shared-platform limitation.

The Platform Penalty benchmark must distinguish those two explanations.

### Relationships

Current relationship state is continuing subject state, not cartridge identity. It affects appraisal, risk, expression envelope, history evaluation, decision effects and memory salience. This is correctly outside immutable origin specification.

An origin specification may contain relationship **priors or sensitivities**, but current trust/guardedness/attachment must remain continuation state.

### Epistemics

Evidence and current belief are separate. The epistemic ledger records evidence independently of revision, and interpretation can project settled subject beliefs as internal sources without promoting temporary interpretation to world truth.

Any new topology may reference belief/evidence IDs or bias attention to evidence but must not collapse evidence, belief and graph activation into one scalar.

### Initiative / proactivity

The proactive queue and endogenous/idle mechanisms are shared. Character-specific body/world/relationship state influences triggers, but proactive policy itself is mostly generic. This is a potential convergence surface if individuals with radically different initiative styles still receive the same threshold structure.

### Renderer context

Renderer context is highly character-specific: identity constraints, temperament, voice, relationship stance, authored examples, current decisions, commitments, memories and development state all enter the expression brief.

This already supports substantial surface differentiation. Previous seven-character mock-renderer testing did not measure that perceptually because the renderer intentionally flattened expression. Actual-model evidence shows the inverse problem too: a model can obscure valid underlying differentiation. Therefore renderer quality must not be used as the sole measure of architecture quality.

### Learning

Current learning includes memory accumulation, relationship consequences, habit evidence, slow-belief consolidation, delivery/outcome evidence and metacognitive/procedural mechanisms. These are generic algorithms over individual histories.

There is not yet a clean origin-owned plasticity contract specifying which authored structural priors may adapt, how quickly, within what bounds, and with what provenance. The connectome prototype attempts this but conflates the origin, current activation and learned state in one SQLite store.

## Current sources of convergence pressure

The shared substrate can unintentionally make characters converge through at least these mechanisms:

1. global appraisal coefficients or thresholds that dominate character-specific sensitivities;
2. shared drive targets/decay/gains that compress different regulation profiles into similar motivational states;
3. shared workspace-selection thresholds without strong individual salience priors;
4. shared memory activation/retrieval rules where authored semantic organization is too shallow;
5. shared simulation assumptions where different characters should predict different consequences;
6. sparse value/action mappings compared with rich descriptive values;
7. common initiative thresholds;
8. common action utility transforms;
9. renderer flattening that hides real pre-renderer divergence;
10. over-strong authored examples that can create surface differentiation without corresponding mechanistic differentiation.

The first eight are potential substrate/conditioning limitations. The last two are expression confounds.

## Current evidence against the claim that shared mechanisms necessarily erase individuality

The existing system already supplies negative evidence against the strongest version of that claim.

Under an identical manipulation, Pretorius, Friendly and Rival can resolve different semantic conduct before rendering. Existing regression evidence also shows that different decisions cause different relationship trajectories. Therefore any argument for bespoke character organisms must explain an **incremental** deficit, not simply assert that the current shared engine produces generic behavior.

## Current evidence against declaring the shared boundary solved

The evidence is insufficient for the opposite conclusion.

- The seven-character package tests used a mock renderer and therefore did not establish human-perceived differentiation.
- Current executable value mappings are sparse relative to authored character material.
- Real models can deny valid memories, invent motives, repeat examples or flatten current relationship state.
- Several high-level mechanisms remain globally parameterized.
- Existing cross-character tests are relatively few and were designed alongside the architecture.
- There has not yet been a fair specialized Condition C.

Therefore `shared mechanisms work at all` is established more strongly than `the current shared abstraction has negligible platform penalty`.

## Architecture hypothesis entering Phase 2

The strongest source-grounded hypothesis is currently:

```text
shared DUCK mechanisms
+ origin-owned individual organization priors
+ Wayfarer-owned developmental continuation
+ current host/body/world constraints
= potentially high individuality without per-character engine forks
```

This is an architectural inference, not a conclusion.

Condition B will test whether deeper organization improves the current shared system. Condition C will test whether generic mechanism boundaries still impose a measurable penalty after B is strengthened.

## Non-goals for the experimental branch

The experiment will not:

- replace Wayfarer as subject authority;
- migrate lived memory into a cartridge;
- make renderer output canonical;
- add character-name branches to generic Condition-B code;
- import the Persona Connectome SQLite store;
- claim biological equivalence;
- use graph nodes as pretend neurons;
- rewrite old negative evidence after fixes;
- merge experimental organization into the frozen production candidate before the decision evidence exists.
