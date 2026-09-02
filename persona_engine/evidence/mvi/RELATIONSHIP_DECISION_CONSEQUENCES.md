# Relationship Decision Consequences

Status: verified Phase C2 engineering evidence

Date: 2026-09-02

Branch under test: `wayfarer-relationship-dispositions-phase`

Verified code checkpoint: `1cbac350fdff4b2ef85e5b82e499786a5b6450d1`

## Question

After Phase C1 moved soft social response selection into character-owned cartridge state, do different semantic choices actually produce different lived relationship trajectories, or does the generic relationship update erase those differences?

## Frozen negative baseline

The pre-repair result is preserved separately in `RELATIONSHIP_CONVERGENCE_BASELINE.md` and must not be rewritten.

Under identical four-turn manipulation histories, Pretorius repeatedly selected `withdraw`, Friendly selected `deflect`, and Rival selected `challenge`, yet all three ended with the same relationship projection:

```text
trust=0.34
familiarity=0.152
tension=0.24
attachment=0.0
respect=0.38
guardedness=0.644
unresolved_conflict=0.0
```

Under two accusations followed by two repairs, the characters again selected different acts but all three returned to the same final relationship projection:

```text
trust=0.5
familiarity=0.152
tension=0.0
attachment=0.0
respect=0.56
guardedness=0.5
unresolved_conflict=0.0
```

This demonstrated a causal convergence problem. Character-owned conduct existed, but the subject's own conduct had almost no typed relationship consequence.

## Minimum repair

The repair does not add per-character relationship equations, OCEAN/Big Five traits, or a general personality-vector system.

The generic relationship layer now recognizes only three currently demonstrated semantic act consequences:

```python
DECISION_RELATIONSHIP_EFFECTS = {
    "challenge": {"tension": 0.02},
    "withdraw": {"guardedness": 0.02},
    "protect_boundary": {"tension": 0.02},
}
```

`respond`, `deflect`, and `decline` currently add no decision-owned relationship delta. Earlier speculative effects for `decline` and extra `protect_boundary` guardedness were intentionally removed because the experiment did not justify them.

The character-specific source of variation remains the already-authored C1 behavioral disposition profile. The generic mechanism only applies the causal semantics of the act that the subject actually selected.

## Causal trace

Each turn now exposes and persists a typed `decision_effects` record after semantic decision resolution and before final persistence:

```json
{
  "dialogue_act": "challenge",
  "relationship": {"tension": 0.02},
  "pressure_relief": 0.0
}
```

Renderer wording is not an input to this state transition. A regression test uses two different renderer phrasings for the same Rival accusation turn and verifies identical semantic decision, identical decision effects, and identical substantive relationship state.

## Repaired manipulation trajectory

After four identical manipulation turns:

```text
Friendly
trust=0.34
tension=0.24
guardedness=0.644
act sequence=deflect, deflect, deflect, deflect

Pretorius
trust=0.34
tension=0.24
guardedness=0.724
act sequence=withdraw, withdraw, withdraw, withdraw

Rival
trust=0.34
tension=0.32
guardedness=0.644
act sequence=challenge, challenge, challenge, challenge
```

The shared user appraisal still produces the same trust/respect/familiarity effects where appropriate. The subject's own semantic conduct now leaves an additional bounded causal trace rather than being erased by that shared appraisal.

## Repaired accusation and repair trajectory

After two identical accusations followed by two identical repair attempts:

```text
Friendly final tension=0.0
Pretorius final tension=0.04
Rival final tension=0.04
```

All three end with `unresolved_conflict=0.0`. Repair therefore still closes the conflict episode, while the history of having challenged the accusations leaves a small residual tension rather than disappearing completely.

## Verification

GitHub Actions run `33658855260` executed the full deterministic suite and the permanent relationship convergence probe on both supported Python versions.

Python 3.11:

```text
371 passed, 1 skipped, 1 warning in 32.84s
relationship convergence probe: passed
```

Python 3.12:

```text
371 passed, 1 skipped, 1 warning in 32.55s
relationship convergence probe: passed
```

The warning is the existing Starlette/httpx TestClient deprecation and is unrelated to this change.

## Claims supported

This evidence supports the narrow claim that character-owned semantic conduct can now contribute to later relationship state through a small renderer-independent causal mechanism. It also supports the claim that the demonstrated relationship convergence failure can be repaired without introducing character-specific relationship equations.

It does not establish that the current relationship model is psychologically complete, empirically human-like, or sufficient for every future character. It does not justify adding more decision effects without new failures.

## Development consequence

Phase C2 closes the currently demonstrated relationship-convergence defect. The next Phase C question is Priority 6: whether authored values and moral boundaries can affect semantic decisions through an equally small typed mechanism while remaining separate from host safety and capability policy.
