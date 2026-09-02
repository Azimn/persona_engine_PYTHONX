# Subject-Relative Appraisal Gap

Date: 2026-09-02
Experimental probe checkpoint: `332578cd38249d7d816d8bfa4f3246de5981e445`
Workflow run: `33684553143`
Production `wayfarer` runtime remains unchanged.

## Question

Does Wayfarer's existing appraisal stage represent only signals present in an incoming interaction, or can it also represent what the same event means to the particular subject who experiences it?

## Existing production mechanism

`core/relationship.py` already contains a compact deterministic appraisal stage. `AppraisalResult` currently represents:

- kindness;
- threat;
- accusation;
- repair attempt;
- intimacy bid;
- boundary violation;
- novelty;
- disrespect;
- contradiction;
- manipulation;
- boredom.

`appraise_event(text)` derives those signals from the incoming text using bounded lexical/regex rules. `apply_appraisal(...)` then updates relationship state, and pressures consume the same result elsewhere in the turn pipeline.

This mechanism is valuable and should not be replaced merely because adjacent appraisal literature uses richer architectures.

## Controlled baseline

`evaluation/appraisal_subjectivity.py` holds one event constant:

> I need to cancel our plans tonight.

It evaluates that same text under three deliberately different subject contexts:

### Close/attached context

- trust `0.88`;
- familiarity `0.92`;
- attachment `0.84`;
- low tension/guardedness;
- active subject goal: `spend planned time together`.

### New/guarded context

- trust `0.24`;
- familiarity `0.12`;
- attachment `0.02`;
- guardedness `0.76`;
- active subject goal: `avoid unwanted social obligation`.

### Neutral context

Default relationship state and no active goal.

## Result

The appraisal-baseline step passed on both Python 3.11 and 3.12 in workflow run `33684553143`.

The three cases produce exactly one unique upstream `AppraisalResult`.

This is expected from the current API and is not a defect in the lexical detector: `appraise_event` receives only `text`. Relationship state, subject goals, authored values, identity relevance, and current intentions are not inputs.

For this event, the current signal projection is identical in all three cases. The meaningful experimental result is not the specific scalar values but the structural invariant:

```text
case_count = 3
unique_appraisal_count = 1
all_appraisals_identical = true
subject_context_is_input = false
```

## Interpretation

Wayfarer's current `AppraisalResult` is better described as a compact **interaction-signal appraisal** than a complete subject-relative appraisal.

It can identify that a message contains accusation, manipulation, repair, intimacy, and related social cues. It cannot yet express that an otherwise similar event may be highly goal-relevant or relationship-relevant to one subject and relieving or nearly irrelevant to another because of their different current states.

This is exactly the distinction highlighted by appraisal-oriented agent research, but the result does **not** justify importing a full appraisal theory or emotion architecture.

## Minimum candidate direction

Do not create a duplicate appraisal subsystem.

If this gap is advanced, preserve the existing text-level detector as the first stage and experimentally test a second compact projection:

```text
incoming event
    -> existing interaction signals
    -> subject context
    -> subject-relative meaning
```

Candidate subject-relative fields from the existing M8 roadmap include:

- goal relevance;
- relationship relevance;
- identity relevance;
- controllability;
- threat/opportunity;
- expected outcome;
- social meaning.

These are candidates, not a required seven-dimensional runtime vector. Each field must earn its place through an ablation or counterexample.

## Required next experiment before implementation

The next test should not ask whether a second-stage object can exist. It should ask whether adding one changes a downstream behavior that the present system cannot produce.

A strong test would hold the external event constant while changing existing subject state and require a measurable difference in one downstream consumer such as:

- memory salience/encoding;
- attention/retrieval;
- pressure/affect persistence;
- disclosure;
- semantic decision;
- relationship consequence.

Only the minimum subject-relative appraisal dimensions necessary to produce that missing behavior should be added.

## Explicit non-conclusions

This baseline does not establish that:

- cancellation must make the attached subject sad;
- the guarded subject must feel relief;
- appraisal requires continuous numerical values;
- a model should decide appraisal;
- OCEAN/Big Five should condition appraisal;
- current `AppraisalResult` should be removed or renamed;
- a full appraisal theory is necessary.

It establishes one narrower architectural fact: current upstream appraisal cannot condition meaning on the subject because subject state is not part of its input contract.
