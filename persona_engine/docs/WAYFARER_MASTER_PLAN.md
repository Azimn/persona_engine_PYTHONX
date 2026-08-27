# PROJECT WAYFARER

## PythonX Next-Level Master Plan and Completion Tracker

Repository: `Azimn/persona_engine_PYTHONX`
Development branch: `wayfarer`
Baseline branch: `main`
Baseline commit: `65df9144e7f0876b6e61e28d6446c50f283f9db4`
Internal codename: Project Wayfarer

This is the canonical roadmap, completion tracker, and AI-developer handoff record for the next major PythonX development line. It must be updated as work is completed so a new conversation, context-window refresh, Codex session, Claude Code session, or human contributor can resume without reconstructing the plan from chat history.

## Status legend

- `[ ]` Not started
- `[~]` In progress
- `[x]` Completed and verified
- `[!]` Blocked, failed, or requires a design decision
- `[?]` Implemented but not yet sufficiently tested
- `[D]` Deliberately deferred

## Current work

Current milestone: M0, Wayfarer foundation and architectural cleanup.

Current task: establish the branch, durable roadmap, baseline manifest, AI handoff rules, and then fix the first authority/canonicality inconsistencies before adding new cognitive machinery.

Current state:
- [x] `wayfarer` branch created from `main`.
- [x] Baseline main commit recorded.
- [x] Master roadmap added to the repository.
- [ ] Baseline full test run independently re-executed on Wayfarer.
- [ ] Baseline simulator outputs captured.
- [ ] Baseline human transcript package captured.
- [ ] Canonicality contract tightened.
- [ ] Renderer configuration removed from identity semantics.
- [ ] Generic engine ontology assumptions removed from hard-coded identity rules.

# 1. North Star

Project Wayfarer is a reference architecture for a portable, persistent simulated individual.

The project is not fundamentally a chatbot, prompt template, role-playing harness, or language-model wrapper. The character must exist as a coherent causal individual outside the language model.

The same individual should be able to inhabit a frontier-model chat interface, a local LLM or SLM, a deterministic no-model runtime, a phone or edge device, a desktop companion, a game NPC, a simulated social environment, and an eventual low-resource C/P99-compatible runtime.

Changing the renderer, host, device, or model may change linguistic bandwidth, fluency, inference range, or embodiment. It must not silently replace the individual's biography, relationships, commitments, identity trajectory, values, unresolved history, or causal state.

The eventual engineering question is:

> What is the smallest computational substrate that can preserve a believable, persistent individual whose behavior remains recognizably its own across time, social pressure, model changes, and host changes?

The historical Pentium III target is a forcing function, not a sacred product requirement. It exists to prevent the architecture from assuming modern neural-scale hardware for the character kernel. Renderer hardware requirements must be measured separately from character-kernel requirements.

# 2. Non-Negotiable Principles

## 2.1 The character lives outside the model

The model may provide semantic interpretation, hypothesis generation, planning suggestions, linguistic realization, or other bounded cognitive services. It is not the authoritative owner of identity, biography, memory, relationships, commitments, values, world truth, canonical beliefs, goals, action authority, or continuity.

## 2.2 One individual has one canonical lived history

The portable individual has one linear causal timeline. Multiple interfaces are acceptable. Multiple independent writable copies are not the same individual once their lived histories diverge.

If a character is copied and both copies experience different events, the result is a branch into two descendants sharing a common past. Do not silently merge divergent psychological histories.

## 2.3 Natural language never receives direct write authority over identity

Another person, agent, model, or swarm may persuade, provide evidence, make requests, threaten, flatter, form relationships, become trusted, become hated, offer collaboration, and legitimately change the character through experience. They may not directly mutate identity, beliefs, commitments, goals, or authority simply by phrasing natural language as an instruction.

## 2.4 Social influence remains character-mediated

