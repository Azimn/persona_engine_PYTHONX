# Architecture Lock

This document records the guardrails future work must preserve. It is intentionally stricter than an implementation tour: it defines what must not drift while the Python lab evolves.

## Non-Negotiable Doctrine

The engine is character-agnostic.

All character-specific content belongs in `.snp` cartridges.

Session state stores lived history.

World Authority owns objective facts.

The character owns subjective interpretation.

The LLM is a renderer only.

Renderer output is not canonical truth.

The UI displays organism state. It does not author organism state.

Sensors report bounded observations only.

Voice and avatar layers perform state only.

Memory creation must pass through canonicality/firewall rules.

Interpretive beliefs are subjective, noncanonical, and support-traced.

Dream/reflection may consolidate patterns only through evidence-backed rules.

## Ownership Boundaries

### Cartridges Own Character Content

Character names, voice traits, lore, body/world profile, belief schema, interpretation bias, and identity content belong in `.snp` cartridges under `persona_engine/cartridges/`.

Engine/core modules must not hardcode cartridge-specific character names, phrases, lore, voice traits, or identity content.

### World Authority Owns Objective Facts

Objective facts must enter through World Authority or approved engine/session channels. Renderers, UI controls, sensors, voice layers, avatar layers, and simulators must not bypass this boundary.

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

### Memory Owns Lived History

Session history and memories must flow through memory, persistence, event-log, and canonicality/firewall rules. Generated renderer text is speech evidence, not objective fact.

### Renderer Owns Surface Language Only

The LLM or mock renderer may produce expressive prose. It may not define what is true. It may not directly write memory, world facts, private state, cartridge content, or belief-ledger state.

Renderer output cannot create canonical belief. It is logged as noncanonical speech evidence behind the memory firewall.

### UI Owns Display and User Input Only

The UI may display public organism state, read-only debug details, interpretive beliefs, voice plans, avatar projection, and chat output. It may send user input and bounded mock observations through approved API endpoints. It must not author private organism state.

### Sensors Own Bounded Observations Only

Audio and vision layers report limited observations such as sound level, sudden onset, speech activity, user presence, light level, and scene change. They must not infer hidden motives, identity facts, or unsupported world events.

### Voice and Avatar Own Performance Only

Voice and avatar systems may perform public state. They do not decide state and must not mutate private organism state.

### Dream and Reflection Own Evidence-Backed Consolidation

Dream/reflection may consolidate patterns only through evidence-backed rules. They must not promote unsupported renderer output or ungrounded interpretation into canonical truth.

Null consolidation is valid. `DreamEngine` may update `last_consolidated` while changing no belief values; that is a checkpoint, not identity drift.

### Tide Is Deterministic Idle Drift

The Tide means deterministic pressure, body, world, and sensorium drift during idle time and wall-clock catch-up. It currently includes:

- energy drain under pressure
- restlessness increase during idle
- pressure decay
- body fatigue, stillness, sensory load, and movement need
- world absence, noise, light mismatch, and routine effects
- sensorium coupling into pressure, memory, and intention state

The Tide does not currently include stochastic mood weather, random affect variance, calendar-based mood variance, or model-generated mood shifts. Do not add randomness without an explicit architecture change request.

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

Risky changes requiring extra scrutiny include:

- changing `persona_engine/core/engine.py`
- changing memory promotion or canonicality rules
- changing interpretation grounding
- changing World Authority behavior
- changing cartridge schema semantics
- introducing new dependencies or external services
- moving character-specific content into engine/core modules

## Required Checks for Behavior Changes

For behavior-changing work, run at minimum:

```bash
python -m pytest persona_engine/tests -q
```

Also run the relevant simulator scripts when the change touches turn flow, interpretation, organism state, cartridges, or UI/server behavior.

For documentation-only work, a lighter check is acceptable, but the final response must say what was or was not run.

## Anti-Patterns

Do not make the LLM the source of truth.

Do not let rendered prose become canonical memory.

Do not let renderer output create canonical belief.

Do not let UI controls write private state directly.

Do not let sensors infer story facts beyond bounded observations.

Do not embed a character's voice or lore in engine/core modules.

Do not make tests require Ollama, network access, microphone, camera, TTS, GPU, avatar engine, or mobile-native tooling.

Do not blur objective world facts and subjective character beliefs.

Do not let interpretive beliefs directly mutate the belief ledger.

Do not add stochastic Tide drift under the name of idle behavior.
