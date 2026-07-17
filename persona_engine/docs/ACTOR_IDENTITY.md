# Actor Identity

Persona Engine keeps a bounded social identity registry so a character can
distinguish people without assuming that names are unique or perfectly
remembered.

## Identity Model

Each social referent receives a stable unsigned 32-bit `actor_id`. The runtime
derives that ID deterministically from a host or provenance key such as:

```text
external:discord-48291
external:game-npc-17
genesis:henry frankenstein
character:septimus pretorius
```

The numeric ID is the compact C99-oriented identity. Display names and aliases
are recognition cues, not primary keys. Two records named `Henry` remain
separate and are shown as `Henry-A` and `Henry-B` in inspection. An ambiguous
reference to `Henry` may activate both records; the engine does not silently
merge them.

The host should supply a durable `speaker_id` whenever it has one. Without a
durable identifier, the engine can preserve a session-local person but cannot
prove that a later same-named person is the same individual.

## Social State

`ActorRelationshipStore` owns one existing `RelationshipState` per actor. The
active speaker selects which relationship participates in appraisal,
synthesis, performance, expectations, and dyadic rituals. Switching speakers
does not reset or blend their histories. Relationship records are allocated
lazily when interaction begins; merely appearing in planted history does not
create a mutable relationship.

World events and subjective experiences carry actor IDs through provenance.
Consolidated memories receive `actor:xxxxxxxx` tags. Actor tags provide a
bounded retrieval boost; they do not exclude unrelated evidence or force a
belief about identity.

## Genesis And Sparse History

Cartridge genesis actors use stable `genesis:` keys, so Henry Frankenstein,
Elizabeth, the Monster, and later interlocutors remain distinguishable from
live users with the same names.

Genesis episodes use their historical years for event timestamps. Long periods
without specific episodes remain sparse. A cartridge may mark a representative
episode as a `historical_span_years` chapter summary, but the engine does not
invent thousands of daily memories. Old memories therefore have realistic
recency and decay pressure while explicit cues, salience, emotion, and learned
connections can still retrieve them.

## Bounds And Authority

- actor records: 256 per session
- aliases: 8 per actor
- ID representation: nonzero `uint32`
- names and aliases never establish objective identity by themselves
- actor matching never merges memory, relationship, or world records
- actor relationships are private inspectable state, not public status
- renderers may name an actor but cannot create or merge canonical actors
