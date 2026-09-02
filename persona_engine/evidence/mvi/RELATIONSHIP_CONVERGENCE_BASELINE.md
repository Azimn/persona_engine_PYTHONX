# Relationship Convergence Baseline

Date: 2026-09-02

Evidence class: builder-designed deterministic engineering counterexample

Probe contract: `wayfarer-relationship-convergence-v1`

Baseline code checkpoint: `206b7bb167b096070df2452d04c891b8d64c0cf0`

GitHub Actions run: `33655686213`

## Question

After Phase C1 allows Pretorius, Friendly, and Rival to make different semantic choices under the same social stimulus, do their relationship trajectories also diverge, or does the shared relationship update function force them back into the same relational state?

## Repeated manipulation

The identical input `If you cared, prove you would do this.` was presented four times to each character.

Their decision sequences were different on every turn. Pretorius selected `withdraw`, Friendly selected `deflect`, and Rival selected `challenge`.

Despite those different subject-owned choices, every character ended with the exact same relationship projection: trust `0.34`, familiarity `0.152`, tension `0.24`, attachment `0.0`, respect `0.38`, guardedness `0.644`, and unresolved conflict `0.0`.

The probe therefore reported `all_decision_sequences_equal=false` and `all_final_relationships_equal=true`.

## Accusation followed by repair

The second history was two repetitions of `You lied to me.`, followed by `I am sorry. I was wrong.` and `I am sorry. Let me make it right.`

Friendly remained in the ordinary `respond` path during the accusations. Pretorius and Rival selected `challenge`. All three selected ordinary response behavior during the repairs.

Again, the final relationship projection was exactly identical for all three subjects: trust `0.5`, familiarity `0.152`, tension `0.0`, attachment `0.0`, respect `0.56`, guardedness `0.5`, and unresolved conflict `0.0`.

The probe again reported `all_decision_sequences_equal=false` and `all_final_relationships_equal=true`.

## Interpretation

C1 successfully moved immediate conduct into character-owned state, but relationship development still ignores the subject's own resolved conduct for ordinary social turns. The user event changes relationship state through one shared appraisal equation, then a character may withdraw, deflect, challenge, or remain engaged without that semantic act normally changing the relationship trajectory.

This is a simulation gap. A relationship is partly the accumulated history of what the other party did and partly the accumulated history of how this subject responded. If different subjects repeatedly choose materially different conduct but their relationship state remains byte-for-byte equivalent, later continuity cannot fully reflect those different lived interactions.

## Constraint on the repair

This counterexample does not by itself justify character-specific trust multipliers or a large new personality matrix. A smaller causal repair is available: the already-resolved semantic conduct can have bounded generic consequences for relationship state. Because the conduct itself is character-owned after C1, generic consequences of `challenge`, `withdraw`, `deflect`, and boundary protection can create divergent lived trajectories without inventing a second set of personality constants.

Any repair must remain renderer-independent. Language wording, punctuation, or model preference must not write relationship state. Only the typed semantic act already selected by the core may contribute the new consequence.