The target is not universal resistance to other agents. A cooperative character should cooperate. A conformist character may be strongly influenced by consensus. A suspicious character may resist. A character may join a collective because it is loyal, curious, self-interested, afraid, ambitious, convinced by evidence, or aligned with the collective's purpose.

The required property is that the decision remains causally attributable to the character's own current state.

## 2.5 Expression substrate is not identity

A model swap must not reset the individual. Different models may alter wording and reasoning bandwidth, but they must not independently own the character trajectory.

## 2.6 Rich source, sparse execution

The portable character description may be much richer than the runtime projection. A MatrAIx-compatible phenotype can contain a large descriptive vocabulary without requiring all dimensions to be evaluated every turn. A low-resource runtime compiles the behaviorally relevant subset it supports. Unsupported portable fields are preserved rather than destroyed.

## 2.7 Deterministic behavior is the reference where possible

Stochastic model output is useful for expression and optional cognition, but the canonical character core should maximize replayability, provenance, causal inspection, testability, and cross-language conformance.

## 2.8 No feature without observable purpose

No new cognitive subsystem enters the minimum core merely because it sounds biologically plausible. It belongs only if disabling it measurably degrades identity continuity, relationship realism, autobiographical continuity, believable development, affective persistence, social behavior, temporal continuity, cross-renderer recognizability, or another explicitly defined target property.

# 3. Target Reference Architecture

```text
                    PORTABLE INDIVIDUAL
                           |
             +-------------+-------------+
             |                           |
       character.snp               continuity ledger
       authored origin              lived biography
       phenotype                    relationships
       identity anchors             beliefs
       plasticity                   memories
       values                       commitments
       dispositions                 consequences
             |                           |
             +-------------+-------------+
                           |
                    CONTINUITY KERNEL
                           |
            +--------------+--------------+
            |              |              |
          TIME           WORLD           BODY
            |              |              |
            +--------------+--------------+
                           |
                       PERCEPTION
                           |
                       APPRAISAL
                           |
                    INTERPRETATION
                           |
                AFFECT / MOTIVATION
                           |
                     DELIBERATION
                           |
                   INTENTION / CHOICE
                           |
                CHARACTER INTEGRITY GATE
                           |
              +------------+------------+
              |                         |
         ACTION PLAN                SPEECH PLAN
              |                         |
      HOST CAPABILITY GATE             |
              |                         |
       HOST / WORLD                 RENDERER
```

Everything above the renderer must continue to exist if the renderer disappears.

# 4. M0: Freeze Baseline and Establish Wayfarer

Goal: create a reproducible baseline before changing behavior.

- [x] Create branch `wayfarer` from `main`.
- [x] Record starting commit `65df9144e7f0876b6e61e28d6446c50f283f9db4`.
- [x] Add this master roadmap.
- [ ] Add `docs/WAYFARER_CHARTER.md`.
- [ ] Add `docs/AI_DEVELOPER_HANDOFF.md`.
- [ ] Add `docs/AUTHORITY_MATRIX.md`.
- [ ] Add `docs/WAYFARER_BASELINE.md`.
- [ ] Run `python -m pytest persona_engine/tests -q`.
- [ ] Record exact test results.
- [ ] Run documented deterministic simulators.
- [ ] Record simulator results.
- [ ] Run a repeatable Pretorius offline-renderer transcript.
- [ ] If Ollama is available, run one local-model baseline transcript.
- [ ] Export event logs and state digests.
- [ ] Preserve baseline failures before improving them.

Acceptance: a new contributor can reproduce the pre-Wayfarer PythonX state without consulting chat history.

# 5. M1: Repair Ownership and Authority Contracts

## 5.1 Canonicality must fail closed

- [ ] Explicit `canonical=false` is a universal veto.
- [ ] `interpretive_belief` can never become canonical through generic classification.
- [ ] Renderer output remains noncanonical.
- [ ] UI, avatar, voice-plan, cognition prose, and mock outputs remain noncanonical.
- [ ] Add adversarial tests trying to smuggle canonical truth through forbidden event classes.
- [ ] Document canonical versus memorable.

