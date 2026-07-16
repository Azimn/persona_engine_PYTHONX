# Behavioral Richness

Behavioral Richness makes existing cognition visible. It is not a dialogue
executive and it does not compete with situated synthesis.

## Runtime Chain

```text
observable input
-> bounded input act
-> cartridge behavioral tendency candidate
-> situated synthesis
-> canonical ActionDecision
-> deterministic PerformancePlan
-> optional language realization
```

A tendency proposes one functional move: `probe`, `compare`, `speculate`,
`express_curiosity`, or `continue_working`. Synthesis may inhibit it. The action
resolver still owns whether the organism speaks, delays, gestures, remains
silent, or continues its activity. The renderer receives the selected move and
performance constraints; it never selects the move.

## Bounded State

- At most 12 tendencies are loaded from a cartridge.
- Tendencies use known input acts and moves only.
- Bias is bounded to `[-0.5, 0.5]`.
- Familiarity, pressure, memory, and activity requirements are explicit.
- Cooldown is bounded to 32 turns and recent use history to 24 entries.
- Exact generated sentences are not learned as tendencies.
- Core code contains no character names or character prose.

Activity callbacks are deterministic performance records. A plan may expose
that an actual activity was continued, paused, resumed, completed, failed,
abandoned, or changed. The renderer can phrase that transition but cannot
invent it.

## Life Callbacks

Elapsed-time returns may propose one grounded callback from existing state:

- `activity_update` reports the actual activity that survived or emerged during
  bounded idle catch-up, without claiming objective progress;
- `return_to_topic` may surface an ordinary open loop offline, while a
  capability-dependent loop still waits for its required renderer or tool;
- `reminisce` remains grounded in considered autobiographical memory.

Activity callbacks carry source keys and are announced at most once per source
within the bounded 16-entry callback history. They are
conversation candidates, so regulation, identity protection, pressure,
intentions, and field-width limits may inhibit them.

When offline expression says it retained a question, the engine submits one
canonical journal world action to World Authority, with speech as a coordinated
performance channel rather than a second action. The journal entry is subjective
character text and the writing event is objective; neither makes the note's
claim objectively true.

The journal is an inventory artifact and private recall tool, not a default
conversation prop. Its existence is not surfaced merely because the user
returns. A host or selected character action may read, write, or disclose it
when conversation and access rules make that relevant.

## Behavioral Proof

Automated diagnostics record move diversity, tendency use, activity callbacks,
continuity moves, and exact repetition per speaker so a repetitive scripted
actor is not confused with repetitive character output. Reports also include
`illusion_review.json`, a blank blind
human-review form covering occupation, interests, natural memory, caused
surprise, repetition, prior life, assistant drift, and desire to continue.

These measures are diagnostic. They do not update character state.
