# Offline Conversation

The portable offline organism is deliberately limited, but it should remain a
continuous person rather than a disconnected error message or phrase dispenser.
It uses classic game-dialogue techniques: bounded discourse acts, contextual
storylet selection, shuffle bags, cooldowns, persistent conversation threads,
and memory-grounded reminiscence.

The authored production method and future-character checklist are documented
in `OFFLINE_DIALOGUE_AUTHORING.md`.

## Ownership

`ConversationCandidate` is a deterministic candidate, not a second executive.
It classifies the observable input and proposes one bounded move:

```text
basic_reply
reminisce
reminisce_and_note
defer_and_note
return_to_topic
acknowledge_nonverbal
ask_clarification
```

The candidate enters situated synthesis. `ActionDecision` still owns whether
the character speaks, gestures, continues an activity, delays, or remains
silent. `PerformancePlan` still owns realization channels. The renderer still
owns wording only.

## Reminiscence

Offline reminiscence requires a prior autobiographical memory admitted to the
considered synthesis field. The realization may use that memory and the current
autobiographical meaning, but cannot add events or connective facts.

If a question asks for analysis beyond offline capability while also touching
a memory, the character may reminisce about the grounded experience and retain
the larger question as pending. Memory supplies lived material; it does not
pretend to supply unavailable reasoning.

## Conversation Notes

Conversation notes reuse `OpenLoop`. They add bounded metadata, including the
resolution artifact and the character's later position:

```text
topic_key
actor_id
source_event_id
reason
required_capability
status
resolution_artifact_id
character_position
```

At most 64 open loops are retained. A note requiring `language_model` changes
from `pending` to `ready` when an approved model renderer is connected. It must
still survive synthesis before it can become `return_to_topic`. Surfacing a
topic does not resolve it; renderer output cannot complete canonical business.

The personal journal remains a tangible character-owned world artifact written
only through the existing journal action boundary. An unresolved offline
question creates both working conversational business and a private
first-person field note. Approved later examination adds a research note and a
bounded position. Conversation may return to the position without announcing
the diary or exposing its private text.

## Authored Topic Track

The portable renderer uses cartridge-authored patterns and response families
for important subjects. The topic track does not choose action. It realizes a
selected speech act using listener-specific discussion depth, current activity,
relationship state, memory tags, and recent fragment history.

Explicit patterns outrank aliases and vocabulary. A topic pack distinguishes
first mention, ordinary discussion, expansion, grounded memory, uncertainty,
irritation, refusal, repetition, relationship disclosure, callbacks, activity,
and closure. Partial or unknown analytical material still routes to the diary
handoff rather than receiving invented expertise.

## Repetition Control

Offline realization stores a bounded shuffle history:

- 24 recent component IDs globally
- 8 recent component IDs per actor
- at most 16 actor histories

Component IDs and ring buffers are directly portable to fixed C arrays. The
history survives save and reload. Frequently heard lines are exhausted before
recent components become attractive again.

## Failure Behavior

- unfamiliar analysis becomes a private field note rather than invented expertise
- low-information input may receive gesture or continued activity with zero
  model calls
- a failed model reconnection falls back to offline wording and leaves the
  topic unresolved
- private notes and realization history appear only in the inspector
- `external_model_calls` distinguishes actual Ollama/API use from deterministic
  offline expression-renderer invocation