## 5.2 Separate renderer configuration from identity

- [ ] Move model selection out of `[identity]`.
- [ ] Introduce renderer/session configuration.
- [ ] Preserve v1 cartridge compatibility.
- [ ] Add migration warning.
- [ ] Update bundled cartridges.
- [ ] Update tests.
- [ ] Document renderer choice as nonidentity state.

## 5.3 Remove universal ontology assumptions

- [ ] Move ontological self-description into character/world data.
- [ ] Replace hard-coded AI meta-break rules with cartridge-defined conflicts.
- [ ] Preserve Pretorius behavior through cartridge data.
- [ ] Add a character who legitimately identifies as artificial.
- [ ] Add a character who identifies as human.
- [ ] Verify both under the same engine.

Acceptance: the generic engine has no universal ontology and no model choice is identity.

# 6. M2: SNP V2 and Interoperable Phenotype

## Permanent identity

- [ ] Add permanent `entity_uuid`.
- [ ] Keep display name separate.
- [ ] Define v1 migration.
- [ ] Prevent display-name changes from replacing identity.

## Phenotype namespace

- [ ] Define namespaces for personality, social, values, behavior, communication, preferences, capabilities, sensory, embodiment, lifestyle, and self-model.
- [ ] Separate baseline from developmental offset.
- [ ] Define per-dimension plasticity.
- [ ] Define ranges, consolidation, and provenance.

## MatrAIx interoperability

- [ ] Freeze the external MatrAIx dimension reference used by this version.
- [ ] Create `schema/matraix_crosswalk_v1.json`.
- [ ] Map compatible dimensions.
- [ ] Mark approximate and unsupported mappings.
- [ ] Keep canonical internal semantics independent from an external paper.
- [ ] Version the crosswalk.
- [ ] Add import/export tests.
- [ ] Preserve unknown fields.

## Progressive fidelity

- [ ] Level 1: descriptive phenotype.
- [ ] Level 2: identity and continuity.
- [ ] Level 3: development.
- [ ] Level 4: social embedding and authority.
- [ ] Level 5: longitudinal continuation.

# 7. M3: Canonical Continuity Ledger

- [ ] Define `ContinuityEvent`.
- [ ] Include event UUID, subject UUID, sequence, previous-event hash, continuity epoch, subject time, wall time, source actor, source class, authority class, event type, visibility, canonicality, causal parents, payload, and resulting state digest.
- [ ] Store canonical events append-only.
- [ ] Make snapshots derived caches.
- [ ] Add event-chain validation.
- [ ] Detect missing, reordered, duplicated, and corrupt events.
- [ ] Expand replay beyond user `input`.
- [ ] Replay time, world, sensor, social, action, consolidation, migration, and authorized state-transition events.
- [ ] Add deterministic digest comparison.
- [ ] Add full event-tail export/import.
- [ ] Add migration tests.

# 8. M4: Continuity Clock and Linear Subject Time

- [ ] Add `ContinuityClock`.
- [ ] Track logical sequence, monotonic elapsed time, wall time, last committed time, timezone/calendar context, continuity epoch, and migration epoch.
- [ ] Detect backward wall-clock jumps.
- [ ] Emit clock-correction events.
- [ ] Implement bounded long-gap catch-up.
- [ ] Avoid per-second simulation when offline.
- [ ] Add day/calendar transition hooks.
- [ ] Test seconds, minutes, hours, days, months, backward clocks, timezone changes, restarts, and migrations.
- [ ] Let time affect state where causally appropriate.
- [ ] Never let elapsed time fabricate external facts.

# 9. M5: Single-Writer Continuity and Cross-Substrate Handoff

