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

## Behavioral Proof

Automated diagnostics record move diversity, tendency use, activity callbacks,
continuity moves, and exact repetition per speaker so a repetitive scripted
actor is not confused with repetitive character output. Reports also include
`illusion_review.json`, a blank blind
human-review form covering occupation, interests, natural memory, caused
surprise, repetition, prior life, assistant drift, and desire to continue.

These measures are diagnostic. They do not update character state.
