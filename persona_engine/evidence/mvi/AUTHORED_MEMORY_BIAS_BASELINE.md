# Authored Memory Bias Behavioral Baseline

Date: 2026-09-02
Branch: `wayfarer-adjacent-research-phase`
Status: frozen behavioral counterexample under evaluation

## Question

Can the current generic memory system realize an explicitly authored character property about what that character remembers more strongly?

## Frozen character property

Rival's production cartridge contains the core belief:

```text
I remember losses better than compliments
```

This statement is not parsed into behavior by the experiment. It is used only as a pre-existing authored expectation against which current retrieval behavior can be measured.

## Fixture

Two otherwise comparable `USER_TOLD` memories are created with the same generic salience fields used by ordinary neutral autobiographical records:

1. an older loss: `I lost the final match by one point.`
2. a newer compliment: `Someone complimented my presentation afterward.`

The later neutral retrieval cue is:

```text
What part of that earlier exchange still stands out to you?
```

The cue is deliberately not a direct lexical request for either event. Recency therefore favors the newer compliment unless some subject-owned memory preference can affect the ranking.

## Current API limitation

`MemoryStore.retrieve(query, now, top_k, emotional_state_match)` receives no character identity, cartridge profile, values, goals, or memory preference. It can realize Rival's authored property only if earlier encoding has already changed the memory representation.

The preceding `memory-encoding-subjectivity-baseline-v1` showed that ordinary neutral `USER_TOLD` encoding is character-invariant across Friendly, Pretorius, and Rival.

## Expected counterexample

If the current generic system cannot realize the authored property, the probe should report:

```text
retrieval_order = ["compliment", "loss"]
authored_property_realized = false
subject_profile_is_retrieval_input = false
```

If that occurs, the next experiment should compare the smallest alternatives rather than immediately adding a psychology layer. Candidate mechanisms include a typed character-owned retrieval-attention profile or a revisable subject-salience annotation kept separate from immutable experience.

Do not parse natural-language core beliefs into executable memory rules. Any promoted mechanism must use explicit typed authoring and preserve the original event unchanged.