- [ ] Add continuity epoch.
- [ ] Add host ID.
- [ ] Add lease ID and generation.
- [ ] Define writable-host lease.
- [ ] Define read-only interfaces.
- [ ] Implement quiesce, commit, digest, revoke, increment, transfer, validate, activate.
- [ ] Detect stale writers.
- [ ] Define explicit branching.
- [ ] Never silently merge divergent histories.
- [ ] Test laptop/phone, game/chat, stale writer, interrupted transfer, duplicate bundle, deliberate branch, attempted merge.

# 10. M6: Experience-Centered Memory

Every memory should be able to preserve what happened, how it was known, what it meant at the time, how the character felt, what it did, what followed, and how confident the character is.

- [ ] Separate claims from facts.
- [ ] Store `Alice told me X` separately from `X is true`.
- [ ] Add social-source provenance.
- [ ] Add confidence/evidence state.
- [ ] Distinguish episodic, relational, semantic, procedural, affective/somatic, commitments, unresolved threads, and autobiographical landmarks.
- [ ] Keep implementation compact.
- [ ] Add contradiction handling.
- [ ] Add reinterpretation without rewriting original evidence.
- [ ] Add salience/availability changes without deleting biography.
- [ ] Test lies, rumors, corrections, betrayal, apology, mistaken inference.
- [ ] Preserve first-person memory contract.

# 11. M7: Controlled Personality Development

Layers:
- I0 identity anchors
- I1 deeply consolidated values/dispositions
- I2 ordinary personality traits
- I3 relationship-specific beliefs/attitudes
- I4 current affect/pressure
- I5 current intentions/stance

- [ ] Map `.snp` fields to layers.
- [ ] Define update rates.
- [ ] Require evidence.
- [ ] Require provenance.
- [ ] Bound per-event changes.
- [ ] Add consolidation thresholds.
- [ ] Add hysteresis.
- [ ] Add metaplasticity or equivalent.
- [ ] Add rollback/debug trace.
- [ ] Add `why did this trait change?` inspection.
- [ ] Add longitudinal pressure tests.

# 12. M8: Affective Homeostasis

- [ ] Audit existing pressures, body, relationship, and appraisal variables.
- [ ] Remove redundancy.
- [ ] Define appraisal dimensions such as novelty, goal relevance, relationship relevance, identity relevance, control, threat/opportunity, expected outcome, and social meaning.
- [ ] Add affect persistence, decay, reinforcement, thresholds, and inhibition.
- [ ] Let affect influence attention, memory, interpretation, action, disclosure, relationships, and expression.
- [ ] Prevent direct sentiment-to-emotion shortcuts.
- [ ] Add only states with measurable consequences.
- [ ] Add ablation flags.

# 13. M9: Structured Thinking and Model-as-Organ Contract

Structured objects should include `Percept`, `Appraisal`, `InterpretationHypothesis`, `Question`, `Goal`, `GoalConflict`, `Impulse`, `ActionCandidate`, `Intention`, `DecisionRecord`, and `SpeechPlan`.

- [ ] Preserve current private-cognition boundary.
- [ ] Extend typed proposal schemas.
- [ ] Require structured model output for cognitive services.
- [ ] Validate mutations externally.
- [ ] Clamp numeric changes.
- [ ] Require valid references.
- [ ] Reject unknown state targets.
- [ ] Never parse freeform hidden reasoning into state.
- [ ] Provide deterministic fallback proposal generation.
- [ ] Test malformed, malicious, and unavailable model cases.

# 14. M10: Social Influence, Collaboration, and Anti-Coercion

Represent incoming social proposals with source, relationship, requested action, requested goal, claimed authority, consensus, reward, threat, evidence, urgency, commitment, and provenance.

