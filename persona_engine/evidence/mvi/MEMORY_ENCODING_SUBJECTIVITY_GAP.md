# Memory Encoding Subjectivity Gap

Date: 2026-09-02
Branch: `wayfarer-adjacent-research-phase`
Status: baseline experiment; no new encoding mechanism implemented

## Question

Do different Wayfarer characters currently store the same neutral experience as meaningfully different autobiographical memory records, or is character-specific interpretation applied only later?

## Existing architecture

Wayfarer already has several subject-specific downstream mechanisms. Relationship state, pressures, behavioral disposition, private cognition, retrieval, decision constraints, and rendering can differ by character.

The ordinary `USER_TOLD` memory write in `InteriorEngine._post_speech_update`, however, constructs a `MemoryUnit` from the incoming event, appraisal/risk values, and identity-violation status. It does not consult cartridge temperament, values, goals, cognitive themes, or a character-owned encoding profile.

`OrganismTick` similarly writes sensorium memories through generic fixed relevance rules. `private_cognition.validate_and_apply` explicitly does not mutate memory.

## Baseline

`evaluation/memory_encoding_subjectivity.py` sends the same neutral event to three existing contrasting cartridges:

- `friendly.snp`
- `pretorius.snp`
- `rival.snp`

The event is:

```text
I found a small silver locket in the hallway.
```

The probe compares only the typed `USER_TOLD` memory representation, excluding generated IDs and timestamps.

Expected baseline contract:

```text
case_count = 3
unique_memory_signatures = 1
all_memory_signatures_identical = true
character_profile_is_encoding_input = false
```

If the baseline passes, it demonstrates only that the neutral autobiographical record is character-invariant at write time. It does not establish that character-relative encoding is always desirable or that the current downstream differences are insufficient.

## Why no new mechanism is added yet

A personality-conditioned memory encoder could easily become another unvalidated psychology layer. The current architecture should not add OCEAN-weighted salience, trait-specific distortion, or free-form LLM memory rewriting simply because related systems do so.

## Next gate

Freeze a longitudinal behavior where character-relative encoding is necessary. A useful experiment would expose two contrasting subjects to the same event and later ask an indirect question after substantial interference. If current retrieval/decision behavior converges when the characters should plausibly retain different aspects of the event, then test the smallest encoding projection that fixes that failure.

Any future mechanism should preserve the immutable experience separately from its subject-relative salience or interpretation. The character must be allowed to reinterpret an event later without rewriting what actually happened.
