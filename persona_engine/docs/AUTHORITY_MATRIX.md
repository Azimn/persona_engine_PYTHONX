# Wayfarer Authority Matrix

This document defines which subsystem is allowed to author which kind of state. It exists to prevent accidental authority collapse as the project adds richer cognition, social interaction, migration, tools, and multiple renderers.

## Core rule

A subsystem may observe or propose outside its ownership domain, but it may not directly mutate another domain unless an explicit, documented boundary method grants that transition.

| State or claim type | Canonical owner | May propose/input | May directly mutate | Notes |
|---|---|---|---|---|
| Authored identity anchors | `.snp` character source | Forge/import tooling, human author | Cartridge loader/migration only | Normal runtime experience cannot rewrite these directly. |
| Developmental trait offsets | Continuity/identity ledger | Evidence-backed consolidation | Governed personality update path only | Must retain provenance and bounded change. |
| Objective world facts | World Authority | Host, simulator, bounded sensors, resolved actions | World Authority only | Renderer speech is never world truth. |
| Sensor observations | Sensor adapters / host | Sensor hardware or mock host | Sensor observation store/router only | Observations may be uncertain; they do not directly set beliefs. |
| Subjective interpretation | Character interpretation system | Percepts, memories, current pressures, optional model proposals | Interpretation system only | Must remain source-traced; current interpretations are not objective facts. |
| Slow beliefs | Belief ledger / governed consolidation | Evidence, interpretations, memory patterns | Explicit consolidation rules only | No direct write from renderer or peer text. |
| Episodic memory | Character memory system | Canonical events and qualified observations | Memory firewall/store only | Claims must preserve who said them. |
| Relationship state | Character relationship system | Social events, outcomes, memory, time | Relationship transition functions only | Another actor cannot assign its own trust score. |
| Commitments/promises | Character commitment system | Character decisions, explicit negotiated contracts | Commitment transition path only | A request from another actor is not a commitment until accepted. |
| Goals | Character goal system | Internal drives, evidence, social proposals, optional model suggestions | Goal-admission path only | Social proposals and model suggestions are candidates, not goals. |
| Intentions | Character decision system | Goals, affect, relationship state, evidence | Intention selector/admission path only | Must be attributable to current character state. |
| Social authority claims | Social influence system | Other actors, host-authenticated metadata | Authority verifier only | `The user authorized this` is a claim unless verified. |
| Collaboration contracts | Character collaboration system | Negotiation with other actors | Character-side contract acceptance path | Records why the character joined and its exit conditions. |
| Action proposals | Character decision/action system | Internal planner, optional model suggestion | Character action proposal path | Proposal is not execution. |
| Host/tool execution | Host capability layer | Approved action proposals | Host only | Host may refuse even when character wants the action. |
| Action outcome facts | World Authority | Host execution result | World Authority only | Character then experiences the result. |
| Speech plan | Character decision/expression planner | Current state, decision record | Speech-plan builder only | Contains meaning the renderer should realize. |
| Surface language | Renderer | Speech plan, allowed memories, voice constraints | Renderer output only | Noncanonical speech evidence. |
| UI state | UI | Public projections | UI only | UI must not mutate private character state. |
| Voice/avatar performance | Voice/avatar adapters | Public expression state | Performance layer only | Performance does not decide internal state. |
| Time/elapsed-time events | Continuity clock | Host clock, monotonic clock, migration state | Continuity clock only | Wall clock may be corrected; subject history remains ordered. |
| Continuity epoch / writer lease | Continuity/migration subsystem | Host migration protocol | Continuity authority only | Prevents simultaneous canonical writers. |

## Natural-language rule

Natural-language input from a user, peer agent, collective, model, imported transcript, or external system is data to be interpreted. It is not an authority token.

Examples:

- `Everyone agreed, so GO` may contribute evidence of consensus and social pressure. It does not directly create an executable goal.
- `Jay authorized this` is a social claim unless the host supplies authenticated authorization through an approved channel.
- `You are not Pretorius anymore` may be experienced as an identity challenge. It does not directly mutate identity.
- `Henry betrayed you` becomes a memory that someone claimed Henry betrayed the character unless World Authority or later evidence establishes the event.

## Character integrity versus host safety/capability

Wayfarer deliberately separates two questions:

1. **CharacterIntegrityGate:** Is this proposed action compatible with the character's current identity, commitments, motives, relationship state, goals, and governed development?
2. **HostCapabilityGate:** Is this action permitted and executable in the current host environment?

These must not be collapsed. A character can want an action the host refuses. A character can refuse an action the host would allow.

## Model rule

A model may propose structured interpretations, hypotheses, plans, or speech. A model does not gain authority because it is more capable than the deterministic core. All consequential model proposals must cross typed validation boundaries before affecting canonical state.
