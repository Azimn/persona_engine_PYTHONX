# Conversation Continuity

Conversation continuity is a bounded per-actor dialogue blackboard. It does not
interpret the world, choose motives, or select actions. It tells existing
synthesis what the current exchange requires and whether one optional
character move is affordable.

## State

Each known actor may have:

- one active topic;
- up to two background topics;
- topic depth from 1 to 12;
- freshness and emotional importance in `[0, 1]`;
- at most one pending obligation: answer, clarify, acknowledge, repair, or
  follow up;
- an initiative budget in `[0, 1]`;
- eight recent semantic move signatures;
- eight recent conversation-trajectory signatures;
- the latest transition reason: completed, exhausted, interrupted, avoided, or
  displaced;
- the last action kind.

The store is bounded to 256 actors. Topic matching uses normalized symbolic
overlap plus short pronoun continuation. It does not use an embedding or model.

## Turn Contract

```text
observable input
-> update actor's dialogue blackboard
-> establish obligation
-> retrieve and score memories against active topic
-> propose at most one optional character move
-> situated synthesis
-> ActionDecision
-> deterministic ConversationChoreographyPlan
-> obligation-first PerformancePlan and rendering
-> record semantic move signature
-> clear fulfilled obligation
```

An optional move may be probe, compare, challenge, reminisce, speculate,
express curiosity, or continue working. It is denied when initiative is low,
the same semantic shape was recently used, repair or clarification must remain
undiluted, or a deep topic is exhausted. No extension is a valid turn shape.

Repeated acknowledgment shapes may rotate through speech, gesture, continued
activity, and silence. Attention capture remains explicit; silence does not
mean the input was unnoticed.

## Memory Boundary

Explicit autobiographical questions may use any considered memory retrieved for
the question. Optional comparisons and reminiscence require active- or
background-topic relevance. Topic relevance supplements retrieval and never
changes memory confidence, content, or canonicality.

## Portability

The C99 representation is fixed-size: three topic records, one obligation enum,
one initiative scalar, eight move signatures, eight trajectory signatures, one
transition enum, and one action-kind enum per actor. Selection is a bounded scan with token overlap. No
dynamic graph, recursive dialogue tree, model call, or unbounded transcript is
required.
