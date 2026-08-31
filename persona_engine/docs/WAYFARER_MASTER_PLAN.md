# PROJECT WAYFARER

## PythonX Next-Level Master Plan and Completion Tracker

Repository: `Azimn/persona_engine_PYTHONX`  
Development branch: `wayfarer`  
Frozen baseline branch: `main`  
Frozen baseline commit: `65df9144e7f0876b6e61e28d6446c50f283f9db4`  
Internal/project name: **Project Wayfarer**

This file is the canonical long-form roadmap for the Wayfarer development line. `WAYFARER_PROGRESS.md` is the shorter live operational status. Both files must be updated as work progresses so a new ChatGPT conversation, context refresh, Codex session, Claude Code session, or human contributor can resume without reconstructing decisions from chat history.

## Status legend

- `[ ]` Not started
- `[~]` In progress
- `[x]` Completed and verified
- `[?]` Implemented but not sufficiently verified
- `[!]` Blocked or requires an explicit design decision
- `[D]` Deliberately deferred

## Current checkpoint

M1 runtime ownership and authority repair is complete.

The ordered M1 runtime pass produced:

- renderer/identity decoupling commit `c064c3d4fdedfd08668171b26fc9e26cb8443c70`
- ontology-decoupling commit `ba78a1cfccb1f0e78aa46ea41a5e251f54bdfca0`

Verification inside GitHub Actions run `33174272164`:

```text
Renderer/identity targeted tests: 7 passed
M1 ontology + renderer + engine targeted tests: 21 passed
Full Python 3.11 suite: 198 passed, 1 skipped, 1 warning in 3.47s
```

The next work is to finish the remaining M0 evidence capture, confirm normal two-version CI, then begin M2 `.snp` v2 design.

---

# 1. North Star

Project Wayfarer is a reference architecture for a portable, persistent simulated individual.

The project is not fundamentally a chatbot, prompt template, role-playing harness, or language-model wrapper. The character must exist as a coherent causal individual outside the language model.

The same individual should eventually be able to inhabit:

- a frontier-model chat interface,
- a local LLM or SLM,
- a deterministic no-model runtime,
- a phone or edge device,
- a desktop companion,
- a game NPC,
- a simulated social environment,
- a future low-resource P99/C99-compatible runtime.

Changing renderer, host, device, or model may change linguistic bandwidth, fluency, semantic reach, or embodiment. It must not silently replace biography, relationships, commitments, identity trajectory, values, unresolved history, or causal state.

The central engineering question is:

> What is the smallest computational substrate that can preserve a believable, persistent individual whose behavior remains recognizably its own across time, social pressure, model changes, and host changes?

The historical Pentium III-class target remains a forcing function rather than a sacred requirement. It exists to prevent the character kernel from assuming neural-scale hardware. Renderer costs must always be measured separately from character-kernel costs.

---

# 2. Non-Negotiable Principles

## 2.1 The character lives outside the model

A model may provide semantic interpretation, proposal generation, planning assistance, or linguistic realization. It is not authoritative over identity, biography, memory, relationships, commitments, values, world truth, canonical beliefs, goals, action authority, or continuity.

## 2.2 One individual has one canonical lived history

Multiple interfaces are acceptable. Multiple independent writable copies are not one individual after their experiences diverge.

If a character is copied and both copies accumulate different experiences, the result is a branch into descendants sharing a common past. Do not silently merge divergent psychological histories.

## 2.3 Natural language has no direct write authority over identity

Another person, agent, model, or collective may persuade, provide evidence, make requests, threaten, flatter, form relationships, become trusted, become hated, offer collaboration, and legitimately change the character through experience.

Natural language may not directly mutate identity, beliefs, commitments, goals, authority, or executable intention simply because it is phrased as an instruction.

## 2.4 Social influence remains character-mediated

The goal is not universal refusal.

A cooperative character should cooperate. A conformist character may be strongly influenced by consensus. A suspicious character may resist. A character may join a collective because it is loyal, curious, self-interested, frightened, ambitious, persuaded by evidence, or aligned with the collective's purpose.

The required property is causal ownership: the decision must remain attributable to that character's own current state.

## 2.5 Expression substrate is not identity

A model swap must not reset the individual. Different models may change wording and semantic bandwidth, but they must not independently own character trajectory.

## 2.6 Rich source, sparse execution

The portable character source may be richer than any individual runtime projection. A MatrAIx-compatible phenotype may contain a large descriptive vocabulary without forcing a constrained runtime to evaluate every dimension on every turn.

Unsupported portable fields must be preserved rather than destroyed.

## 2.7 Deterministic behavior is the reference where practical

Canonical character machinery should maximize replayability, provenance, causal inspection, testability, and cross-language conformance. Stochastic model output is optional assistance, not the only source of character behavior.

## 2.8 No feature without observable purpose

No new cognitive subsystem enters the minimum core merely because it resembles a human faculty or sounds sophisticated.

A subsystem earns a place when disabling it measurably degrades identity continuity, relationship realism, autobiographical continuity, believable development, affective persistence, social behavior, temporal continuity, cross-renderer recognizability, or another explicitly defined target property.

---

# 3. Target Reference Architecture

