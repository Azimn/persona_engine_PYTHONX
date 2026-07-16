# Long-Duration Memory Proof

Run the deterministic scenario with:

```bash
python persona_engine/simulator.py --script persona_engine/simulator_scripts/autobiographical_reconsolidation_weeks.yaml --cartridge persona_engine/cartridges/pretorius.snp
```

It proves this causal sequence without a model call being required for memory
change:

1. An objective shared-task failure has a missing-information cause.
2. The character encodes a mistaken first-person attribution with hurt.
3. Fourteen simulated days decay accessibility, not the original record.
4. Objective corrective evidence explicitly links to the earlier event.
5. Under strain, missed contradiction creates a deferred reconsideration.
6. Later calm and noticed conflict append interpretation version 2.
7. Version 1 remains inspectable and hurt remains after factual correction.
8. The current meaning can influence later retrieval and synthesis.

Direct tests also cover save/load, replay digest stability, private inspector
visibility, public-state privacy, renderer isolation, bounded versions, and a
C99 fixture round-trip.

This proof does not implement adaptive memory edges, procedural induction,
SocialMind, or identity growth. Its records are evidence those later slices
may consume.

## Development Measurement

Measured on July 16, 2026 with the bundled Codex Python runtime and one
two-version history:

| Probe | Result |
| --- | ---: |
| World events / experiences / memories | 2 / 1 / 1 |
| Interpretations / versions | 2 / 2 |
| Deferred records after acceptance | 0 |
| Serialized engine state | 15,691 bytes |
| C99 fixture | 2,861 bytes |
| Mean ordinary retrieval, 1,000 runs | 65.57 microseconds |
| Mean meaning activation, 10,000 runs | 5.02 microseconds |
| Current / historical activation | 0.471 / 0.124375 |
| Model calls for the memory transition | 0 |

These timings describe one development machine and are not hard acceptance
thresholds.

The automated playtest laboratory extends this proof to 14-, 21-, and 30-day
observable histories with actor-move replay and state-growth reports.
