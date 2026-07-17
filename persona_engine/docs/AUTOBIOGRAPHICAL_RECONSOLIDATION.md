# Autobiographical Reconsolidation

Persona Engine preserves distinct historical layers:

```text
WorldEvent -> SubjectiveExperience -> MemoryUnit
                 |
                 v
        AutobiographicalInterpretation versions
                 |
                 v
          situated synthesis -> action -> performance
```

## Ownership

- `WorldEvent` owns what objectively happened.
- `SubjectiveExperience` owns what the character perceived and interpreted then.
- `MemoryUnit` owns the consolidated, retrievable first-person trace.
- `AutobiographicalInterpretation` owns what that event currently means.
- `SelfMonitor` owns whether contradiction is noticed.
- `AutobiographicalReconsolidator` validates evidence-linked later meaning.
- Situated synthesis determines whether current meaning affects cognition.
- `ActionDecision` owns outward action; `PerformancePlan` owns realization.
- The renderer owns wording only and cannot create or revise interpretations.

## Non-Destructive Decay

Decay may reduce confidence, encoding strength, lifecycle, and accessibility.
It never rewrites the original perceived summary, interpretation, emotional
residue, event link, provenance, or creation time. `recall_surface()` derives a
faded presentation without storing it as canonical memory content.

Legacy records already destructively faded remain loadable. They are marked
`legacy_destructive_decay`; the lost text is not invented.

## Reconsideration

Revisions require an allowed trigger, linked evidence, adequate actual and
perceived capacity, bounded pressure, and noticed contradiction where
applicable. A missed or overloaded correction becomes a bounded deferred
record. Later calm may reconsider the same evidence but never guarantees
correction.

Histories are append-only, sequential, and capped at eight versions per
experience and 1,024 total records. Reaching a bound refuses a revision; it
does not delete or splice history.

Current meanings can enter synthesis beside retrieved memory. Superseded
meaning is normally diagnostic only. Under low capacity and strong emotional
charge it may intrude with strength capped at `0.25`.

`InterpretationUseOutcome` conservatively records whether meaning was
considered or inhibited. Failure alone never proves an interpretation false.

Developmental Life consumes explicit supporting and contradicting links plus
use outcomes. Learned connectivity modifies activation only; it never rewrites
the autobiographical version chain.

## C99 Portability

Records use schema versions, stable IDs, bounded numbers, tuples, explicit
evidence links, and flat JSON-compatible structures. `core/c99_fixtures.py`
exports a complete history without recursive Python object identity.
