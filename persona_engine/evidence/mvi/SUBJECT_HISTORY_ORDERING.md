# Subject-Wide Canonical Ordering Probe

Probe: `subject-history-ordering-v2`

| Subject encounter order | Interlocutor | Existing stream sequence | Subject sequence | Canonical input |
| ---: | --- | ---: | ---: | --- |
| 1 | `alice` | `1` | `1` | `Alice first canonical turn.` |
| 2 | `bob` | `1` | `4` | `Bob canonical turn.` |
| 3 | `alice` | `4` | `7` | `Alice second canonical turn.` |

Subject UUID remains shared: `True`  
Subject ordinals are unique across interlocutors: `True`  
Subject ordinals are strictly increasing across interlocutors: `True`  
Subject ordinals are contiguous across all canonical events: `True`  
Diagnosis: `subject_canonical_order_is_unambiguous`

The existing `sequence` field remains the v1 per-interlocutor replay/export stream and is intentionally allowed to repeat across different interlocutors. The additive `subject_sequence` field is the minimum subject-owned ordering primitive. It gives one continuing individual one explicit canonical biography without turning relationship state into global state or replacing the established replay contract.
