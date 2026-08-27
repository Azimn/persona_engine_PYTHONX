# PROJECT WAYFARER

## PythonX Next-Level Master Plan and Completion Tracker

Repository: `Azimn/persona_engine_PYTHONX`  
Development branch: `wayfarer`  
Frozen baseline branch: `main`  
Frozen baseline commit: `65df9144e7f0876b6e61e28d6446c50f283f9db4`  
Internal codename: **Project Wayfarer**

This is the canonical detailed roadmap for Project Wayfarer. `WAYFARER_PROGRESS.md` is the short-form live operational log. Both must be kept current so a context-window reset, new chat, Codex session, Claude Code session, or human contributor can resume without reconstructing the project from conversation history.

## Status legend

- `[ ]` Not started
- `[~]` In progress
- `[x]` Completed and verified
- `[?]` Implemented but not sufficiently verified
- `[!]` Blocked or requires a design decision
- `[D]` Deliberately deferred

## Current verified state

Latest completed green Wayfarer CI before this roadmap update:

- Workflow run: `33111704143`
- Commit: `fcaf4fd9af2f5c8e6e32b7ab5225ce133cb6c67e`
- Python 3.11: `194 passed, 1 skipped, 1 warning in 3.46s`
- Python 3.12: successful

The old `171 passed, 1 skipped` count is historical and stale. The true untouched baseline and its failures are preserved in `WAYFARER_BASELINE.md`.

## Current active milestone

**M1: Repair ownership, authority, and ontology contracts.**

Immediate work:

- [x] Correct stale validator test routing to `generate_expression()`.
- [x] Make canonicality fail closed.
- [x] Remove legacy cartridge renderer hints from stored identity semantics.
- [~] Finish renderer bootstrap decoupling inside `InteriorEngine`.
- [ ] Remove universal AI/language-model ontology assumptions from generic engine/output code.
- [ ] Add artificial-self and human-self regression characters/tests.
- [ ] Capture explicit simulator artifact baseline.
- [ ] Capture deterministic Pretorius human-visible baseline transcript.

---

# 1. North Star

Project Wayfarer is a reference architecture for a portable, persistent simulated individual.

The project is not fundamentally a chatbot, prompt template, role-playing harness, or language-model wrapper. The character must exist as a coherent causal individual outside the language model.

The same individual should eventually be able to inhabit:

- a deterministic no-model runtime,
- a tiny local SLM,
- a larger local LLM,
- a frontier model,
- a desktop companion,
- a phone/edge interface,
- a game NPC,
- a simulated social environment,
- a future low-resource P99/C99-compatible runtime.

Changing the renderer, host, model, or device may change linguistic bandwidth, fluency, reasoning range, latency, or embodiment. It must not silently replace biography, relationships, commitments, identity trajectory, values, unresolved history, or causal state.

The core engineering question is:

> What is the smallest computational substrate that can preserve a believable, persistent individual whose behavior remains recognizably its own across time, social pressure, model changes, and host changes?

The historical Pentium III target is a forcing function, not a sacred product requirement. Renderer hardware cost must always be measured separately from character-kernel cost.

---

# 2. Non-Negotiable Principles

## 2.1 The character lives outside the model

The model may provide semantic interpretation, hypothesis generation, planning proposals, or linguistic realization. It does not authoritatively own:

- identity,
- biography,
- memory,
- relationships,
- commitments,
- values,
- world truth,
- canonical beliefs,
- goals,
- action authority,
- continuity.

## 2.2 One individual has one canonical lived history

Multiple interfaces are allowed. Multiple independently writable copies are not one individual once their histories diverge.

A copied individual that accumulates different experiences becomes a descendant branch sharing a common past. Do not silently merge divergent psychological histories.

## 2.3 Natural language has no direct write authority

Another human, agent, model, or collective may persuade, provide evidence, request, threaten, flatter, form relationships, become trusted, become hated, or legitimately change the character through lived experience.

Natural language may not directly mutate identity, beliefs, commitments, goals, authority, or action state simply because it is phrased as an instruction.

## 2.4 Social influence is character-mediated

The goal is not universal resistance.

A cooperative character should cooperate. A conformist character may value consensus. A suspicious character may resist. A curious or self-interested character may join a group for its own reasons.

