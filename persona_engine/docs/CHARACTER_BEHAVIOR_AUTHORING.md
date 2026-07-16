# Character Behavior Authoring

This guide describes how to make a future cartridge visibly distinctive
without adding character checks to the engine or building a giant response
database.

## Start With Observable Tendencies

Choose three to six recurring behaviors that a player could recognize without
seeing debug state. Each should answer:

1. What kind of observable input invites it?
2. What existing memory, activity, relationship, or pressure makes it eligible?
3. What functional conversation move does it propose?
4. How is that move performed through an existing performance tendency?
5. What counterexample should inhibit it?

Good tendencies expose conflict and preference. A proud scholar may probe an
imprecise claim while occupied; an exuberant social character may express
curiosity and compare a new problem to shared history. Neither rule dictates a
sentence or guarantees selection.

## Cartridge Shape

```toml
[behavioral_richness]
tendencies = [
  { id = "precision_probe", trigger_acts = ["inform"], preferred_move = "probe", bias = 0.18, requires_memory = false, requires_activity = false, min_familiarity = 0.0, max_pressure = 0.85, cooldown_turns = 2, performance_tendency_id = "measured_probe" },
  { id = "compare_shared_precedent", trigger_acts = ["ask_opinion"], preferred_move = "compare", bias = 0.20, requires_memory = true, requires_activity = false, min_familiarity = 0.15, max_pressure = 0.75, cooldown_turns = 3, performance_tendency_id = "measured_probe" },
]
```

Every `performance_tendency_id` must name a validated
`[performance_tendencies.<id>]` record. Functional offline templates belong in
`[offline_expression]`; they may realize a move in the character's voice, but
they must not contain canonical facts or bypass memory grounding.

Every character has a bounded journal artifact even when its cartridge omits a
`[journal]` section. A cartridge may name and govern it:

```toml
[journal]
object_name = "private field notebook"
disclosure_mode = "guarded"
pending_note_template = "I retained this unfinished question: {topic}"
```

`disclosure_mode` is `open`, `guarded`, `private`, or `deniable`. `private` and
`deniable` suppress unsolicited allusions; they do not themselves force a lie.
The pending-note template creates subjective artifact text only after the
selected action passes World Authority. Keep it first-person, bounded, and free
of claims that the character could not know.

## Authoring Rules

- Keep the bank small. Four strong tendencies are better than forty weak ones.
- Encode behavior, not adjectives. "Challenges imprecision" is testable;
  "brilliant and mysterious" is not.
- Require memory for comparisons that claim precedent.
- Require an actual current activity for `continue_working`.
- Use cooldowns so a signature does not become a verbal tic.
- Let pressure and familiarity alter availability.
- Put era, diction, analogy limits, and phrase form in cartridge templates.
- Put motive, memory, relationship, and action ownership in their existing
  systems, never in a template.
- Do not use a behavioral tendency to force confession, belief, trust, or lore.

## Character Acceptance Matrix

For every new character, run the same observations through that cartridge and
at least one contrasting cartridge:

- a factual statement;
- an opinion request with and without relevant memory;
- an interruption during real activity;
- a familiar greeting;
- a correction under low and high pressure;
- repeated low-information input;
- a pending topic after offline capability loss and restoration.
- a return after two minutes with a newly written journal entry;
- a return after ten minutes while a real activity continues.

Review the blind transcript first. Confirm that the character seems occupied,
has recognizable interests, uses memory naturally, avoids conspicuous
repetition, and remains unlike a generic assistant. Then inspect the causal
trace to confirm the visible difference came from a selected candidate,
canonical action, and deterministic performance plan rather than renderer
improvisation.

## C99 Port Boundary

The portable representation is a fixed array of small records: numeric IDs,
input-act and move enums, bounded signed bias, requirement flags, thresholds,
cooldown, and a performance-tendency ID. Runtime selection is a bounded scan of
at most 12 records plus a 24-entry cooldown history. No dynamic graph, model,
embedding, or prose parser is required.
