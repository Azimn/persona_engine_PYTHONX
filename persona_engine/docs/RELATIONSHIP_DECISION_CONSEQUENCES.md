# Relationship Decision Consequences

## Purpose

Wayfarer distinguishes between what happens to a subject and what the subject chooses to do about it.

The normal appraisal path models the effect of incoming social evidence on relationship state. Phase C2 adds a second, much smaller path for the consequences of the subject's own already-resolved semantic conduct.

This distinction exists to prevent different characters from selecting different actions while nevertheless being forced through identical future relationship trajectories.

## Design rule

Character-specific variation remains outside the generic relationship mechanism whenever possible.

The cartridge-owned behavioral disposition profile determines which bounded semantic act the subject selects for a soft social trigger. The relationship layer does not know whether it is operating on Pretorius, Friendly, Rival, or another character. It only knows the semantic act that was resolved.

The current generic effect table is intentionally tiny:

```python
DECISION_RELATIONSHIP_EFFECTS = {
    "challenge": {"tension": 0.02},
    "withdraw": {"guardedness": 0.02},
    "protect_boundary": {"tension": 0.02},
}
```

Do not expand this table because another effect seems psychologically plausible. Add an effect only when a controlled scenario demonstrates a behaviorally meaningful missing consequence.

## Two causal paths

Incoming event appraisal remains the primary relationship update. Kindness, accusation, manipulation, threat, repair, intimacy, and related evidence modify shared relationship dimensions through the existing bounded equations.

After the semantic decision is resolved, `apply_decision_relationship_effect()` applies any currently supported consequence of the subject's own act. This is deliberately downstream of decision selection and independent of renderer wording.

The resulting turn therefore has a simple causal structure:

```text
user/world event
    -> appraisal
    -> relationship response to event
    -> semantic character decision
    -> bounded relationship consequence of that decision
    -> language realization
```

The model renderer cannot create, remove, or change the decision-owned relationship effect by choosing different prose.

## Decision effect trace

`InteriorEngine.receive_input()` returns and persists `decision_effects`:

```json
{
  "dialogue_act": "withdraw",
  "relationship": {"guardedness": 0.02},
  "pressure_relief": 0.0
}
```

This is a diagnostic causal certificate. It is not a second decision and is not renderer authority.

## Why this is not a personality model

The table encodes generic semantics of a small action vocabulary, not character traits. `challenge` sustaining some tension and `withdraw` sustaining some guardedness are consequences of acts. The character-specific question, whether this subject challenges, withdraws, deflects, or responds, is resolved elsewhere from cartridge-owned and lived state.

This keeps the mechanism compatible with the project's low-resource goal. Different apparent psychologies can emerge from combinations of a small action vocabulary, authored disposition data, shared appraisal, memory, commitments, and accumulated relationship state rather than requiring a large matrix of personality constants.

## Current boundary

C2 does not individualize the base appraisal equations. The current evidence did not require that complexity. It also does not claim that the three present effects are exhaustive.

If a future controlled test shows that two subjects with appropriately different authored state still converge because the same event must have intrinsically different salience or appraisal strength for them, that would justify testing a compact character-owned sensitivity representation. Until then, do not add one.

## Evidence

The frozen failure is `evidence/mvi/RELATIONSHIP_CONVERGENCE_BASELINE.md`.

The verified repair is `evidence/mvi/RELATIONSHIP_DECISION_CONSEQUENCES.md`.
