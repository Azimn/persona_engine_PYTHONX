# WorldAuthority Semantic Compaction Probe

All server/visible truth views preserved: `True`.  
Production policy changed: `False`.

| Scenario | Facts before | Facts after | Removed |
| --- | ---: | ---: | ---: |
| permanent_churn | 3 | 1 | 2 |
| temporary_override_fallback | 2 | 2 | 0 |
| nested_expiry | 3 | 3 | 0 |
| dominated_expiry | 3 | 2 | 1 |
| hidden_permanent_override | 2 | 2 | 0 |
| hidden_temporary_override | 2 | 2 | 0 |

Deterministic 2,000-fact mixed fixture: `2000` -> `53` active facts, removing `1947` (97.4%).

The probe preserves authoritative server and visible truth, including future expiry fallback. It does not claim historical recent_facts output is preserved; canonical continuity is the intended history authority and this compatibility seam must be reviewed before production integration.
