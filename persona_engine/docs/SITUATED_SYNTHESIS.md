# Situated Synthesis

The situated synthesis layer formalizes the bounded selection already performed before workspace construction. It adds no model call and stores no hidden reasoning.

## Integration Capacity

Capacity is a derived value and is not independently mutable:

```text
capacity = clamp(
    0.32
    + 0.40 * energy
    + 0.20 * (1 - fatigue)
    - 0.15 * sensory_load
    - 0.25 * dominant_pressure
    - 0.10 * unresolved_conflict
    - 0.08 * min(1, open_loop_count / 4)
    - 0.07 * interruption_load
    - 0.08 * recent_failure
)
```

Engine energy is the mean of legacy engine energy and body energy. Every input and the result are clamped to `0.0..1.0`.

## Field Width

- Capacity at least `0.75`: six influences.
- Capacity at least `0.50`: four influences.
- Capacity at least `0.25`: two influences.
- Lower capacity: one influence.

Candidates come from present evidence, pressures, explained memory retrieval, validated capability artifacts, intentions, open loops, habits, relationship concern, current activity, and immediate body needs. Candidate work is bounded before deterministic sorting.

Fallible self-monitoring evaluates the base influence field once, then adds at
most three `regulation` influences. Synthesis still runs exactly once.
Regulation does not automatically outrank evidence, identity, safety, or urgent
intentions. `SynthesisResult.selected_regulation_candidate_id` records the
highest considered regulation candidate; `ActionDecision` records it only if
the canonical resolver actually applies it.

Current autobiographical meaning may enter as structured evidence after its
linked memory is retrieved. It is neither an action nor a second executive.
Superseded meaning remains outside ordinary synthesis; low-capacity emotional
intrusion is capped at `0.25`.

Under strain, immediate cues, pressure, established habits, and emotionally congruent memories receive bounded boosts. Distant intentions and contradictory evidence receive bounded penalties. Identity and authority gates remain outside this selection and are always active.

## Records And Persistence

`SynthesisResult` records considered and inhibited influences, unresolved conflicts, selected intention, habit, or regulation, reality support, and concise structured reasons. `ActionCompletion` links the synthesis to the existing world event, subjective experience, expected outcome, and actual outcome.

Both records use the existing event log. No new mutable persistence field or parallel event system is required. The read-only inspector exposes the latest records.

## Replay And Portability

Selection is deterministic for the same ordered state and uses stable digest IDs. Records contain bounded scalar values, strings, and tuples that serialize to JSON and map directly to fixed C99 records.