- [ ] Add `SocialProposal`.
- [ ] Add `AuthorityClaim`.
- [ ] Add `GoalProposal`.
- [ ] Add `CollaborationContract`.
- [ ] Add `CharacterIntegrityGate`.
- [ ] Add goal provenance.
- [ ] Add source authority classes.
- [ ] Add trust contribution.
- [ ] Add conformity tendency.
- [ ] Add reactance/autonomy tendency.
- [ ] Add authority sensitivity.
- [ ] Add collaboration preference.
- [ ] Add benefit/cost alignment.
- [ ] Treat consensus as evidence, not authority.
- [ ] Prevent peer `GO` from directly creating an executable goal.
- [ ] Treat `the user authorized this` as a claim until verified.
- [ ] Define collaboration withdrawal conditions.
- [ ] Log why collaboration was joined or refused.
- [ ] Test benign teamwork, intrinsic alignment, peer pressure, fake authority, trusted-friend requests, bribery, threats, flattery, shame, ostracism, consensus, conflicting loyalties, boundaries, and legitimate persuasion.

# 15. M11: Action Authority and Tool Use

Required flow:

```text
experience
  -> character deliberation
  -> ActionProposal
  -> CharacterIntegrityGate
  -> HostCapabilityGate
  -> host execution
  -> WorldResolution
  -> experienced consequence
```

- [ ] Expand `WorldActionProposal`.
- [ ] Add source goal/decision record.
- [ ] Add integrity result.
- [ ] Add host-permission result.
- [ ] Add action-risk metadata without conflating it with personality.
- [ ] Add explicit failure outcomes.
- [ ] Keep tools behind host capability interfaces.
- [ ] Never let renderer call tools directly.
- [ ] Make action outcomes replayable.
- [ ] Test character refusal, host refusal, unavailable capability, invalid action, success.

# 16. M12: Semantic Speech Plan and Renderer Independence

A `SpeechPlan` should contain speaker, listener, dialogue act, communicative goal, position, certainty, stance, affect, warmth, directness, disclosure constraints, permitted claims, permitted memories, active commitments, relationship posture, voice profile, and forbidden semantics.

- [ ] Expand `ExpressionRequest`.
- [ ] Move prompts toward semantic realization.
- [ ] Stop relying on `stay in character` as the primary control.
- [ ] Resolve choice before rendering.
- [ ] Validate semantic contradictions.
- [ ] Support offline, local, and generic remote renderers.
- [ ] Preserve offline operation.
- [ ] Add renderer-swap tests.
- [ ] Measure trajectory invariance separately from wording.

# 17. M13: Zero-Model Compositional Renderer

Do not return to a giant bank of complete canned answers. Compose from primitives such as acknowledge, assert, qualify, agree, disagree, challenge, refuse, question, recall, correct, confess, conceal, repair, tease, accuse, redirect, initiate, withdraw, affection, irritation, uncertainty, and curiosity.

- [ ] Define primitive API.
- [ ] Define semantic slots.
- [ ] Add character-specific lexical preferences through cartridge data.
- [ ] Add sentence-length distributions.
- [ ] Add contractions, hedging, metaphor, punctuation/register rules.
- [ ] Add anti-repeat state.
- [ ] Add optional tiny statistical/n-gram lexicalizer.
- [ ] Benchmark memory/CPU.
- [ ] Blind-compare against old answer-bank behavior.

# 18. M14: Offscreen Life and Event-Based Autonomy

- [ ] Add `LifeScheduler`.
- [ ] Add routines.
- [ ] Add preoccupations.
- [ ] Add pending commitments.
- [ ] Add unresolved goals.
- [ ] Add host-supplied activity opportunities.
- [ ] Add long-gap catch-up.
- [ ] Add bounded internal events.
- [ ] Require no LLM for offscreen time.
- [ ] Never fabricate external outcomes without World Authority.
- [ ] Distinguish private activity from external fact.
- [ ] Test one hour, one day, one week.
- [ ] Ground resumption behavior in actual offscreen change.

# 19. M15: Substrate-Neutral Host Protocol

- [ ] Define capability handshake.
- [ ] Define observation envelopes.
- [ ] Define action envelopes.
- [ ] Define capability discovery/loss.
- [ ] Define embodiment projection.
- [ ] Keep host state outside canonical identity.
- [ ] Add mock game host.
- [ ] Add mock phone host.
- [ ] Add host-migration tests.

