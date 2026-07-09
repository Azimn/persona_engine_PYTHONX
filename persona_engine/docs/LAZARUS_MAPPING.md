# Lazarus Mapping

This document maps the conceptual "Lazarus Substrate" language onto the current Persona Engine architecture. It is a metaphor and orientation aid, not a license to redesign the engine.

## Important Correction

In the current project, the base generative model is not the root authority.

The LLM is a renderer only. It gives language texture after the engine has assembled identity, state, memory, interpretation, and expression constraints. It does not own truth, identity, memory, or world facts.

The project maps more accurately as:

```text
Cartridge / Ledger / World Authority / Session
        -> Tide + Undertow + Memory
        -> Active Chamber
        -> Mask Suppression
        -> Loom / Face
        -> Event Log + Long Sleep
```

## Layer Mapping

| Lazarus term | Current project equivalent | Notes |
| --- | --- | --- |
| The Loom | `LocalLLMRenderer`, mock renderer, optional Ollama | Language texture only. Renderer output is not canonical truth. |
| The Ledger | `.snp` cartridges, `IdentityLedger`, `BeliefLedger` | Always-resident identity and belief schema. Character-specific content belongs in cartridges. |
| The Tide | `PressureSystem`, relationship appraisal, body/world affect, `OrganismTick` | Mood drift, pressure, energy, tension, comfort, and downstream consequence. |
| The Undertow | `InterpretationEngine`, interpretation bias, habits, relationship pressure | Latent subjective readings. Must be visible-source grounded and noncanonical. |
| The Memory | `MemoryStore`, event log, `Persistence`, session state | Lived history and retrievable event traces. Memory creation passes through canonicality/firewall rules. |
| Active Chamber | `WorkspaceFrame` | Limited working frame containing identity, relationship, affect, memory, intention, world/body/sensorium state, interpretive beliefs, and expression constraints. |
| Mask Suppression | identity guard, `OutputValidator`, forbidden claims, refusal modes, expression envelope | Prevents generic assistant drift, meta-breaks, unsupported memory claims, and identity overwrite. |
| The Face | renderer output, voice plan, avatar projection, UI display | Performs state as speech, voice, avatar, and visible UI. It does not author canonical state. |
| The Long Sleep | `DreamEngine`, reflection, memory compression, belief rules | Evidence-backed consolidation and forgetting. Must not promote unsupported renderer text or ungrounded interpretation. |

## Original Diagram, Reinterpreted

The original diagram starts with:

```text
THE LOOM -> THE LEDGER
```

For this repository, invert that authority relationship:

```text
THE LEDGER -> ACTIVE CHAMBER -> THE LOOM
```

The character's cartridge, session history, world facts, pressure state, and subjective interpretation constrain what the renderer may express. The renderer does not create the character's truth.

## Doctrine-Preserving Reading

### The Ledger

The Ledger is split across cartridge identity and engine ledgers:

- immutable/core identity from cartridge data
- belief schema and belief ledger
- moral boundaries and prohibited mutations
- voice constraints and profile data

The Ledger must remain character-agnostic in engine code. Specific character content lives in `.snp`.

### The Tide

The Tide is the engine's affective and organism drift:

- pressure changes
- relationship appraisal
- body state
- world state
- idle cycle effects
- open loops and habits

It creates continuity and consequence across turns.

### The Undertow

The Undertow is not hidden omniscience. It is grounded subjective interpretation:

- visible sources only
- source IDs
- support keys
- confidence
- pressure key
- distortion label
- `canonical: false`

This lets the character own belief without confusing belief for objective truth.

### Active Chamber

The Active Chamber corresponds closely to `WorkspaceFrame`. It is the bounded frame passed toward rendering. It contains enough current context for expression, but it must preserve access rules and forbidden claims.

### Mask Suppression

Mask Suppression is not a personality patch. It is the set of guards that prevent:

- "as an AI" drift
- generic helpful-assistant behavior
- unsupported memory claims
- forced identity rewrites
- private-state claims about the user
- renderer output becoming canonical

### The Face

The Face is the performance surface:

- speech text
- voice plan
- avatar projection
- UI display

The Face may show state. It may not define state.

### The Long Sleep

The Long Sleep is consolidation:

- dream/reflection
- compression
- evidence-backed belief-rule changes
- pattern formation from lived history

It must remain downstream of evidence and canonicality checks.

## Porting Use

This mapping is useful when porting Python-lab improvements back toward the C99 line:

- Preserve the same ownership boundaries.
- Keep renderer/model code late in the pipeline.
- Keep character content in cartridges or cartridge-equivalent assets.
- Keep UI as display/input, not organism-state author.
- Keep sensors bounded.
- Keep consolidation evidence-backed.

If a proposed change makes "The Loom" author truth, identity, memory, or objective facts, it violates the architecture lock.