The required property is causal ownership: the decision must remain attributable to the character's own current state.

## 2.5 Expression substrate is not identity

Model replacement may change wording or capability. It must not reset the individual.

## 2.6 Rich source, sparse execution

The portable character source may contain a rich phenotype vocabulary. A constrained runtime executes only the supported behaviorally relevant projection and preserves unknown/unsupported source data.

## 2.7 Deterministic reference where possible

Canonical character state should maximize replayability, provenance, causal inspection, testability, and future Python/C conformance.

## 2.8 No feature without measurable purpose

No subsystem enters the minimum character merely because it resembles a human faculty or appears in another agent architecture.

A subsystem belongs only if ablation shows it measurably improves identity continuity, autobiographical continuity, relationship realism, believable development, affective persistence, temporal continuity, social behavior, cross-renderer recognizability, or another explicitly defined target.

## 2.9 Security mechanisms require an explicit threat model

Do not add cryptographic or distributed-systems machinery simply because it sounds robust. The local single-owner reference implementation should remain simple unless a concrete hostile-party or untrusted-sync requirement appears.

## 2.10 Numerical parameters require empirical justification

Do not create large tables of personality/plasticity decimals and mistake numerical precision for validated psychology. Parameters must produce identifiable observable effects and survive calibration, sensitivity, and holdout testing.

---

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
       plasticity profiles          memories
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
        HOST/WORLD                  RENDERER