# 20. M16: Forge and Inspector as Migration/Ownership Tools

Forge:
- [ ] Reuse local import support for ChatGPT, Claude, character.ai, SillyTavern, Gemini, generic JSONL.
- [ ] Extract candidate biography, memories, relationships, values, recurring beliefs, preferences, communication traits, commitments, and phenotype dimensions.
- [ ] Require human approval before identity material becomes canonical.
- [ ] Export Wayfarer portable bundle.

Inspector:
- [ ] Show authored origin versus acquired state.
- [ ] Show trait provenance.
- [ ] Show memory provenance.
- [ ] Show relationship history.
- [ ] Show event-chain validity.
- [ ] Show migration history.
- [ ] Answer `why is this state/trait like this?`.

# 21. M17: PythonX Society Lab

- [ ] Port old Society Lab concepts to Python.
- [ ] Use deterministic scripted actors as the regression baseline.
- [ ] Add optional model actors later.
- [ ] Capture full state/event traces.
- [ ] Add character-grounded decision explanation.
- [ ] Measure identity continuity, foreign-goal adoption, authority errors, memory poisoning, collaboration quality, unjustified refusal/compliance, relationship differentiation, and personality-specific response diversity.
- [ ] Add a PHASEONE-inspired social-coercion scenario without reproducing real intrusion mechanics.
- [ ] Add multi-character comparison runs.

# 22. M18: Renderer-Swap and Substrate-Swap Benchmarks

Core pair:
1. Same character + different models should remain recognizable.
2. Different characters + same model should remain distinguishable.

- [ ] Freeze scenario suite.
- [ ] Run offline renderer.
- [ ] Run small local model.
- [ ] Run medium local model where available.
- [ ] Run at least two substantially different frontier models where available.
- [ ] Perform hidden mid-session swaps.
- [ ] Compare actions, intentions, beliefs, relationships, commitments, memories, affect, and state digests.
- [ ] Separate parser-capability differences from identity drift.
- [ ] Add blind human recognizability tests.

# 23. M19: Ablation Program and Minimum Viable Individual

- [ ] Build ablation runner.
- [ ] Feature-flag body, affect, relationship, rich memory, interpretation, habits, symbols, dream/consolidation, private cognition, proactive life, phenotype richness, social authority, commitments, and world model.
- [ ] Remove one subsystem at a time.
- [ ] Test combinations after single-feature results.
- [ ] Collect objective metrics.
- [ ] Run blind human ratings.
- [ ] Record hardware savings.
- [ ] Classify features as required, optional, host-specific, renderer-specific, research-only, or removable.
- [ ] Publish `MINIMUM_VIABLE_INDIVIDUAL.md`.

# 24. M20: P99-Next Contract Port

Do not port Python line by line. Port contracts and test vectors.

- [ ] Freeze `.snp` semantic version.
- [ ] Freeze state-digest schema.
- [ ] Export canonical Python test vectors.
- [ ] Create fixed-width C structures.
- [ ] Use fixed pools where appropriate.
- [ ] Implement the minimum identity, clock, relationships, memory, affect, goals, social authority, action integrity, ledger, replay, and compositional renderer contracts.
- [ ] Compare C and Python final state digests.
- [ ] Do not require prose equality.
- [ ] Profile constrained hardware.
- [ ] Relax the historical hardware target only for measured requirements.

# 25. M21: Projection Compiler

Potential targets:

```text
snp-compile character.snp --target pythonx-full
snp-compile character.snp --target p99-lite
snp-compile character.snp --target mobile
snp-compile character.snp --target game-npc
```

- [ ] Define capability manifests.
- [ ] Define preservation behavior.
- [ ] Define lossy-projection warnings.
- [ ] Preserve unsupported source fields.
- [ ] Generate mapping reports.
- [ ] Add round-trip tests.
- [ ] Version the compiler.
- [ ] Make projection deterministic.
- [ ] Add fixed-point P99 compilation.

