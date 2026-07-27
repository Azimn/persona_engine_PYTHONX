# Architecture Lock

This document records the guardrails future work must preserve. It is intentionally stricter than an implementation tour: it defines what must not drift while the Python lab evolves.

## Foundational Definition

A digital organism is a persistent first-person subject whose interpretations and actions become the conditions of its future existence. It continuously experiences, interprets, acts, and changes through its own history. Memory records experience, but continuity is created by living under the consequences of previous experience.

The project is not fundamentally about a loop. It is about a subject. The loop is machinery used to preserve one continuing individual across changing moments.

The architecture is therefore subject-centered and consequence-bound.

A normal memory system asks what happened before. This architecture must also preserve what the subject made of it, what the subject did because of it, what followed, and how that outcome changed the subject who encounters the next moment.

## Governing Design Filter

Every computation in the system exists only because it changes what the subject experiences, believes, intends, expresses, or becomes.

A component does not belong in the organism core merely because humans possess something similar, because another agent framework includes it, or because it increases generic capability. It belongs only when its result changes the subject's lived position while preserving ownership and causal traceability.

## Non-Negotiable Doctrine

The persistent subject is the object of design. The loop, memory system, renderer, tools, sensors, and interface are supporting machinery.

Each new moment must be encountered by the same individual who lived through the previous moment, and the previous moment must make some difference to who encounters the next one.

The engine is character-agnostic.

All character-specific content belongs in `.snp` cartridges.

Session state stores the subject's lived history and inherited consequences.

World Authority owns objective facts.

The subject owns subjective interpretation.

The LLM is a renderer only.

Renderer output is not canonical truth.

The UI displays organism state. It does not author organism state.

Sensors report bounded observations only.

Voice and avatar layers perform state only.

Memory creation must pass through canonicality/firewall rules.

Interpretive beliefs are subjective, noncanonical, and support-traced.

Dream/reflection may consolidate patterns only through evidence-backed rules.

Expression substrate is not identity. Changing models may alter verbal texture, fluency, or cognitive range, but must not reset biography, relationships, commitments, unresolved consequences, or lived position.

## Subject Continuity Contract

A completed turn must preserve a causal chain linking:

1. what happened to the subject
2. what the subject perceived or noticed
3. what prior experience became relevant
4. what the subject interpreted or believed
5. what the subject intended
6. what the subject expressed, concealed, withheld, or did
7. what objectively followed
8. how the result changed the next subject state

Not every stage must produce a large mutation. A valid result may be restraint, uncertainty, failed action, no disclosure, no belief change, or no consolidation. The requirement is not constant change. The requirement is that consequences are represented honestly and are available to condition future experience.

Memory retrieval alone does not satisfy continuity. Stored history must be capable of altering current appraisal, interpretation, intention, expression, inhibition, expectation, relationship position, or later consolidation.

No subsystem may create a second independent subject, decision authority, or identity trajectory beside the canonical subject state.

## Ownership Boundaries

### Cartridges Own Character Content

Character names, voice traits, lore, body/world profile, belief schema, interpretation bias, identity invariants, and initial dispositions belong in `.snp` cartridges under `persona_engine/cartridges/`.

Engine/core modules must not hardcode cartridge-specific character names, phrases, lore, voice traits, or identity content.

Cartridges define who begins. They do not overwrite who the subject has become through lived history.

### Subject State Owns Lived Position

The canonical subject state owns the accumulated position produced by prior experience. This includes mutable pressures, relationships, commitments, habits, interpretations, expectations, unresolved conflicts, autobiographical consequences, and other governed state used by the next turn.

Identity invariants constrain change, but they must not erase consequence. Mutable state may evolve without turning the subject into a different individual.

A model swap, renderer failure, UI restart, or process restart must not silently replace the subject with a fresh persona when valid persisted state exists.

### World Authority Owns Objective Facts

Objective facts must enter through World Authority or approved engine/session channels. Renderers, UI controls, sensors, voice layers, avatar layers, and simulators must not bypass this boundary.

Objective outcomes provide the external consequence against which the subject's interpretations and actions are tested.

### Interpretation Owns Subjective Readings

`InterpretationEngine` is the current Undertow mechanism. It turns visible evidence, pressure state, and generic bias into subjective belief objects for the active turn.

Interpretive beliefs are short-term subjective readings. They may be biased by visible evidence and pressure, but they must be:

- noncanonical
- deterministic
- source-traced
- support-keyed
- bounded to visible evidence
- safe for replay/debug inspection

Interpretive beliefs must not directly mutate the long-term belief ledger.

Interpretive belief bias may color visible evidence. It may not create objective fact, canonical memory, or slow belief-ledger drift.

Only `DreamEngine` or explicitly governed consolidation rules may alter slow `BeliefLedger` values.

Interpretation matters only insofar as it changes the subject's current lived position, such as expectation, pressure, intention, disclosure, inhibition, or future consolidation.

### Memory Owns Lived History

Session history and memories must flow through memory, persistence, event-log, and canonicality/firewall rules. Generated renderer text is speech evidence, not objective fact.

