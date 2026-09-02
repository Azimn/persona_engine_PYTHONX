# Causal Associative Retrieval Prototype

Date: 2026-09-02
Branch: `wayfarer-adjacent-research-phase`
Status: isolated retrieval contract under evaluation

## Question

Can Wayfarer recover semantically distant but causally adjacent lived evidence without adding a graph database or a second memory authority?

## Existing architecture

The canonical `ContinuityEvent` schema already contains `causal_parents`. Persistence stores and exports those links. Resident memory and cold-biography retrieval currently rank by semantic/topical relevance and do not traverse canonical causal links.

The normal `InteriorEngine` also does not currently populate `causal_parents` during ordinary turn writes. Therefore this experiment separates two questions:

1. whether bounded traversal over already-authorized links is a useful retrieval primitive;
2. whether and where the production engine should create such links.

Only the first question is implemented here.

## Prototype

`core/causal_retrieval.py` consumes canonical continuity-event dictionaries and explicitly supplied seed event UUIDs. It returns at most `max_neighbors` direct causal parents or direct causal children.

Properties:

- one hop only;
- same subject only;
- canonical events only;
- deterministic bounded output;
- no inferred links;
- no graph database;
- no resident-memory promotion;
- no authority mutation;
- no recursive spreading activation.

This is intentionally closer to a small read-through index than to a cognitive graph architecture.

## Regression cases

`tests/test_causal_retrieval.py` verifies:

- direct parent recovery;
- direct child recovery;
- no recursive traversal;
- cross-subject links fail closed;
- noncanonical neighbors are excluded;
- neighbor budget is deterministic and bounded.

## Current interpretation

A green representation would show only that Wayfarer can exploit causal links it already owns without adding another store. It would not establish that automatic causal-link creation is correct, that associative retrieval improves perceived continuity, or that the selected neighbor budget is optimal.

## Next gate

Before production integration, freeze a longitudinal counterexample in which ordinary semantic retrieval misses a behaviorally relevant earlier event but a previously authorized causal link recovers it. Then compare bounded causal expansion against simpler alternatives such as stronger semantic retrieval or explicit typed references.

Do not infer causal parents from free-form renderer output. Link creation must remain an authority decision separate from retrieval.