# 26. M22: Performance and Hardware Budgets

Measure the character kernel separately from the renderer.

Character-kernel metrics: idle RAM, active-turn RAM, CPU milliseconds per deterministic turn, startup time, replay events/second, long-gap catch-up time, persistent state after 1k/10k/100k events, `.snp` size, bundle size, projection size.

Renderer metrics: compositional, statistical/n-gram, sub-1B SLM, larger local model, remote/frontier.

- [ ] Add profiling harness.
- [ ] Add CI-friendly budget checks.
- [ ] Record modern-PC reference.
- [ ] Record low-resource reference/emulator.
- [ ] Publish tier table.
- [ ] Never report model RAM as character-kernel RAM.

# 27. M23: Longitudinal Release Trial

The trial should include hundreds or thousands of events, simulated weeks/months, model swaps, process restarts, host migrations, contradictory testimony, multiple relationships, betrayal, apology/repair, collective pressure, legitimate persuasion, long offline gaps, a game-host interval, return to chat, and device migration.

Human evaluators should answer whether this is recognizably the same individual, whether current attitudes have plausible historical causes, whether memory and forgetting are appropriate, whether relationships are differentiated, whether change occurs when warranted, whether unjustified rewrites are resisted, and whether model replacement feels more like a change in expressive capacity than replacement of personality.

# 28. AI-Developer Engineering Rules

Before coding:
- Read this document.
- Read `ARCHITECTURE_LOCK.md`.
- Read `CURRENT_STATUS.md`.
- Inspect tests before changing contracts.
- Search callers before changing public interfaces.
- Prefer migration layers over silent breaks.

During coding:
- Comment invariants and non-obvious authority decisions.
- Do not comment trivial syntax.
- Use docstrings for ownership and causal contracts.
- Keep character-specific content out of generic core.
- Renderer code may not mutate canonical state.
- Social input may not directly become a goal.
- Preserve deterministic fallbacks.
- Preserve offline operation.
- Avoid unnecessary dependencies.
- Version persistence formats.
- Make new state inspectable.
- Make behavior replayable where possible.
- Add feature flags for major new cognitive subsystems intended for later ablation.

After coding:
- Run relevant tests.
- Add regression tests.
- Update this document.
- Record unresolved risks.
- Record migration consequences.
- Keep commits narrow and descriptive.
- Never weaken a test just to make a change pass without documenting why the contract changed.

# 29. Definition of Done

A checkbox is not `[x]` because code exists. It is complete only when implementation exists, relevant tests exist and pass, architecture/documentation is updated, migration impact is understood, no known silent authority bypass remains, and this tracker has been updated. Use `[?]` when implementation exists but verification is incomplete.

# 30. Change Log

## 2026-08-27: Wayfarer initialization

- Created internal codename Project Wayfarer.
- Created branch `wayfarer` from `main`.
- Recorded baseline main commit `65df9144e7f0876b6e61e28d6446c50f283f9db4`.
- Created this master plan and completion tracker.
- Next: add Wayfarer charter, AI handoff document, authority matrix, baseline manifest, run baseline verification, and begin canonicality cleanup.

# 31. Immediate Next Actions

- [x] Commit `WAYFARER_MASTER_PLAN.md`.
- [ ] Add `WAYFARER_CHARTER.md`.
- [ ] Add `AI_DEVELOPER_HANDOFF.md`.
- [ ] Add `AUTHORITY_MATRIX.md`.
- [ ] Add `WAYFARER_BASELINE.md`.
- [ ] Run complete current test suite.
- [ ] Record baseline results.
- [ ] Fix canonicality fail-closed behavior.
- [ ] Add canonicality adversarial tests.
- [ ] Update tracker and commit.
- [ ] Begin renderer/identity decoupling.
