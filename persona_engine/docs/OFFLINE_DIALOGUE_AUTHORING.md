# Offline Dialogue Authoring

Offline conversation is a game-dialogue product, not a reduced imitation of
the model renderer. The organism remains shared, but the language adapter is
deliberately retro:

```text
observable input
-> bounded intent and authored-pattern match
-> character, relationship, activity, memory, and listener state
-> synthesis-owned action
-> cartridge-authored response family
-> deterministic offline realization
```

The target is not universal comprehension. A character should remain
recognizable, discuss its important subjects, use lived memories when they
advance the exchange, avoid exposing its response pool, and retain unfamiliar
material for later work.

## Production Rule

No new conversational subsystem should be added until a demonstrated
player-facing failure cannot be corrected by, in order:

1. authored content;
2. pattern coverage or response-selection policy;
3. an existing organism state field;
4. one small local state addition;
5. a new subsystem as the last resort.

The deferred active-claim ledger is an example of a plausible idea that has
not yet earned implementation. Topic continuity, repetition, and modality
handoff must first be judged in real visits.

## Shared And Adapter-Owned State

The shared organism owns identity, memory, relationships, activity, pressure,
open loops, action, and the personal journal. Both online and offline
realizers consume those owners.

The offline adapter owns only:

- bounded pattern and topic recognition;
- cartridge-authored response families;
- recent fragment suppression;
- per-listener topic familiarity;
- partial-understanding and unknown-subject routing.

It does not create beliefs, memories, actions, or objective facts.

## The Diary

Every character possesses a journal as a tangible world object. Its name and
writing style are cartridge-authored. Reading and writing occur through World
Authority, and entries remain private unless a later selected action permits
disclosure.

The diary has two compatible uses:

1. ordinary first-person notes, reflections, research records, and recall;
2. first-person capture of an offline question the character cannot yet
   examine.

The second use supports modality handoff:

```text
offline unknown question
-> private field note plus unresolved open loop
-> approved online/external examination
-> first-person research note plus bounded character position
-> later offline return to the shared conversational thread
```

The spoken character normally says only that the issue was retained. It does
not announce the diary, quote private text, or turn the artifact into a
recurring conversational prop.

## Topic Pack

A major topic should normally contain:

- aliases, specific patterns, concept words, and relevant memory tags;
- 2 openings;
- 2 first-mention positions;
- 6 to 8 ordinary fragments;
- 2 expanded positions;
- 2 memory-supported forms;
- 2 to 4 uncertainty forms;
- 2 irritation forms;
- 2 refusals;
- 3 repetition forms;
- 2 relationship-sensitive disclosures;
- 2 callbacks, activity forms, and closings.

This is roughly 28 to 40 short fragments. Minor topics should omit families
they cannot honestly support. Storage is not the limiting resource; exposed
pool machinery is.

Author fragments as positions and moves, not synonym lists. Orthogonal
variation should come from topic depth, current activity, pressure,
relationship, memory, disclosure, and recent use.

## Pattern Order

Candidate recognition proceeds from strongest to weakest:

```text
exact authored phrase
specific wildcard pattern
known entity plus intent
known entity
known topic vocabulary
general conversational intent
partial recognition
unknown
```

Wildcard patterns are cartridge content. They should cover ordinary player
phrasings, including pronoun follow-ups, without pretending to understand an
unbounded domain. Unknown technical analysis must remain unknown.

## Character Difference

The fifteen-minute test is not a friendliness test.

Kiki should usually welcome sustained contact, remain warm and intelligent,
use her pre-2000 cultural vocabulary as a thinking tool, and preserve honest
uncertainty.

Pretorius may regard the visitor as an interruption. A successful visit means
the player can earn his interest through precision, relevant work, or a sharp
question. It does not mean making him apologetic, agreeable, or assistant-like.

## Experience Checkpoint

Each major character must pass a deterministic visit containing:

- arrival while the character is occupied;
- five known subjects;
- at least two contextual follow-ups;
- one grounded autobiographical recollection where available;
- one repeated question;
- one unknown analytical subject;
- one apology, correction, or interruption;
- private diary capture;
- approved online completion;
- later offline return;
- departure;
- zero external model calls.

Judge the transcript directly. Record:

- exact and semantic repetition;
- incorrect topic matches;
- false unknowns and invented answers;
- unsolicited questions;
- assistant drift;
- character-specific texture;
- whether activity remains perceptible;
- whether the modality handoff feels continuous;
- whether the player would choose another visit.

Tests protect the experience, but do not define enjoyment. Human review
remains the release gate.

## C99 Boundary

The runtime remains suitable for fixed-size implementations:

- bounded topic count;
- bounded fragments per family;
- bounded per-listener thread history;
- stable string IDs;
- deterministic matching and selection;
- no recursive structures;
- no required model, network, embedding, or dependency.

Character prose stays in cartridges. Core code stays character-agnostic.
