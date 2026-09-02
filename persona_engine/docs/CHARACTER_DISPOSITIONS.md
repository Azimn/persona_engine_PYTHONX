# Wayfarer Character Dispositions

## Purpose

Wayfarer must provide common mechanisms without forcing every simulated subject to share the same psychology. Before this phase, several social triggers were coupled directly to one global response policy. An accusation always selected `challenge`, manipulation always selected `go_quiet`, rapid intimacy always selected `deflect`, and boredom always selected `shift_topic`, regardless of which character was running.

That design preserved state continuity but created a convergence risk. Two characters could have different biographies, voices, values, and authored temperaments while still making the same semantic choice when placed under the same social pressure. Surface wording could differ while the engine underneath behaved like one recurring Wayfarer personality.

The behavioral disposition profile is the first narrow separation between generic social-response mechanisms and character-owned preference for those mechanisms.

## Authority boundary

The profile does not own hard identity invariants. If a user attempts an authored prohibited identity mutation, the core still selects `character_refusal` independently of the disposition profile. A cartridge cannot use this profile to turn a protected identity rewrite into ordinary compliance.

The profile also does not outrank explicit subject-owned commitments, canonical history, world authority, or host capability and safety gates. It only selects a preferred response mode for supported soft social triggers when those higher-authority constraints do not already decide the turn.

This distinction is intentional. Personality may determine whether a subject confronts, deflects, withdraws, redirects, shortens, declines, or does nothing special in response to social pressure. Personality does not rewrite the authority model.

## Current contract

`BehavioralDispositionProfile` recognizes seven soft trigger fields: `intimacy_too_fast`, `accusation`, `contradiction`, `manipulation`, `boredom`, `disrespect`, and `emotional_overload`.

Each field may select one of the bounded mechanism values `challenge`, `deflect`, `go_quiet`, `shift_topic`, `shorten`, `decline`, or `none`. `none` does not mean unconditional compliance. It means that this trigger contributes no authored resistance mode, so the normal decision path can continue using relationship history, commitments, affect, memory, and other active constraints.

A missing `[behavior_profile]` section uses the previous Wayfarer behavior as its compatibility default. Existing cartridges therefore do not silently change merely because the new mechanism exists.

## Demonstration characters

The initial profiles are intentionally small and are based on already-authored differences rather than invented personality dimensions. Pretorius retains the prior guarded policy and withdraws from manipulation. Friendly remains engaged under accusation and deflects manipulation rather than treating every accusation as a challenge. Rival confronts manipulation, boredom, disrespect, accusation, and contradiction.

These are not claims that the current seven fields fully model personality. Their purpose is narrower: prove that one generic engine can produce different semantic conduct from character-owned state before the renderer chooses wording.

The principal regression uses the same manipulation input for all three characters. Pretorius resolves `withdraw`, Friendly resolves `deflect`, and Rival resolves `challenge`. A second comparison gives Friendly and Rival the same accusation. Friendly has no authored accusation resistance and remains in the ordinary response path, while Rival resolves `challenge`.

## What remains generic

Relationship appraisal equations are still shared. The same event currently applies the same base trust, attachment, tension, respect, guardedness, and unresolved-conflict update functions before later character-specific decision selection. Expression-envelope thresholds are also still generic.

Those shared equations are now an explicit open convergence question rather than an implicit assumption. They should not be parameterized by a large set of speculative personality constants. The next relationship work should begin with controlled cross-character counterexamples, then introduce only the smallest sensitivity or transformation contract required by those failures.

## Portability

The new top-level `[behavior_profile]` survives the current v1 to v2 normalization because migration begins from a deep copy of authored source. Runtime loading also returns the section explicitly. It has not yet been promoted into a standardized v2 phenotype namespace.

A later portability revision should decide whether this profile becomes part of `phenotype.behavioral_tendencies`, remains a Wayfarer extension, or is represented by a more general typed disposition schema. That decision should preserve existing data and should be driven by cross-runtime interoperability requirements rather than schema aesthetics.

## Design rule

Generic code should define mechanisms, bounds, precedence, and validation. Character data should determine which allowed mechanisms a particular subject tends to select. Lived experience may later change developmental state, but authored disposition is not rewritten from renderer prose.

The success criterion is not that every character has more parameters. It is that characters that are supposed to differ can make materially different decisions under the same stimulus, while the same character remains stable across renderer changes.