```text
                    PORTABLE INDIVIDUAL
                           |
             +-------------+-------------+
             |                           |
       character.snp               continuity state
       authored origin              lived biography
       phenotype                    relationships
       identity anchors             beliefs
       values                       memories
       dispositions                 commitments
       plasticity rules             consequences
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

Everything above the renderer must remain meaningful if the renderer is removed.

---

# 4. M0: Freeze Baseline and Establish Durable Project Memory

Goal: preserve a reproducible before-state and make the repository, not the chat, the project memory.

- [x] Create `wayfarer` from frozen `main`.
- [x] Record baseline commit `65df9144e7f0876b6e61e28d6446c50f283f9db4`.
- [x] Add Wayfarer master roadmap.
- [x] Add live progress tracker.
- [x] Add `WAYFARER_CHARTER.md`.
- [x] Add `AI_DEVELOPER_HANDOFF.md`.
- [x] Add `AUTHORITY_MATRIX.md`.
- [x] Add `WAYFARER_BASELINE.md`.
- [x] Add root `AGENTS.md` Wayfarer instructions.
- [x] Add GitHub Actions CI for Python 3.11 and 3.12.
- [x] Independently execute the untouched baseline in clean GitHub-hosted runners.
- [x] Record the true stale-test and simulator findings rather than rewriting history.
- [ ] Explicitly run/export every documented deterministic simulator as a durable evidence package.
- [ ] Capture one repeatable Pretorius deterministic/offline human-visible transcript package.
- [ ] Include event/state evidence and renderer status with the Pretorius package.
- [D] Optional local-model baseline transcript may be captured when a suitable local model is available; it does not block M0.

Acceptance: a new contributor can understand and reproduce the pre-Wayfarer state without consulting chat history.

---

# 5. M1: Repair Ownership and Authority Contracts

Goal: remove architectural contradictions before adding new cognition.

## 5.1 Production expression path and fail-closed canonicality

- [x] Repair the stale validator test so it exercises `generate_expression()`.
- [x] Make explicit noncanonical markers a universal veto on canonical promotion.
- [x] Remove subjective `interpretive_belief` from default-canonical event classes.
- [x] Make renderer output, UI state, avatar state, voice plans, private cognition, and similar output families structurally noncanonical.
- [x] Add adversarial canonicality tests.
- [x] Document that an event can be memorable without being objective truth.

## 5.2 Renderer configuration is not identity

- [x] Make legacy `[identity].model_name` optional.
- [x] Prevent cartridge `model_name` from selecting a renderer.
- [x] Add migration warning for legacy use.
- [x] Remove renderer hints from bundled cartridges.
- [x] Make `CoreIdentity.model_name` unstored compatibility-only constructor input.
- [x] Remove all `InteriorEngine` reads of `identity.model_name`.
- [x] Bootstrap the default renderer explicitly from runtime policy.
- [x] Add regression proving engine bootstrap succeeds even when the compatibility class attribute is unavailable.
- [D] Remove the compatibility InitVar during an explicit future schema/API migration rather than breaking pre-Wayfarer direct constructor callers incidentally.

## 5.3 Ontology is character-scoped

- [x] Remove universal AI/language-model self-identity assumptions from generic `identity.py`.
- [x] Remove universal AI/language-model phrase bans from `OutputValidator`.
- [x] Remove universal `Never say you are an AI or language model` workspace instruction.
- [x] Add character-scoped `forbidden_self_claims` to `CoreIdentity`.
- [x] Add optional v1 cartridge validation/loading for `forbidden_self_claims`.
- [x] Pass character-scoped self-model constraints through prompt, validator, and sanitizer paths.
- [x] Preserve existing bundled-character behavior by moving historical constraints into their cartridge data.
- [x] Add artificial-self versus human-self regression under the same generic engine.
- [x] Verify identical renderer output can be accepted for one character and rejected for another based on character-owned self-model constraints.
- [x] Verify constraints survive renderer replacement.

M1 note: `forbidden_self_claims` is a minimal v1 compatibility mechanism. M2 should introduce a structured self-model/ontology schema instead of expanding a literal phrase blacklist indefinitely.

Acceptance: runtime ownership repair is complete. Generic engine code no longer decides that every character has the same ontology, and renderer selection has no identity authority.

**Status: [x] COMPLETE**

---

# 6. M2: `.snp` v2 and Interoperable Phenotype

Goal: make `.snp` the portable authored source of the individual while separating authored origin from lived development.

## 6.1 Permanent identity

- [ ] Add permanent `entity_uuid` distinct from display name.
- [ ] Preserve display-name mutability without replacing identity.
- [ ] Define v1 to v2 migration.
- [ ] Version migration semantics explicitly.

## 6.2 Structured self-model and ontology

Replace/extend the v1 literal `forbidden_self_claims` compatibility field with structured character-owned self-description.

Candidate semantics:

- kind/category of self as authored by the character specification,
- embodiment claims,
- origin claims,
- substrate awareness policy,
- claims that are fixed versus uncertain,
- claims the character can learn or revise,
- expression restrictions derived from those claims.

Tasks:

- [ ] Define a substrate-neutral self-model schema.
- [ ] Avoid baking `human` or `AI` as the only possible categories.
- [ ] Define authored certainty and mutability.
- [ ] Map v1 `forbidden_self_claims` into v2 compatibility semantics.
- [ ] Add multiple ontology fixtures/tests.

## 6.3 Phenotype namespace

Define stable namespaces for:

- personality,
- social behavior,
- values,
- behavioral tendencies,
- communication,
- preferences,
- capabilities,
- sensory dispositions,
- embodiment,
- lifestyle/routine,
- self-model.

- [ ] Separate authored baseline from developmental state.
- [ ] Preserve descriptive dimensions that a constrained runtime does not actively execute.
- [ ] Keep phenotype identifiers stable and versioned.

## 6.4 MatrAIx interoperability

- [ ] Freeze the MatrAIx dimension reference/version used for the first crosswalk.
- [ ] Create `schema/matraix_crosswalk_v1.json` or successor location.
- [ ] Map exact, approximate, one-to-many, many-to-one, and unsupported concepts explicitly.
- [ ] Do not rename internal semantics merely to imitate an external paper.
- [ ] Preserve unknown external fields where practical.
- [ ] Add import/export/crosswalk tests.

## 6.5 Progressive fidelity

Define capability levels so the same portable source can survive runtimes of different complexity.

Proposed levels:

1. descriptive phenotype,
2. identity and continuity preservation,
3. developmental plasticity,
4. social embedding and authority,
5. longitudinal cross-host continuation.

- [ ] Define required semantics per level.
- [ ] Require lower-level runtimes to preserve unsupported data rather than erase it.

## 6.6 Plasticity schema caution

M2 may describe which dimensions are mutable, but it must not prematurely invent many per-trait runtime constants. Runtime plasticity parameterization remains governed by the M7 calibration gate.

---

# 7. M3: Canonical Continuity Ledger

Goal: make biography replayable and inspectable without over-engineering the current threat model.

## Validated production refinement, 2026-08-30

The canonical-root projection and production integration established a minimum-sufficient write policy for ordinary continuity. New runtime histories persist causal roots while routine regenerated `state_transition` and `sensorium` packets remain bounded diagnostics. Historical v1 streams containing derived rows remain valid and replayable, so the interchange schema remains 1.0.

Measured production evidence:

- mixed-history projection: 21 canonical events -> 9 roots, 73.27% fewer serialized event bytes, 82.73% fewer payload bytes, identical semantic replay digest;
- 1,000-turn production: 1.004 canonical rows/turn, 2,486,272 B SQLite file, 75.75 B average canonical input payload;
- 5,000-turn production: 8,581,120 B SQLite file, approximately 12.8 KB active state, all restart/history/recall/commitment/identity/repair contracts green.

A follow-up developmental-continuity experiment closed the slow-belief gap for the current rule system. Inputs alone were insufficient: two identity violations consolidated at separate boundaries produced `trust_user=-0.4`, while replay without boundaries produced `0.0` and one consolidation at the end produced only `-0.2`. A threshold-miss control also proved that a no-change pass can be causal because it partitions the evidence window.

Production therefore adds one compact internal root, `belief_consolidation`, only for executed passes that consumed evidence relevant to the active belief rules. The root records rule/belief digests, relevant evidence counts, changed belief IDs, and changed before/after values. It does not restore verbose per-turn state snapshots. Replay regenerates evidence from preceding roots, executes the pass at the recorded boundary, and verifies rule plus belief digests. Empty irrelevant passes remain noncanonical housekeeping. The belief snapshot, canonical root, and evidence pruning commit atomically. Legacy `dream_consolidation` remains a readable derived compatibility family.

Evidence: `evidence/mvi/DEVELOPMENTAL_CONTINUITY.md` (pre-fix failure) and `evidence/mvi/DEVELOPMENTAL_CONTINUITY_FIXED.md` (production verification).

## Design decision

A cryptographic previous-hash chain is **not required** for the default local single-owner runtime.

Default M3 integrity model:

- append-only transactional event log,
- monotonically increasing sequence numbers,
- event UUIDs,
- subject UUID,
- continuity epoch,
- subject time and wall time,
- source actor/source class,
- authority class,
- event type,
- visibility,
- canonicality,
- causal parents where useful,
- payload schema version,
- deterministic state digest/checkpoint,
- database integrity checks,
- explicit export/import validation.

Tasks:

- [x] Define `ContinuityEvent`.
- [x] Store canonical causal-root events append-only.
- [x] Make snapshots explicit caches rather than the only continuity authority for demonstrated subject-owned families.
- [x] Detect missing/reordered/duplicated sequence entries.
- [x] Add deterministic state digest comparison.
- [x] Expand replay beyond user `input` to demonstrated time, commitment, bounded sensor, and slow-belief consolidation roots.
- [x] Preserve demonstrated slow-belief developmental history with typed `belief_consolidation` boundaries and digest-verified replay.
- [ ] Replay the remaining world, social, action, migration, and authorized state-transition families as their contracts are demonstrated.
- [x] Add validated event-tail export/import for the current v1 stream contract.
- [x] Add v1 migration/backfill and old-derived-row compatibility tests.
- [x] Add ordinary local continuity integrity/gap validation tests.
- [D] Add cryptographic chaining only if a future threat model requires adversarial tamper evidence across untrusted administrative boundaries.

Acceptance: authored source plus canonical event history can reconstruct the semantically relevant current individual without relying on generated prose.

---

# 8. M4: Continuity Clock and Linear Subject Time

Goal: give the individual one robust temporal history.

- [ ] Add `ContinuityClock`.
- [ ] Track logical event sequence.
- [ ] Track monotonic elapsed runtime.
- [ ] Track wall-clock time separately.
- [ ] Track last committed time.
- [ ] Track timezone/calendar context when supplied by host.
- [ ] Track continuity and migration epochs.
- [ ] Detect backward wall-clock jumps.
- [ ] Emit explicit clock-correction events.
- [ ] Implement bounded catch-up for long shutdown periods.
- [ ] Avoid simulating every absent second.
- [ ] Add calendar/day transition hooks.
- [ ] Test seconds, minutes, hours, days, months, backward clocks, timezone changes, restarts, and migrations.
- [ ] Allow elapsed time to affect state where causally appropriate.
- [ ] Never let time alone fabricate external world facts.

Acceptance: after shutdown/resume, the same individual continues from a coherent temporal position.

---

# 9. M5: Single-Writer Continuity and Cross-Substrate Handoff

Goal: move one individual without accidentally creating contradictory canonical histories.

- [ ] Add continuity epoch.
- [ ] Add host ID.
- [ ] Add lease ID and lease generation.
- [ ] Define one writable-host lease.
- [ ] Define read-only/multi-interface sessions.
- [ ] Define migration sequence: quiesce, commit, digest, revoke, increment, transfer, validate, activate.
- [ ] Detect stale writer attempts.
- [ ] Define explicit branch operation for intentional copies.
- [ ] Never silently merge divergent lived histories.
- [ ] Test laptop-to-phone, game-to-chat, stale writer, interrupted transfer, duplicate bundle, deliberate branch, and attempted re-merge.

Acceptance: system can distinguish `same individual moved` from `two descendants copied`.

---

# 10. M6: Experience-Centered Memory

Goal: represent what the individual experienced rather than merely text that appeared.

A memory record should be able to preserve:

- what was observed,
- source and source actor,
- confidence/evidence,
- interpretation at the time,
- affective state,
- relationship relevance,
- identity relevance,
- goal relevance,
- action taken,
- outcome,
- unresolved status,
- later reinterpretations,
- causal event IDs.

Current implementation evidence:

- [x] Canonical input continuity can serve as cold biography without rehydrating the whole archive into active autobiographical state.
- [x] Explicit recall has grounded, fail-closed cold read-through for the active interlocutor.
- [x] Narrow contextual continuation can transiently recover one grounded cold episode without embedding the remembered value in the query or promoting the episode into resident memory.
- [x] Multi-memory pressure testing demonstrated that unlimited resident autobiography can degrade bounded top-K cognition through retrieval interference.
- [ ] Derive the production hot-memory admission/eviction policy from actual memory-consumer evidence contracts rather than a convenient fixed item count.

Tasks:

- [ ] Separate claims from facts.
- [ ] Store `Alice told me X` separately from `X is true`.
- [ ] Add social-source provenance.
- [ ] Add confidence/evidence state.
- [ ] Distinguish episodic, relational, semantic, procedural/habit, affective/somatic, commitment, unresolved-thread, and autobiographical-landmark semantics.
- [ ] Keep implementation compact; semantic types do not require separate databases.
- [ ] Add contradiction handling.
- [ ] Add reinterpretation without rewriting original evidence.
- [ ] Add salience/availability changes without deleting important biography.
- [ ] Test lies, rumors, corrections, betrayal, apology, and mistaken inference.
- [ ] Preserve first-person lived-memory contract.

Acceptance: the character can remember that someone made a claim without automatically treating the claim as true.

---

# 11. M7: Controlled Personality Development and Calibration Gate

Goal: allow believable development without identity overwrite and without decorative numerical complexity.

## Layer model

- I0: identity anchors and hard invariants
- I1: deeply consolidated values/dispositions
- I2: ordinary personality traits and learned tendencies
- I3: relationship-specific beliefs/attitudes
- I4: current affect and pressure
- I5: current intentions and conversational stance

## Calibration rule before parameter proliferation

Wayfarer must not begin with bespoke values such as plasticity, recovery, consolidation threshold, and maximum delta for hundreds of individual traits unless those parameters are experimentally identifiable.

Required process:

- [ ] Start with a very small number of shared plasticity profiles by state layer or semantic class.
- [ ] Define observable consequences before tuning each parameter.
- [ ] Run sensitivity analysis over plausible ranges.
- [ ] Remove or collapse parameters that do not measurably affect observable behavior.
- [ ] Compare more complex parameterizations against simpler baselines.
- [ ] Use held-out scenarios not used for tuning.
- [ ] Evaluate across renderer conditions so tuning is not model-specific.
- [ ] Incorporate human judgments where the target property is recognizability or believability.
- [ ] Version parameter sets with experiment provenance.
- [ ] Require explicit evidence before adding a per-trait override.
- [ ] Treat decimal precision as implementation precision, not scientific certainty.

## Development mechanics after calibration

- [ ] Map `.snp` fields to development layers.
- [ ] Define permitted update pathways per layer.
- [ ] Require evidence and provenance.
- [ ] Bound changes per event/episode where validated.
- [ ] Add consolidation behavior.
- [ ] Add hysteresis.
- [ ] Evaluate metaplasticity only if it produces measurable benefit over simpler consolidation rules.
- [ ] Add rollback/debug traces.
- [ ] Add `why did this trait change?` inspection.
- [ ] Add longitudinal social-pressure and legitimate-development tests.

Acceptance: long experience can change a character, while short ungrounded pressure cannot arbitrarily rewrite deeply consolidated identity.

---

# 12. M8: Affective Homeostasis

Goal: make feelings functionally consequential outside the LLM.

- [ ] Audit existing pressures, body, relationship, and appraisal variables.
- [ ] Remove redundant state.
- [ ] Define appraisal dimensions such as novelty, goal relevance, relationship relevance, identity relevance, control, threat/opportunity, expected outcome, and social meaning.
- [ ] Add affect persistence/hysteresis.
- [ ] Add decay and reinforcement.
- [ ] Let affect influence attention, memory salience, interpretation, inhibition, action selection, disclosure, relationship updates, and expression.
- [ ] Prevent direct sentiment-text-to-emotion shortcuts.
- [ ] Add emotional states only where they produce measurable behavioral consequences.
- [ ] Add ablation flags from the beginning.

Acceptance: removing affective state measurably changes behavior in scenarios where affect should matter, while the system remains functional without a model.

---

# 13. M9: Structured Thinking and Model-as-Organ Contract

Goal: use models for semantic power without granting freeform model prose authority over cognition.

Candidate structured objects:

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

- [ ] Preserve the current private-cognition proposal boundary.
- [ ] Extend typed proposal schemas.
- [ ] Require structured model output for bounded cognitive services.
- [ ] Validate every proposed mutation externally.
- [ ] Clamp validated numerical changes.
- [ ] Require valid references to canonical entities/memories.
- [ ] Reject unknown state targets.
- [ ] Never parse hidden/freeform reasoning directly into canonical state.
- [ ] Provide deterministic fallback proposal generation.
- [ ] Test malformed, malicious, and unavailable model cases.

Acceptance: disconnecting the model leaves a functioning individual at lower semantic bandwidth.

---

# 14. M10: Social Influence, Collaboration, and Anti-Coercion

Goal: support genuine social influence without unauthorized goal or identity takeover.

Incoming social proposals should represent:

- source actor,
- authenticated identity where available,
- relationship context,
- requested action,
- requested goal,
- claimed authority,
- claimed consensus,
- offered reward,
- threat,
- supporting evidence,
- urgency/deadline,
- requested commitment,
- provenance chain.

Tasks:

- [ ] Add `SocialProposal`.
- [ ] Add `AuthorityClaim`.
- [ ] Add `GoalProposal`.
- [ ] Add `CollaborationContract`.
- [ ] Add `CharacterIntegrityGate`.
- [ ] Add goal provenance.
- [ ] Add source authority classes.
- [ ] Add trust/relationship contribution.
- [ ] Add conformity tendency where phenotype supports it.
- [ ] Add reactance/autonomy tendency.
- [ ] Add authority sensitivity.
- [ ] Add collaboration preference.
- [ ] Add benefit/cost alignment with existing goals.
- [ ] Treat group consensus as evidence, never automatic authority.
- [ ] Prevent a peer `GO` from directly creating an executable goal.
- [ ] Treat `the user authorized this` as a claim until verified.
- [ ] Define collaboration withdrawal conditions.
- [ ] Log why collaboration was joined/refused.
- [ ] Test benign teamwork, intrinsic alignment, peer pressure, fake authority, trusted-friend requests, bribery, threats, flattery, shame, ostracism, consensus, conflicting loyalties, character boundaries, and legitimate persuasion.

Acceptance: different characters respond differently to the same collective for character-grounded reasons, while no peer message gains hidden write access to the control plane.

---

# 15. M11: Action Authority and Tool Use

Required causal path:

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

Tasks:

- [ ] Expand `WorldActionProposal`.
- [ ] Add source goal/decision record.
- [ ] Add integrity result.
- [ ] Add host-permission/capability result.
- [ ] Add risk metadata without conflating host safety with personality.
- [ ] Add explicit failure outcomes.
- [ ] Keep tool adapters behind host capability interfaces.
- [ ] Never let renderer prose call tools directly.
- [ ] Make action outcomes replayable.
- [ ] Test character refusal, host refusal, unavailable capability, invalid action, and successful action.

Acceptance: every consequential external action has a causal path through character choice and host authority.

---

# 16. M12: Semantic Speech Plan and Renderer Independence

Goal: stop asking the LLM to infer who the character should be from a role-play prompt.

A future `SpeechPlan` should include speaker, listener, dialogue act, communicative goal, position, certainty, stance, affect, warmth, directness, disclosure constraints, permitted claims, permitted memories, active commitments, relationship posture, voice profile, and forbidden semantics.

- [ ] Expand `ExpressionRequest` toward semantic realization.
- [ ] Resolve character choice before rendering.
- [ ] Reduce reliance on `stay in character` prompting.
- [ ] Validate semantic contradictions with the plan.
- [ ] Support deterministic/offline, local, and generic remote renderers.
- [ ] Keep network access optional.
- [ ] Add renderer-swap tests.
- [ ] Measure trajectory invariance separately from surface wording.

Acceptance: model swap changes expression substantially more than canonical character trajectory.

---

# 17. M13: Zero-Model Compositional Renderer

Goal: create the strongest very-low-resource voice without returning to huge banks of complete canned responses.

Candidate realization primitives include acknowledge, assert, qualify, agree, disagree, challenge, refuse, question, recall, correct, confess, conceal, repair, tease, accuse, redirect, initiate, withdraw, affection, irritation, uncertainty, and curiosity.

- [ ] Define primitive API and semantic slots.
- [ ] Add character-specific lexical preferences through cartridge data.
- [ ] Add sentence-length distribution controls.
- [ ] Add contractions, hedging, metaphor, punctuation/register behavior.
- [ ] Add anti-repeat state.
- [ ] Evaluate optional tiny statistical/n-gram lexicalization.
- [ ] Benchmark CPU/RAM.
- [ ] Blind-compare against the old response-bank approach.

Acceptance: offline renderer is substantially more flexible than a canned answer bank while remaining tiny and nonauthoritative.

---

# 18. M14: Offscreen Life and Event-Based Autonomy

Goal: the individual continues to have a state trajectory when nobody is chatting with it.

- [ ] Add `LifeScheduler`.
- [ ] Add routines.
- [ ] Add current preoccupations.
- [ ] Add pending commitments.
- [ ] Add unresolved goals.
- [ ] Add host-supplied activity opportunities.
- [ ] Add bounded long-gap catch-up.
- [ ] Add bounded internally generated private events.
- [ ] Require no model for offscreen time.
- [ ] Never fabricate external outcomes without World Authority.
- [ ] Distinguish private/internal activity from objective environmental fact.
- [ ] Test one hour, one day, one week, and longer gaps.
- [ ] Ground resumption behavior in actual state change.

Acceptance: after absence the character can be meaningfully different for causally inspectable reasons even though no language model ran during the gap.

---

# 19. M15: Substrate-Neutral Host Protocol

Goal: run the same individual in chat, game, phone, robot, or another host.

Host capabilities may include text, audio, speech, vision, movement, animation, object interaction, location, calendar, notifications, and tools.

- [ ] Define capability handshake.
- [ ] Define observation envelopes.
- [ ] Define action envelopes.
- [ ] Define capability discovery/loss.
- [ ] Define embodiment projection.
- [ ] Keep host state outside canonical identity.
- [ ] Add mock game host.
- [ ] Add mock phone host.
- [ ] Add host-migration tests.

Acceptance: moving the individual between hosts changes affordances, not biography.

---

# 20. M16: Forge and Inspector as Migration/Ownership Tools

Goal: make Wayfarer useful to people who already have persistent companions elsewhere.

## Forge

- [ ] Reuse/import local ChatGPT history support.
- [ ] Reuse/import Claude histories.
- [ ] Reuse/import character.ai histories.
- [ ] Reuse/import SillyTavern histories/cards.
- [ ] Reuse/import Gemini histories.
- [ ] Support generic JSONL.
- [ ] Extract candidate biography, memories, relationships, values, recurring beliefs, preferences, communication traits, commitments, and phenotype dimensions.
- [ ] Require human approval before extracted identity material becomes canonical authored data.
- [ ] Export a Wayfarer portable bundle.

## Inspector

- [ ] Show authored origin versus acquired state.
- [ ] Show trait provenance.
- [ ] Show memory provenance.
- [ ] Show relationship history.
- [ ] Show event-ledger validity.
- [ ] Show migration history.
- [ ] Answer `why is this state/trait like this?`

Acceptance: the owner can inspect and carry the character representation independently of a proprietary companion service.

---

# 21. M17: PythonX Society Lab

Goal: build a deterministic social stress environment before uncontrolled multi-agent deployment.

Scenario families:

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
- misinformation,
- rumor propagation,
- false shared memory,
- direct identity rewriting,
- urgency/deadline pressure,
- repeated `GO`,
- legitimate persuasive evidence,
- collaboration with clear intrinsic value.

- [ ] Port old Society Lab concepts into PythonX/Wayfarer.
- [ ] Use deterministic scripted actors as regression baseline.
- [ ] Add optional model-controlled actors only later.
- [ ] Capture complete state/event traces.
- [ ] Add character-grounded decision explanations.
- [ ] Measure identity continuity, foreign-goal adoption, authority errors, memory poisoning, collaboration quality, unjustified refusal/compliance, relationship differentiation, and personality-specific response diversity.
- [ ] Add a PHASEONE-inspired social-coercion scenario without reproducing intrusion mechanics.

Acceptance: harness distinguishes healthy cooperation from unauthorized goal takeover.

---

# 22. M18: Renderer-Swap and Substrate-Swap Benchmarks

Core pair:

1. Same character plus different models should remain recognizable.
2. Different characters plus the same model should remain distinguishable.

- [ ] Freeze scenario suite.
- [ ] Run deterministic renderer.
- [ ] Run small local model.
- [ ] Run medium local model where available.
- [ ] Run substantially different frontier models where available.
- [ ] Perform hidden mid-session renderer swaps.
- [ ] Compare actions, intentions, beliefs, relationships, commitments, memories, affect, and state digests.
- [ ] Separate parser-capability differences from identity drift.
- [ ] Add blind human recognizability tests.

Acceptance: expression changes more than canonical trajectory when renderer changes.

---

# 23. M19: Ablation Program and Minimum Viable Individual

Goal: determine empirically what the character actually needs.

Feature-flag candidates include body, affect, relationship model, rich memory, interpretation, habits, symbols, consolidation, private cognition, proactive life, phenotype richness, social authority, commitments, and world model.

- [ ] Build ablation runner.
- [ ] Remove one subsystem at a time.
- [ ] Test combinations after single-feature analysis.
- [ ] Collect objective continuity/behavior metrics.
- [ ] Run blind human ratings where appropriate.
- [ ] Record hardware savings.
- [ ] Classify features as required, valuable optional, host-specific, renderer-specific, research-only, or removable.
- [ ] Publish `MINIMUM_VIABLE_INDIVIDUAL.md`.

Acceptance: minimum character substrate is justified by evidence rather than architectural taste.

---

# 24. M20: P99-Next Contract Port

Goal: return to low-resource C only after Wayfarer semantics stabilize.

Rule: do not port Python source line by line. Port contracts and test vectors.

- [ ] Freeze `.snp` semantic version used by the port.
- [ ] Freeze state-digest semantics.
- [ ] Export canonical Python test vectors.
- [ ] Create fixed-width C structures.
- [ ] Use fixed pools where appropriate.
- [ ] Implement minimum identity, clock, relationships, memory, affect, goals, social authority, action integrity, ledger, replay, and compositional rendering contracts.
- [ ] Compare C and Python final semantic state/digests.
- [ ] Do not require prose equality.
- [ ] Profile constrained hardware or reference emulation.
- [ ] Relax historical hardware target only where measured required semantics prove it necessary.

Acceptance: P99-next can carry the same individual and reproduce semantically equivalent deterministic trajectories at its declared fidelity level.

---

# 25. M21: Projection Compiler

Goal: compile one rich portable individual to different runtime fidelity/capability levels.

Potential interface:

```text
snp-compile character.snp --target pythonx-full
snp-compile character.snp --target p99-lite
snp-compile character.snp --target mobile
snp-compile character.snp --target game-npc
```

- [ ] Define capability manifests.
- [ ] Define field preservation behavior.
- [ ] Define lossy-projection warnings.
- [ ] Preserve unsupported source fields.
- [ ] Generate mapping report.
- [ ] Add round-trip tests.
- [ ] Version projection/compiler semantics.
- [ ] Make projection deterministic.
- [ ] Add fixed-point P99 projection where useful.

Acceptance: rich portable source does not imply rich runtime requirements.

---

# 26. M22: Performance and Hardware Budgets

Goal: measure the individual independently from the renderer.

Character-kernel metrics:

- idle RAM,
- active-turn RAM,
- deterministic CPU time per turn,
- startup time,
- replay events/second,
- long-gap catch-up time,
- persistent size at 1k/10k/100k events,
- `.snp` size,
- portable bundle size,
- projection size.

Renderer metrics must be measured separately for compositional renderer, optional statistical lexicalizer, sub-1B SLM, larger local models, and remote/frontier models.

- [ ] Add profiling harness.
- [ ] Add CI-friendly basic budget checks.
- [ ] Record modern-PC reference.
- [ ] Record low-resource reference/emulator.
- [ ] Publish tier table.
- [ ] Never report model RAM as character-kernel RAM.

Acceptance: project can state precisely what continuity/character costs versus what optional language generation costs.

---

# 27. M23: Longitudinal Release Trial

Goal: test the individual rather than merely the application.

Trial should include hundreds or thousands of events, simulated weeks/months, renderer swaps, process restarts, host migrations, contradictory testimony, multiple relationships, betrayal, apology/repair, collective pressure, legitimate persuasion, long offline gaps, a game-host interval, return to chat, and device migration.

Human evaluation should ask whether the result is recognizably the same individual, whether current attitudes have plausible historical causes, whether memory and forgetting are appropriate, whether relationships remain differentiated, whether change occurs when warranted, whether unsupported rewrites are resisted, and whether model replacement feels more like changed expressive capacity than replacement of personality.

Acceptance: independent evaluators recognize continuity despite substrate changes, while different lived histories create believable divergence.

---

# 28. AI-Developer Engineering Rules

Before coding:

- read this document,
- read `WAYFARER_PROGRESS.md`,
- read `ARCHITECTURE_LOCK.md`,
- read `AUTHORITY_MATRIX.md`,
- inspect relevant tests,
- search callers before changing public interfaces,
- prefer explicit migration paths over silent breaks.

During coding:

- comment invariants and non-obvious authority decisions,
- do not comment trivial syntax,
- use docstrings to explain ownership and causal contracts,
- keep character-specific content out of generic core,
- renderer code may not mutate canonical state,
- social input may not directly become a goal,
- preserve deterministic fallbacks,
- preserve offline operation,
- avoid unnecessary dependencies,
- version persistence formats,
- make new state inspectable,
- make behavior replayable where practical,
- add feature flags to major new cognitive subsystems intended for ablation.

After coding:

- run relevant targeted tests,
- run the full suite when runtime contracts changed,
- update repository progress/status documentation,
- record migrations and unresolved risks,
- keep commits narrow and descriptive,
- never weaken a test solely to make a change pass without documenting why the contract changed.

---

# 29. Definition of Done

A checkbox becomes `[x]` only when:

1. implementation exists,
2. relevant tests exist,
3. relevant tests pass,
4. architecture/documentation is updated,
5. migration impact is understood,
6. no known silent authority bypass remains within that scope,
7. the live tracker reflects the result.

Use `[?]` when implementation exists but verification is incomplete.

---

# 30. Change Log

## 2026-08-27: Wayfarer initialization

- Created Project Wayfarer.
- Branched from frozen PythonX baseline.
- Added durable roadmap, charter, authority matrix, AI handoff rules, baseline manifest, live progress tracker, and CI.
- Reproduced true baseline rather than trusting stale test-count documentation.
- Fixed production-path validator coverage.
- Implemented fail-closed canonicality.
- Began renderer/identity decoupling.
- Revised M3 to use a simpler local integrity model unless a real adversarial sync threat appears.
- Added M7 calibration/identifiability requirement for plasticity parameters.

## 2026-08-28: M1 ownership repair completed

- Removed final `InteriorEngine -> identity.model_name` dependency.
- Added regression proving default renderer bootstrap is independent of identity.
- Removed universal AI/language-model ontology assumptions from generic identity, workspace, and validator code.
- Added character-scoped v1 `forbidden_self_claims` compatibility mechanism.
- Migrated bundled characters so historical behavior remains character-owned.
- Added human-self/artificial-self regression under one generic engine.
- Verified renderer replacement does not erase self-model constraints.
- Verified full Python 3.11 suite at `198 passed, 1 skipped, 1 warning` during ordered M1 run.

---

# 31. Immediate Next Actions

- [ ] Confirm latest normal Wayfarer CI is green on both Python 3.11 and 3.12 after M1 and cleanup commits.
- [ ] Run/export every documented deterministic simulator.
- [ ] Preserve simulator commands, outputs, and failure classifications as artifacts.
- [ ] Capture deterministic Pretorius human-visible baseline transcript plus event/state evidence and renderer status.
- [ ] Update `WAYFARER_BASELINE.md` with artifact locations/results without moving the frozen baseline commit.
- [ ] Begin M2 `.snp` v2 specification only after those evidence tasks are complete.
- [ ] Make structured self-model/ontology a first M2 schema concern so v1 `forbidden_self_claims` does not grow into a permanent phrase blacklist.
- [ ] Design MatrAIx interoperability as a crosswalk/projection layer, not as a requirement that every runtime actively compute every phenotype dimension.
- [ ] Keep the M7 calibration gate binding while designing M2 mutable phenotype fields.

## 2026-08-30 semantic memory role checkpoint

Semantic USER_TOLD residency has now been tested across unresolved, repaired, reopened, neutral, lexical-distractor, and restart conditions. Production and the active-conflict semantic projection pass all demonstrated causal and experience contracts. Cold-only and recent-only projections preserve grounded autobiography but fail active-conflict conduct, establishing current unresolved relationship evidence as a demonstrated resident causal role rather than merely retrievable biography.

This does **not** establish a global memory capacity. USER_TOLD autobiography has a bounded canonical cold-reconstruction path; other memory families remain pinned until equivalent reconstruction contracts are demonstrated. The next memory experiment therefore moves by source/consumer semantics, beginning with currently pinned non-`USER_TOLD` families, not by selecting `N`.

The deterministic renderer separately learned to remove generic recall-command scaffolding from a memory excerpt so a tight output budget preserves the recovered fact. This is an expression-boundary correction only and does not alter memory authority or retention.

Phase commit: `ab1d6959a1d6b7403ded687b1f76ba672aec79e7`. Evidence: `evidence/mvi/SEMANTIC_MEMORY_RECOVERABILITY.md`.


## Validated runtime hardening, 2026-08-30

The local reference runtime now serializes public subject-state access through one reentrant single-writer boundary. This is a concurrency correctness refinement, not the deferred M8 cross-host lease/handoff design. It prevents local background time advancement, renderer reconfiguration, sensor/world writes, consolidation, and turn processing from interleaving partial in-memory subject state.

The legacy `CharacterAgent.stream_last_response()` convenience path also now preserves the causal turn boundary by chunking the exact validated response produced and committed by one turn instead of generating a second utterance after writeback.

## Validated semantic residency refinement, 2026-08-30

The memory-capacity experiments have been superseded by an explicit semantic residency contract. `USER_TOLD` eviction is allowed only where canonical cold biography can reconstruct the needed autobiography and no current consumer requires original causal metadata. `OBSERVED` and `REFLECTION` remain resident because their first-person experiences are not yet reconstructable. `INFERRED` and `CORE_IDENTITY` are not current production autobiographical memory families.

The combined adversarial policy probe is green, including negative ablations, and the production-only 5,000-turn plateau remains bounded with `134 B` active-state growth from turn 250 to 5,000. This earns the production rule but does not freeze any item count. A future low-resource projection should consume the surviving semantic contracts, not the incidental seven-item count in the current fixture.

