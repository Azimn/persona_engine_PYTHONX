# Conversational Plasticity

Conversational plasticity is the deterministic realization layer between a
canonical `ActionDecision` and its multimodal `PerformancePlan`. It changes how
an already-selected action conducts the exchange. It does not decide whether
the character answers, refuses, asks, remembers, withdraws, or speaks.

```text
ConversationContinuityState
-> conversation candidates
-> situated synthesis
-> ActionDecision
-> ConversationChoreographyPlan
-> PerformancePlan
-> offline grammar or model renderer
```

## Choreography Record

The bounded plan records rhetorical strategy, trajectory phase,
conversational energy, response span, answer shape, pacing, disclosure depth,
initiative level, activity relationship, resolution policy, memory role, the
already-selected optional extension, and a compact trajectory signature.

Conversational energy is derived from current body energy, fatigue, pressure,
topic importance, initiative, familiarity, and perceived confidence. It is not
a new need, mood, or random variable.

## Authority

`ConversationChoreographyPlan` is replay-authoritative deterministic
realization state. It is not canonical cognition or a world fact. It may not:

- change action kind, target, intention, or communicative function;
- invent an optional extension;
- turn a non-speech action into speech;
- invent or disclose memory;
- reveal withheld private state;
- resolve a topic, relationship conflict, or obligation in canonical state.

The performance planner consumes energy, answer shape, pacing, and activity
relationship. The renderer receives the bounded plan as a realization
constraint. Offline rendering may shorten or stage existing authored content,
but it may not manufacture content to satisfy a shape.

## Repetition Control

Each per-actor continuity state retains eight recent trajectory signatures.
The planner searches a small Cartesian set of valid strategies, spans, and
answer shapes and selects the least recently repeated valid combination using
a stable seed. Meaningful repetition remains possible when the available
action and obligation genuinely constrain the turn.

Playtests measure exact speech, exact nonverbal performance, semantic-move,
behavioral-strategy, and full-trajectory repetition separately. They also
report strategy entropy, dominant strategy share, energy bands, response spans,
memory roles, and both pre-selection and post-turn topic transitions. A high
semantic-repeat rate is a failure even when every sentence is textually unique.
Entropy is not maximized: a recognizable character should have preferences
without collapsing into one repeated interaction pattern.

Character crossplay carries a generated response into the next actor turn
without executing or recording it twice. Nonverbal performance remains visible
but reaches the other character as structured nonverbal context, not as a
literal utterance such as `gesture:minimal`. These host contracts are necessary
for repetition metrics to describe character behavior rather than harness
artifacts.

## C99 Shape

The portable plan is one fixed record of bounded enums, a `uint32` actor ID,
one bounded energy scalar, stable IDs, a short reason-code array, and one
trajectory signature. The continuity state adds eight fixed trajectory slots.
Planning is a bounded scan over a small product of valid enum choices. It needs
no model, embedding, dynamic graph, or unbounded transcript.