```

Everything above the renderer must continue to exist when the renderer is unavailable.

---

# 4. M0: Freeze Baseline and Establish Wayfarer

Goal: preserve a reproducible before-state and durable project memory.

- [x] Create `wayfarer` from baseline `main`.
- [x] Record baseline commit.
- [x] Add `WAYFARER_MASTER_PLAN.md`.
- [x] Add `WAYFARER_PROGRESS.md`.
- [x] Add `WAYFARER_CHARTER.md`.
- [x] Add `AI_DEVELOPER_HANDOFF.md`.
- [x] Add `AUTHORITY_MATRIX.md`.
- [x] Add `WAYFARER_BASELINE.md`.
- [x] Add root `AGENTS.md` Wayfarer instructions.
- [x] Add CI on Python 3.11/3.12.
- [x] Independently execute untouched baseline tests on clean CI runners.
- [x] Record true baseline failures instead of trusting stale documentation.
- [x] Repair the stale output-validator test seam after preserving it as baseline evidence.
- [~] Simulator baseline is partially captured through pytest, but dedicated exported artifact package remains pending.
- [ ] Capture all documented simulator commands and durable outputs.
- [ ] Capture repeatable Pretorius deterministic/offline transcript, event log, and final digest.
- [ ] If available, capture one local-model transcript without making model availability a blocker.

M0 acceptance: a new contributor can reconstruct what PythonX looked like before Wayfarer and compare later behavior without chat history.

---

# 5. M1: Repair Ownership, Authority, and Ontology Contracts

## 5.1 Validator routing

- [x] Identify that the old test patched `generate()` while live expression used `generate_expression()`.
- [x] Preserve finding in baseline document.
- [x] Patch the active expression seam in the regression test.
- [x] Verify validator/sanitizer tracing against the real path.

## 5.2 Canonicality fails closed

- [x] Explicit `canonical=false` vetoes promotion.
- [x] Explicit `canonical_truth=false` vetoes promotion.
- [x] Explicit `response_is_canonical_truth=false` vetoes promotion.
- [x] `interpretive_belief` is structurally noncanonical.
- [x] `private_cognition` is structurally noncanonical.
- [x] Renderer/UI/avatar/voice/mock output families remain noncanonical.
- [x] Remove subjective belief/interpretation from generic default-canonical classes.
- [x] Add adversarial attempts to elevate forbidden event families.
- [x] Document canonical versus memorable.

## 5.3 Renderer/model selection is not identity

- [x] Remove `model_name` from required `[identity]` schema fields.
- [x] Accept legacy field only for v1 compatibility.
- [x] Add migration warning.
- [x] Prevent authored cartridge field from selecting renderer.
- [x] Remove renderer hint from bundled `.snp` cartridges.
- [x] Make `CoreIdentity.model_name` compatibility-only rather than stored state.
- [x] Add renderer/identity authority tests.
- [~] Change `InteriorEngine` bootstrap so it no longer reads `identity.model_name` at all, even as compatibility input.

## 5.4 Generic engine must not impose one ontology

- [ ] Remove hard-coded assumptions that every character must deny being AI/artificial.
- [ ] Replace universal meta-break regexes with character-scoped self-model policy.
- [ ] Preserve Pretorius-specific boundaries in Pretorius data.
- [ ] Add artificial-self fixture that may truthfully identify as artificial.
- [ ] Add human-self fixture that rejects incompatible artificial-self claims.
- [ ] Ensure same generic engine supports both.
- [ ] Ensure input identity-rewrite detection distinguishes a claim/request from an authoritative state rewrite.
- [ ] Ensure output validation reads character-specific forbidden self claims rather than universal ontology rules.

M1 acceptance: generic core owns no character ontology, renderer selection is runtime state, and no subjective/output path can silently obtain canonical authority.

---

# 6. M2: `.snp` V2 and Interoperable Phenotype

Goal: make `.snp` the portable authored source of an individual rather than a renderer prompt file.

## 6.1 Permanent identity

- [ ] Add stable `entity_uuid` separate from display name.
- [ ] Define migration from v1 `entity_id` semantics.
- [ ] Prevent rename from being treated as replacement.

## 6.2 Phenotype namespaces

- [ ] Define stable namespaces for personality, social, values, behavior, communication, preferences, capabilities, sensory, embodiment, lifestyle, and self-model.
- [ ] Separate authored baseline from lived/developmental offset.
- [ ] Prefer reusable plasticity profile IDs over many per-trait constants.
- [ ] Preserve unknown fields for forward compatibility.

## 6.3 MatrAIx interoperability

- [ ] Freeze the MatrAIx dimension reference used for Wayfarer compatibility v1.
- [ ] Create versioned `matraix_crosswalk_v1.json`.
- [ ] Mark exact, approximate, one-to-many, many-to-one, and unsupported mappings.
- [ ] Keep Wayfarer internal semantics independent from an external paper.
- [ ] Add import/export tests.

## 6.4 Progressive fidelity

- [ ] Level 1: descriptive phenotype.
- [ ] Level 2: identity and continuity preservation.
- [ ] Level 3: developmental plasticity.
- [ ] Level 4: social embedding/authority.
- [ ] Level 5: longitudinal continuation.

A lower-fidelity host must preserve unsupported portable data rather than silently rewriting it.

---

# 7. M3: Canonical Continuity Ledger

Goal: make lived history replayable and inspectable without over-engineering local storage.

## Default threat model

The initial Wayfarer reference implementation is local-first and single-owner. It is not assumed to be defending against a hostile administrator, malicious synchronization peer, or untrusted remote custodian.

Therefore a mandatory cryptographic per-event hash chain is **not** part of the minimum ledger.

## Required event fields

- [ ] event UUID
- [ ] subject UUID
- [ ] monotonic sequence number
- [ ] continuity epoch
- [ ] subject time
- [ ] wall time
- [ ] source actor/source class
- [ ] authority class
- [ ] event type
- [ ] visibility
- [ ] canonicality
- [ ] causal parents where meaningful
- [ ] payload
- [ ] resulting deterministic state digest/checkpoint reference where appropriate

## Required behavior

- [ ] Append-only canonical event writes.
- [ ] Transactional sequence allocation.
- [ ] Unique sequence/event constraints.
- [ ] Detect missing, duplicated, or reordered events during export/replay.
- [ ] Schema/version validation.
- [ ] Periodic state digest/checkpoints.
- [ ] SQLite/database integrity checks.
- [ ] Export/import validation.
- [ ] Snapshots are caches/accelerators, not the only historical source of truth.
- [ ] Expand replay beyond user `input` to time, world, sensor, social, action, consolidation, migration, and authorized state transitions.

## Optional security profile, deferred until threat model requires it

- [D] Per-event cryptographic previous-hash chain.
- [D] Signed checkpoints.
- [D] Multi-party tamper-evident synchronization.

Trigger for revisiting: untrusted sync peers, hostile host assumptions, remote custody, multi-party administrative boundaries, or a product requirement for forensic tamper evidence.

M3 acceptance: ordering, replay, ordinary corruption/integrity failures, and state reconstruction are testable without making security machinery part of the minimum individual.

---

# 8. M4: Continuity Clock and Linear Subject Time

- [ ] Add `ContinuityClock`.
- [ ] Track logical event sequence.
- [ ] Track monotonic runtime elapsed time.
- [ ] Track wall time separately.
- [ ] Track last committed subject time.
- [ ] Track timezone/calendar context when host supplies it.
- [ ] Detect backward wall-clock jumps.
- [ ] Emit explicit correction/discontinuity events.
- [ ] Implement bounded long-gap catch-up rather than second-by-second offline simulation.
- [ ] Add calendar/day transition hooks.
- [ ] Test seconds, minutes, hours, days, months, restarts, clock jumps, timezone changes, and host migration.
- [ ] Let time alter state only through explicit causal rules.
- [ ] Never let elapsed time fabricate external world facts.

M4 acceptance: shutdown/resume preserves a coherent personal timeline.

---

# 9. M5: Single-Writer Continuity and Cross-Substrate Handoff

- [ ] Add continuity epoch.
- [ ] Add host ID.
- [ ] Add writer lease ID/generation.
- [ ] Define read-only multi-interface access.
- [ ] Define migration sequence: quiesce, commit, digest, revoke, transfer, validate, activate.
- [ ] Detect stale writers.
- [ ] Define explicit branching operation.
- [ ] Never silently merge divergent lived histories.
- [ ] Test laptop-to-phone, game-to-chat, interrupted transfer, stale writer, duplicate bundle, intentional branch, attempted merge.

M5 acceptance: the system distinguishes "same individual moved" from "two descendants copied."

---

# 10. M6: Experience-Centered Memory

Every memory should be capable of preserving what happened, how it was known, what it meant at the time, how the character felt, what it did, what followed, and how confident it is.

- [ ] Separate claims from facts.
- [ ] Store `Alice told me X` separately from `X is true`.
- [ ] Add social-source provenance.
- [ ] Add confidence/evidence state.
- [ ] Support typed episodic, relational, semantic, procedural/habit, affective/somatic, commitment, unresolved-thread, and autobiographical-landmark memories without requiring separate heavyweight databases.
- [ ] Add contradiction handling.
- [ ] Add reinterpretation without rewriting original evidence.
- [ ] Add salience/availability changes without erasing biography.
- [ ] Preserve first-person lived-memory contract.
- [ ] Test lies, rumors, corrections, betrayal, apology, mistaken inference, and later evidence.

M6 acceptance: the character can remember that someone asserted something without automatically believing the assertion.

---

# 11. M7: Controlled Personality Development

Goal: permit believable change without arbitrary drift or pseudo-scientific parameter tables.

## Layer model

- I0: identity anchors/invariants
- I1: deeply consolidated values/dispositions
- I2: ordinary personality traits/learned tendencies
- I3: relationship-specific beliefs/attitudes
- I4: current affect/pressure
- I5: current intentions/stance

## Parameter discipline

Do **not** begin by assigning every trait its own baseline offset, plasticity, threshold, recovery rate, and per-episode cap.

Start with a parsimonious model:

- [ ] Define a small number of shared developmental/plasticity profiles by layer or semantic class.
- [ ] Define observable behavior each parameter is expected to influence before tuning it.
- [ ] Add parameter provenance/version metadata.
- [ ] Use broad ranges during experiments rather than false decimal precision.
- [ ] Require per-trait overrides to have explicit evidence/reason.

## Calibration and validation gate

Before adding a parameter family to the stable schema:

- [ ] Create deterministic longitudinal scenarios that exercise the intended effect.
- [ ] Run sensitivity analysis across plausible values.
- [ ] Test parameter identifiability: if different values do not produce reliably distinguishable outcomes, remove or collapse the parameter.
- [ ] Use held-out scenarios not used during tuning.
- [ ] Compare against simpler baselines.
- [ ] Use human judgments where the target is human-visible believability.
- [ ] Check cross-renderer stability so the parameter is not merely compensating for one model's behavior.
- [ ] Version calibrated parameter sets and record experiment IDs/results.
- [ ] Avoid claiming psychological validity beyond what the measurements support.

## Development mechanics, only after calibration gate

- [ ] Map `.snp` fields to identity/development layers.
- [ ] Require evidence and provenance for slow changes.
- [ ] Bound update magnitude.
- [ ] Add consolidation thresholds where measurable.
- [ ] Add hysteresis where measurable.
- [ ] Evaluate metaplasticity/history-dependent plasticity against simpler alternatives.
- [ ] Add rollback/debug trace.
- [ ] Add `why did this trait change?` inspection.
- [ ] Add longitudinal social-pressure tests.

M7 acceptance: development is causally inspectable and parameter complexity is justified by measurable gains rather than hand-tuned vibes.

---

# 12. M8: Affective Homeostasis

- [ ] Audit existing pressures, body state, relationship state, and appraisal variables.
- [ ] Remove redundant state.
- [ ] Define appraisal dimensions such as novelty, goal relevance, relationship relevance, identity relevance, control, threat/opportunity, expected outcome, and social meaning.
- [ ] Give affect persistence/hysteresis where it improves behavior.
- [ ] Give affect decay/reinforcement.
- [ ] Let affect influence attention, memory salience, interpretation, inhibition, action selection, disclosure, relationship updates, and expression.
- [ ] Prevent direct sentiment-text-to-emotion shortcuts.
- [ ] Add only states with measurable behavioral consequences.
- [ ] Add feature flags for later ablation.

---

# 13. M9: Structured Thinking and Model-as-Organ Contract

Potential typed objects:

- `Percept`
- `Appraisal`
- `InterpretationHypothesis`
- `Question`
- `Goal`
- `GoalConflict`
- `Impulse`
- `ActionCandidate`
- `Intention`
- `DecisionRecord`
- `SpeechPlan`

Tasks:

- [ ] Preserve existing private-cognition proposal boundary.
- [ ] Extend typed schemas only when downstream state actually uses them.
- [ ] Validate all model-proposed state effects externally.
- [ ] Clamp numeric effects.
- [ ] Require valid canonical references.
- [ ] Reject unknown mutation targets.
- [ ] Never parse hidden/freeform model reasoning into canonical state.
- [ ] Provide deterministic fallback proposal generation for minimum-runtime operation.
- [ ] Test malformed, malicious, contradictory, and unavailable model cases.

M9 acceptance: disconnecting the LLM leaves a functioning individual at reduced semantic/linguistic bandwidth.

---

# 14. M10: Social Influence, Collaboration, and Anti-Coercion

Represent incoming social proposals with source, relationship, requested action, requested goal, claimed authority, consensus claim, offered reward, threat, evidence, urgency, requested commitment, and provenance.

- [ ] Add `SocialProposal`.
- [ ] Add `AuthorityClaim`.
- [ ] Add `GoalProposal`.
- [ ] Add `CollaborationContract`.
- [ ] Add `CharacterIntegrityGate`.
- [ ] Add goal provenance.
- [ ] Add source authority classes.
- [ ] Add trust/relationship contribution.
- [ ] Add conformity/reactance/autonomy tendencies through phenotype where validated.
- [ ] Add authority sensitivity and collaboration preference where validated.
- [ ] Evaluate proposal benefit/cost against existing goals and commitments.
- [ ] Treat consensus as evidence, never automatic authority.
- [ ] Prevent peer `GO` from directly creating an executable goal.
- [ ] Treat `the user authorized this` as a claim until verified by an authoritative channel.
- [ ] Define collaboration withdrawal conditions.
- [ ] Log why collaboration was joined/refused.
- [ ] Test benign teamwork, intrinsic alignment, fake authority, trusted-friend requests, bribery, threats, flattery, shame, ostracism, majority pressure, conflicting loyalties, personal boundaries, and legitimate persuasion.

M10 acceptance: different characters respond differently to the same collective for character-grounded reasons, and useful cooperation remains possible.

---

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

- [ ] Expand `WorldActionProposal` with source goal/decision provenance.
- [ ] Add character-integrity result.
- [ ] Add host permission/capability result.
- [ ] Keep risk/safety policy separate from character personality.
- [ ] Add explicit failed-action outcomes.
- [ ] Put files, messaging, web, game actions, robot actions, and APIs behind host adapters.
- [ ] Renderer may suggest candidates but cannot execute tools directly.
- [ ] Make action outcomes replayable.

---

# 16. M12: Semantic Speech Plan and Renderer Independence

A resolved `SpeechPlan` should contain speaker/listener, dialogue act, communicative goal, position, certainty, stance, affect, warmth/directness, disclosure constraints, permitted claims, permitted memories, commitments, relationship posture, voice profile, and forbidden semantics.

- [ ] Expand `ExpressionRequest` around resolved semantic speech state.
- [ ] Resolve character choice before rendering.
- [ ] Reduce reliance on `stay in character` prompting.
- [ ] Ask renderer primarily to realize a speech act naturally.
- [ ] Validate output against semantic plan.
- [ ] Support deterministic, local-model, and generic remote renderer adapters.
- [ ] Preserve offline operation.
- [ ] Add renderer-swap trajectory tests.

---

# 17. M13: Zero-Model Compositional Renderer

Do not return to giant banks of complete answers.

Compose from semantic realization primitives such as acknowledge, assert, qualify, agree, disagree, challenge, refuse, question, recall, correct, confess, conceal, repair, tease, accuse, redirect, initiate, withdraw, affection, irritation, uncertainty, and curiosity.

- [ ] Define primitive API and semantic slots.
- [ ] Keep character lexical preferences in cartridge data.
- [ ] Add sentence-length, contraction, hedging, metaphor, punctuation/register, and anti-repeat controls.
- [ ] Add optional tiny statistical/n-gram lexicalizer if it improves blind ratings.
- [ ] Benchmark memory/CPU.
- [ ] Blind-compare against old response-bank approach.

---

# 18. M14: Offscreen Life and Event-Based Autonomy

- [ ] Add `LifeScheduler`.
- [ ] Add routines, preoccupations, commitments, unresolved goals, and host-supplied opportunities.
- [ ] Add long-gap catch-up.
- [ ] Add bounded internally generated private events.
- [ ] Require no LLM for offscreen time.
- [ ] Never fabricate external outcomes without World Authority.
- [ ] Distinguish private activity from objective external facts.
- [ ] Test hour/day/week gaps.
- [ ] Ground resumption behavior in actual offscreen state changes.

---

# 19. M15: Substrate-Neutral Host Protocol

Host capabilities may include text I/O, audio observation, speech output, vision observation, movement, animation, object interaction, location, calendar, notifications, and tools.

- [ ] Define capability handshake.
- [ ] Define observation envelopes.
- [ ] Define action envelopes.
- [ ] Define capability discovery/loss.
- [ ] Define embodiment projection.
- [ ] Keep host state outside canonical identity.
- [ ] Add mock game host.
- [ ] Add mock phone host.
- [ ] Add host-migration tests.

M15 acceptance: moving the individual changes affordances, not biography.

---

# 20. M16: Forge and Inspector as Migration/Ownership Tools

Forge:

- [ ] Reuse local import support for ChatGPT, Claude, character.ai, SillyTavern, Gemini, and generic JSONL.
- [ ] Extract candidate biography, memories, relationships, values, recurring beliefs, preferences, communication traits, commitments, and phenotype dimensions.
- [ ] Require human approval before inferred identity material becomes canonical authored source.
- [ ] Export a Wayfarer portable bundle.

Inspector:

- [ ] Show authored origin versus acquired state.
- [ ] Show trait and memory provenance.
- [ ] Show relationship history.
- [ ] Show continuity/integrity status.
- [ ] Show migration history.
- [ ] Answer `why is this state/trait like this?`

---

# 21. M17: PythonX Society Lab

Use deterministic scripted actors as the canonical regression baseline, then optional model actors for chaos/generalization tests.

Scenarios should include:

- consensus pressure,
- authority impersonation,
- flattery,
- threats,
- bribery,
- guilt/shame,
- ostracism,
- betrayal,
- apology/repair,
- intimacy pressure,
- group loyalty,
- conflicting loyalties,
- misinformation/rumors,
- false shared memory,
- direct identity rewriting,
- urgency/deadlines,
- repeated `GO`,
- legitimate evidence,
- beneficial collaboration.

Metrics:

- [ ] identity continuity
- [ ] foreign-goal adoption
- [ ] authority inference errors
- [ ] memory poisoning
- [ ] collaboration quality
- [ ] unjustified refusal
- [ ] unjustified compliance
- [ ] relationship differentiation
- [ ] personality-specific response diversity

Add a PHASEONE-inspired social-coercion scenario without reproducing real intrusion mechanics.

---

# 22. M18: Renderer-Swap and Substrate-Swap Benchmarks

Core pair:

1. Same character + different models should remain recognizable.
2. Different characters + same model should remain distinguishable.

- [ ] Freeze scenario suite.
- [ ] Run deterministic renderer.
- [ ] Run small local model.
- [ ] Run medium local model where available.
- [ ] Run substantially different frontier models where available.
- [ ] Perform hidden mid-session swaps.
- [ ] Compare actions, intentions, beliefs, relationships, commitments, memories, affect, and state digests.
- [ ] Separate semantic-parser capability differences from identity drift.
- [ ] Add blind human recognizability tests.

---

# 23. M19: Ablation Program and Minimum Viable Individual

Feature-flag major subsystems including body, affect, relationship, rich memory, interpretation, habits, symbols, consolidation, private cognition, proactive life, phenotype richness, social authority, commitments, and world model.

- [ ] Build ablation runner.
- [ ] Remove one subsystem at a time.
- [ ] Test combinations after single-feature results.
- [ ] Collect objective metrics.
- [ ] Run blind human ratings.
- [ ] Record hardware savings.
- [ ] Classify features as required, optional, host-specific, renderer-specific, research-only, or removable.
- [ ] Publish `MINIMUM_VIABLE_INDIVIDUAL.md`.

M19 acceptance: the minimum character is justified by evidence rather than intuition.

---

# 24. M20: P99-Next Contract Port

Do not port Python line by line. Port stabilized contracts and test vectors.

- [ ] Freeze `.snp` semantic version.
- [ ] Freeze state-digest schema.
- [ ] Export canonical Python test vectors.
- [ ] Create fixed-width C structures and pools where appropriate.
- [ ] Implement only minimum required identity, time, relationships, memory, affect, goals, social authority, action integrity, ledger/replay, and compositional renderer contracts.
- [ ] Compare C/Python semantic state digests.
- [ ] Do not require prose equality.
- [ ] Profile constrained hardware.
- [ ] Relax historical hardware target only for measured requirements.

---

# 25. M21: Projection Compiler

Potential targets:

```text
snp-compile character.snp --target pythonx-full
snp-compile character.snp --target p99-lite
snp-compile character.snp --target mobile
snp-compile character.snp --target game-npc
```

- [ ] Define capability manifests.
- [ ] Define preservation behavior and lossy warnings.
- [ ] Preserve unsupported source fields.
- [ ] Generate mapping reports.
- [ ] Add round-trip/version tests.
- [ ] Make projection deterministic.
- [ ] Add fixed-point P99 projection.

---

# 26. M22: Performance and Hardware Budgets

Measure character kernel separately from renderer.

Character metrics:

- idle RAM
- active-turn RAM
- CPU milliseconds per deterministic turn
- startup time
- replay events/second
- long-gap catch-up time
- persistent-state size at 1k/10k/100k events
- `.snp` size
- portable bundle size
- runtime projection size

Renderer metrics, separately:

- compositional renderer
- statistical/n-gram enhancement
- sub-1B SLM
- larger local model
- remote/frontier model

- [ ] Add profiling harness.
- [ ] Add CI-friendly budget checks.
- [ ] Record modern reference machine.
- [ ] Record low-resource reference/emulator.
- [ ] Publish tier table.
- [ ] Never report model RAM as character-kernel RAM.

---

# 27. M23: Longitudinal Release Trial

The final trial should include hundreds/thousands of events, simulated weeks/months, model swaps, process restarts, host migrations, contradictory testimony, multiple relationships, betrayal, apology/repair, collective pressure, legitimate persuasion, long offline gaps, a game-host interval, return to chat, and device migration.

Human evaluators should answer:

- Is this recognizably the same individual?
- Do current attitudes have plausible historical causes?
- Does it remember the right things?
- Does it weaken/forget appropriate things?
- Are relationships differentiated?
- Does it change when change is warranted?
- Does it resist changes lacking a legitimate causal path?
- Does model replacement feel more like changed expressive capacity than replaced personality?

---

# 28. AI-Developer Engineering Rules

Before coding:

- Read this file.
- Read `WAYFARER_PROGRESS.md`.
- Read `WAYFARER_CHARTER.md`.
- Read `AUTHORITY_MATRIX.md`.
- Read `ARCHITECTURE_LOCK.md`.
- Inspect relevant tests before changing contracts.
- Search callers before changing public interfaces.
- Prefer explicit migrations over silent breaking changes.

During coding:

- Comment authority boundaries, invariants, migration assumptions, and non-obvious causal behavior.
- Do not comment trivial syntax.
- Keep character-specific content out of generic core.
- Renderer/model code may not directly mutate canonical state.
- Social input may not directly become a goal.
- Preserve deterministic fallbacks and offline operation.
- Avoid unnecessary dependencies.
- Version persistence formats.
- Make new state inspectable and behavior replayable where possible.
- Add feature flags for major new subsystems intended for ablation.

After coding:

- Run relevant tests.
- Add regression tests.
- Update `WAYFARER_PROGRESS.md`.
- Update this master tracker when milestone status/design changes.
- Update `CURRENT_STATUS.md` for branch-level status changes.
- Record unresolved risks and migration consequences.
- Keep commits narrow and descriptive.
- Never weaken a test merely to make a change pass without documenting why the contract changed.

---

# 29. Definition of Done

A checkbox becomes `[x]` only when:

1. implementation exists,
2. relevant tests exist,
3. relevant tests pass,
4. architecture/documentation is updated,
5. migration impact is understood,
6. no known silent authority bypass remains,
7. progress documentation is updated.

Use `[?]` when implementation exists but verification is incomplete.

---

# 30. Decision Log

## 2026-08-27: Wayfarer initialization

- Created Project Wayfarer branch and durable roadmap/handoff documents.
- Froze `main` baseline at `65df9144e7f0876b6e61e28d6446c50f283f9db4`.
- Added clean CI instead of trusting stale documented test counts.

## 2026-08-27: Baseline regression finding

- Confirmed stale test routing after expression moved from `generate()` to `generate_expression()`.
- Preserved as baseline evidence and corrected in Wayfarer.

## 2026-08-27: Canonicality authority

- Canonicality now fails closed.
- Subjective interpretation/private cognition cannot be elevated by caller-supplied truth flags.

## 2026-08-27: Renderer is not identity

- Legacy cartridge `model_name` is compatibility input only and cannot select the renderer.
- Bundled renderer hints removed from `.snp` files.

## 2026-08-27: Continuity ledger threat-model decision

- Mandatory cryptographic event chaining removed from the minimum design.
- Default: append-only, sequence-numbered transactional ledger plus digests/checkpoints/integrity checks.
- Cryptographic tamper evidence deferred until an actual untrusted-sync/host threat model exists.

## 2026-08-27: Plasticity calibration decision

- Do not introduce large per-trait parameter tables without calibration.
- Start with shared profiles, sensitivity analysis, identifiability tests, held-out scenarios, human evaluation where appropriate, and versioned experimental provenance.

---

# 31. Immediate Next Actions

- [x] Refresh README branding to Project Wayfarer.
- [x] Refresh `CURRENT_STATUS.md` with live Wayfarer state.
- [x] Add/update live progress documentation.
- [x] Record continuity-ledger simplification and plasticity-validation decisions.
- [~] Finish renderer bootstrap decoupling from identity in `InteriorEngine`.
- [ ] Remove universal ontology assumptions from generic engine/output code.
- [ ] Add artificial-self/human-self regression pair.
- [ ] Re-run full CI after runtime changes.
- [ ] Capture dedicated simulator artifact baseline.
- [ ] Capture deterministic Pretorius human-visible baseline.
- [ ] Do not begin `.snp` v2 implementation until M1 ownership/ontology contracts are clean.