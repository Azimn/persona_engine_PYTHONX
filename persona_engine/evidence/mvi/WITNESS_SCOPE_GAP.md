# Witness / POV Scope Gap Audit

Date: 2026-09-02
Branch: `wayfarer-adjacent-research-phase`
Status: architecture audit only; no runtime change

## Question

Does Wayfarer need a separate point-of-view or witness-memory subsystem to prevent subjects from knowing events they did not observe?

## Existing architecture

`WorldAuthority` already separates objective world facts from character-visible context. Each `WorldFact` carries `visible_to_character`, and sensor observations become bounded facts before downstream interpretation. `InterpretationEngine` consumes visible sources rather than raw hidden world truth.

This means the core single-subject architecture already has the most important authority separation:

objective event != character-visible event != subjective interpretation

A separate witness-memory authority would duplicate existing responsibilities.

## Narrower unresolved issue

The current visibility contract is global at the fact level:

- `WorldFact.visible_to_character` is a boolean;
- `WorldAuthority.get_visible_context(actor_id)` accepts an actor identifier but does not use it when filtering facts.

That is sufficient for the current single-subject host profile, but it may become insufficient if one shared World Authority serves multiple autonomous subjects with different locations, senses, attention, or permissions.

## Why this is not implemented now

The repository has not yet demonstrated that Society Lab or another multi-subject host actually shares one World Authority instance across subjects in a way that produces false shared knowledge.

Changing the schema now to per-actor witness sets, observer ACLs, or event-recipient graphs would therefore be speculative architecture.

## Next gate

Freeze a multi-subject counterexample in which:

1. one world event is objectively true;
2. subject A observes it;
3. subject B does not observe it;
4. both subjects later reason or converse about the event;
5. the current host/world projection incorrectly gives B access to information that only A should possess.

Only if that failure occurs should the minimal fix be evaluated. Candidate fixes should extend existing World Authority visibility rather than create another memory store. Possible forms include actor-scoped visibility metadata or host-provided observation receipts.

No renderer-generated statement should create witness authority.
