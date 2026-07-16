# Persona Engine v8, C99 Porting Notes

These notes identify the deterministic seams that should be ported first when translating the Python reference engine into a C99 console runtime.

## Hard separation

The C engine should preserve the same three-way split as the Python reference.

- Engine or console: character-agnostic mechanics only.
- Cartridge: authored character-specific constants and thresholds.
- Session state: lived mutable state for one character/user instance.

No character-specific literal strings should appear in engine source other than field names, enum labels, and diagnostic messages. Character names, voice constraints, body/world sensitivities, interpretation biases, belief IDs, and prohibited mutations belong in the `.snp` cartridge.

## Port first

Port these deterministic pieces before any renderer integration.

1. Cartridge schema parser and validator. TOML can be replaced with a simpler packed format later, but the field set and numeric ranges should remain equivalent.
2. Belief ledger rules: min, max, fixed flag, decay, threshold counts, and delta application.
3. Session snapshot checksum formula. Keep the exact JSON canonicalization contract or bump schema version.
4. Event log row format: timestep, event_type, created_at, payload. In constrained builds, payload can be compact tagged structs instead of JSON.
5. World/body tick formulas and pressure decay.
6. Memory activation scoring. Use fixed-point or scaled floats if needed, but keep recency, recall count, emotional salience, relationship relevance, identity relevance, and unresolved boost as separate terms.
7. Interpretation layer. It must remain deterministic and non-LLM. It transforms visible facts into grounded subjective beliefs.
8. Output validation and memory firewall. Renderer text is speech evidence, not world truth.

## Suggested C layout

```text
src/
  cartridge.c/.h
  session.c/.h
  event_log.c/.h
  belief_ledger.c/.h
  pressure.c/.h
  relationship.c/.h
  memory.c/.h
  world.c/.h
  body.c/.h
  sensorium.c/.h
  interpretation.c/.h
  workspace.c/.h
  renderer_bridge.c/.h
  replay.c/.h
```

## Determinism expectations

The C runtime should support a replay mode where a cartridge plus canonical input events reproduces the same state digest. The digest does not need generated prose. It should include relationship floats, pressure floats, belief values, memory count, open loop count, habit count, symbol count, and timestep.

Genesis episodes and journal entries use fixed schema versions, bounded arrays,
stable IDs, scalar fields, and UTF-8 text. A C runtime may materialize the
journal as text while retaining the bounded entry table as replay authority.

## Memory firewall rule

User statements, server truth, visible context, sensorium events, validated interpretive beliefs, and explicit authorial cartridge data can become canonical memory candidates.

Renderer output should be logged as a speech event only. It must not be promoted to truth without a separate validation pass.

## Embedded constraints

For low hardware targets, avoid dynamic allocation during turn processing. Allocate fixed pools for memories, symbols, open loops, intentions, sensorium events, and event-log records. Use indexes rather than pointers in serialized state.

## Compatibility tests

Port these Python tests into C harness tests first.

- Cartridge rejects malformed fields.
- Fixed belief resists matching rules.
- Session checksum rejects tampering.
- Event-log replay produces a stable state digest.
- Identity mutation attempt produces character refusal pressure but does not alter immutable identity.
- Long absence changes world/body state and feeds interpretation.
- Renderer text never becomes canonical truth memory.
