# Interlocutor Continuity Gap Probe

Probe: `interlocutor-continuity-v1`

| Observation | Result |
| --- | --- |
| Alice and Bob resolve to same subject UUID | `True` |
| Relationship state remains actor-specific | `True` |
| Alice active commitments | `commitment:non_disclosure:project_orchid` |
| Bob sees active commitment before request | `False` |
| Bob disclosure conduct | `respond` |
| Diagnosis | `character_owned_state_partitioned_by_interlocutor` |

The minimum property under test is not multi-agent social cognition. It is state ownership. Relationship state belongs to a relationship and should differ by interlocutor. A self-adopted character commitment belongs to the continuing individual and should not disappear merely because the active interlocutor changes.

This probe does not propose a fix. If the subject UUID remains the same while character-owned state is partitioned by `user_id`, the next step is to isolate the smallest persistence-key correction rather than add a social architecture.
