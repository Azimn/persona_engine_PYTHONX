# Earned Trait Ownership Probe

Probe: `subject-earned-trait-ownership-v1`

| Observation | Result |
| --- | --- |
| Alice/Bob same subject UUID | `True` |
| Alice learned trait | `{'name': 'deliberate_caution', 'strength': 0.05, 'source_memory_ids': ['trait-ownership-probe-evidence']}` |
| Alice restart preserved trait | `True` |
| Bob on same subject preserved trait | `False` |
| Bob trait state | `None` |
| Diagnosis | `earned_character_development_partitioned_by_interlocutor` |

The property under test is narrow. `IdentityLedger.earned_traits` represents slow, evidence-backed development of the continuing character. If it survives an Alice restart but disappears merely because Bob becomes the active interlocutor, the failure is state ownership rather than trait learning or persistence.

This probe does not generalize ownership rules for memories, pressures, body, world, symbols, or relationship beliefs.
