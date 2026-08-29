# Subject-Wide Canonical Ordering Probe

Probe: `subject-history-ordering-v1`

| Subject order by recorded wall time | Interlocutor | Stored sequence | Canonical input |
| ---: | --- | ---: | --- |
| 1 | `alice` | `1` | `Alice first canonical turn.` |
| 2 | `bob` | `1` | `Bob canonical turn.` |
| 3 | `alice` | `4` | `Alice second canonical turn.` |

Subject UUID remains shared: `True`  
Sequence values are unique subject-wide: `False`  
Sequence values are strictly increasing subject-wide: `False`  
Sequence values are contiguous subject-wide: `False`  
Diagnosis: `canonical_sequence_partitioned_by_interlocutor`

This probe distinguishes an ordering property from the interlocutor-ownership property. Relationship views may remain actor-specific, but a single individual's canonical biography should not require `(user_id, sequence)` to determine which of two events was "sequence 1." Wall time is retained as evidence, but it is not a substitute for an explicit canonical order when the architecture claims a monotonic event sequence.

No sequence schema is changed by this probe.
