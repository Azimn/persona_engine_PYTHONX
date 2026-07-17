# Conversational Initiative

Conversational initiative is a bounded bridge from existing organism state to
an optional conversational extension. It is not a planner, topic generator, or
second executive.

## Ownership

The initiative assessor may inspect five existing source classes:

- contextually relevant autobiographical memory
- a due open loop
- the current intrinsic activity proposal
- a supported relationship expectation
- a recent objective or bounded life change

It emits at most one `InitiativeProposal`. The proposal carries a stable source
ID, topic key, functional move, score, and reason codes. It cannot invent prose,
facts, memories, goals, or a conversational obligation.

The turn remains:

```text
current obligation and bounded source state
-> InitiativeAssessment
-> optional InitiativeProposal
-> ConversationCandidate
-> situated synthesis
-> ActionDecision
-> choreography and performance
-> offline grammar or model renderer
```

The character first honors the current obligation. Initiative can supply one
optional move only when the obligation, initiative budget, source cooldown,
and continuity gates permit it. Situated synthesis may still reject it. Silence
and nonverbal behavior remain valid outcomes.

## Structural Action Fence

Initiative can select one optional move: `probe`, `compare`, `reminisce`,
`speculate`, `express_curiosity`, or `continue_working`. It cannot replace the
pending obligation, select a target, submit a world action, invent a scene or
content, resolve an open loop, or bypass situated synthesis.

Its direct realization is speech addressed to the current interlocutor.
Existing higher-priority identity, resistance, regulation, and continuity
gates may instead yield gesture, continued activity, delay, silence, or
withdrawal. `world_action` and `observe` are outside the initiative fence.
Runtime validation rejects any future path that crosses this boundary.

## Source Rules

Mirrored `I heard you say` memories, sensorium records, and ambient events are
not initiative memories. Memory initiative requires an already contextualized
autobiographical candidate. Recent source IDs are retained per actor so the
same motive, event, expectation, or memory cannot repeatedly reopen itself.

Intrinsic activity is advanced by bounded idle time before it can become a
source. Accelerated hosts call `advance_time()` once per simulated day; the
method summarizes elapsed life rather than treating an entire day as one
continuous body-exertion tick.

## Diagnostics

Every turn reports one outcome:

- `no_source_eligible`
- `proposal_below_threshold`
- `proposal_inhibited`
- `proposal_selected`
- `proposal_denied_by_synthesis`

Playtest metrics separately report eligible source classes, proposed source
classes, interaction outcomes, and silence reasons. A high silence rate is not
interpretable without this breakdown.

The hardening probe records memory-store size, retrieved candidates,
pre-topic autobiographical candidates, relevance passes, and final contextual
memory eligibility. In empty Kiki/Pretorius crossplay both stores are populated,
but the retrieved candidates contain no autobiographical episodes; its zero is
therefore fixture content, not a topic-threshold artifact. A seeded, plainly
relevant autobiographical episode clears all gates in the contract test.

The same 30-day probe attributes 27 synthesis denials primarily to
`intrinsic_activity`, rather than to unavailable or below-threshold sources.
That is a genuine competition result and should be investigated before source
thresholds are tuned. Semantic-move and trajectory repeat flags overlap on 80%
of flagged turns in this fixture; they are strongly correlated here, but each
also identifies turns the other does not.

The steady-collaborator repeat root is split across two layers: 18 repeats are
authored by the deterministic human policy, while Pretorius contributes four
repeats from the bounded offline clarification realization pool. Those character
turns share the same `clarify|none|speak` move signature and repeat a previously
used clarification line; this is a delivery-pool exhaustion finding, not a
counting artifact or an initiative-selection defect.

The deterministic seven-day `initiative_world_changes_7_days.yaml` scenario
contains ordinary quiet periods and two explicit world changes. It verifies
that changes can become grounded proposals without requiring every turn to
produce speech.

## Porting Bounds

The runtime keeps at most five eligible sources per assessment and eight recent
source IDs per actor. Records use stable IDs, bounded enums, bounded floats, and
flat arrays suitable for a later C99 representation.