Memory is evidence available to the continuing subject. Memory storage is not itself continuity. The architecture must preserve the effects of experience, including changes that are not reducible to recalling a text record.

### Intention and Action Own Consequential Choice

Action selection, withholding, refusal, concealment, disclosure, waiting, repair, and failed attempts must be attributable to the current subject state and bounded evidence.

The system must preserve enough traceability to explain how a chosen or withheld action arose and how its objective completion altered the next subject state.

### Renderer Owns Surface Language Only

The LLM or mock renderer may produce expressive prose. It may not define what is true. It may not directly write memory, world facts, private state, cartridge content, or belief-ledger state.

Renderer output cannot create canonical belief. It is logged as noncanonical speech evidence behind the memory firewall.

The renderer gives the subject a voice. It is not the subject and must not own biography or continuity.

### UI Owns Display and User Input Only

The UI may display public organism state, read-only debug details, interpretive beliefs, voice plans, avatar projection, and chat output. It may send user input and bounded mock observations through approved API endpoints. It must not author private organism state.

### Sensors Own Bounded Observations Only

Audio and vision layers report limited observations such as sound level, sudden onset, speech activity, user presence, light level, and scene change. They must not infer hidden motives, identity facts, or unsupported world events.

Observations become meaningful only after the subject interprets them through its current state and history.

### Voice and Avatar Own Performance Only

Voice and avatar systems may perform public state. They do not decide state and must not mutate private organism state.

### Dream and Reflection Own Evidence-Backed Consolidation

Dream/reflection may consolidate patterns only through evidence-backed rules. They must not promote unsupported renderer output or ungrounded interpretation into canonical truth.

Null consolidation is valid. `DreamEngine` may update `last_consolidated` while changing no belief values; that is a checkpoint, not identity drift.

Reflection exists to change future interpretation or conduct. Reflection that produces no governed effect is optional commentary, not organism state.

### Tide Is Deterministic Idle Drift

The Tide means deterministic pressure, body, world, and sensorium drift during idle time and wall-clock catch-up. It currently includes:

- energy drain under pressure
- restlessness increase during idle
- pressure decay
- body fatigue, stillness, sensory load, and movement need
- world absence, noise, light mismatch, and routine effects
- sensorium coupling into pressure, memory, and intention state

The Tide does not currently include stochastic mood weather, random affect variance, calendar-based mood variance, or model-generated mood shifts. Do not add randomness without an explicit architecture change request.

Idle change must still belong to the same subject and must be persisted as part of its causal history.

### Mask Suppression Is Traceable

Mask Suppression is distributed across existing gates:

- identity guard
- expression envelope
- resistance selector
- workspace forbidden claims
- output validator
- renderer sanitizer
- memory firewall

Suppression traces are observability records only. They must not decide character behavior or mutate private state.

## Allowed Change Types

Safe changes usually include:

- documentation updates
- tests for existing contracts
- packaging fixes
- UI display improvements that preserve state boundaries
- simulator coverage for existing behavior
- cartridge tooling that keeps character content in cartridges
- renderer abstraction that preserves renderer-as-surface doctrine
- continuity tests proving that prior consequences alter later subject state
- replay checks linking interpretation, conduct, outcome, and state update

Risky changes requiring extra scrutiny include:

- changing `persona_engine/core/engine.py`
- changing subject-state ownership or persistence
- changing memory promotion or canonicality rules
- changing interpretation grounding
- changing World Authority behavior
- changing cartridge schema semantics
- introducing new dependencies or external services
- moving character-specific content into engine/core modules
- allowing a model, renderer, tool, or UI layer to create an independent identity trajectory

## Required Checks for Behavior Changes

For behavior-changing work, run at minimum:

```bash
python -m pytest persona_engine/tests -q
```

Also run the relevant simulator scripts when the change touches turn flow, interpretation, organism state, cartridges, persistence, or UI/server behavior.

Behavior changes affecting continuity should include a test showing that an earlier interpretation or action produces an objective or subjective consequence that changes a later turn.

For documentation-only work, a lighter check is acceptable, but the final response must say what was or was not run.

## Anti-Patterns

Do not make the loop the object of design. The loop serves the subject.

Do not mistake stored memories for continuity.

Do not create state that cannot affect what the subject later experiences, believes, intends, expresses, or becomes.

Do not make the LLM the source of truth.

Do not let rendered prose become canonical memory.

Do not let renderer output create canonical belief.

Do not let model replacement reset lived history or identity trajectory.

Do not let UI controls write private state directly.

Do not let sensors infer story facts beyond bounded observations.

Do not embed a character's voice or lore in engine/core modules.

Do not make tests require Ollama, network access, microphone, camera, TTS, GPU, avatar engine, or mobile-native tooling.

Do not blur objective world facts and subjective character beliefs.

Do not let interpretive beliefs directly mutate the belief ledger.

Do not add stochastic Tide drift under the name of idle behavior.

Do not introduce a second decision engine that competes with the canonical subject state.