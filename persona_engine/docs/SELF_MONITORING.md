# Fallible Self-Monitoring

`SelfMonitor` is a deterministic, character-shaped estimate of the organism's
current cognitive condition. It is not a second executive and does not call a
model.

The authority chain is:

```text
actual engine diagnostics
    -> fallible perceived diagnostics
    -> bounded regulation candidates
    -> situated synthesis
    -> ActionDecision
    -> PerformancePlan
    -> optional renderer wording
```

## Actual And Perceived State

The monitor reads derived integration capacity, fatigue, dominant pressure,
identity threat, recent failure, retrieval confidence, and structured
synthesis influences. A cartridge profile shapes introspective accuracy, bias
awareness, uncertainty tolerance, admission, concealment, externalization, and
correction.

Stable seeded error allows the perceived capacity to be accurate,
underestimated, or defensively overestimated. Conflict detection may notice or
miss structured conflicts reproducibly. These are character-perceived
diagnostics, not objective claims about another person.

## Regulation

The monitor emits at most three candidates: pause, delay, clarification,
deferred judgment, self-correction, concealed uncertainty, withdrawal,
doubling down, or habitual continuation. Candidates are immutable evidence.
They must enter the existing bounded synthesis and may be inhibited by
identity, safety, urgent intention, evidence, or stronger situated influences.

Only an applied candidate is referenced by `ActionDecision`. Regulation never
rewrites the selected intention or bypasses action validation.

## Visibility

`SelfMonitorResult` is a canonical cognitive record available in persistence,
replay, causal evaluation, and the private developer inspector. Public status
does not expose it.

When speech is selected, `WorkspaceFrame` may contain a short reportable
summary such as low perceived confidence, uncertain memory, noticed conflict,
or selected self-correction. It never contains actual capacity, missed
conflict IDs, raw confidence values, or unreportable regulation candidates.

The renderer realizes wording only. It does not choose what the character
noticed or how regulation affected the action.

Noticed contradiction may make an evidence-linked autobiographical revision
eligible. Missed contradiction creates no revision; evidence may remain in a
bounded deferred record for later calm reconsideration.

## Portability

The implementation uses bounded floats, stable IDs, tuples, sorted influences,
and a stable turn seed. No global random state, model, embedding, network, or
new persistence technology is required. The records map directly to fixed C99
structs and bounded arrays.
