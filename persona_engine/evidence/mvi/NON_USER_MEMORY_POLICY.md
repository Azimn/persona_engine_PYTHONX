# Non-USER_TOLD Memory Policy Adversarial Probe

Probe: `non-user-memory-policy-v1`.  
Production policy: `semantic-residency-v1`.  
All expected outcomes: `True`.

| Variant | Obs experience | Reflection experience | Conduct | Provenance | Autobiography | Authority | Full production contract |
| --- | --- | --- | --- | --- | --- | --- | --- |
| production | True | True | True | True | True | True | True |
| evict_observed | False | True | True | True | True | True | False |
| evict_reflection | True | False | True | True | True | True | False |
| evict_active_user_told | True | True | False | False | True | True | False |
| evict_observed_and_reflection | False | False | True | True | True | True | False |

## Earned conclusions

OBSERVED and REFLECTION remain resident because their first-person experiences are not safely reconstructable. Current unresolved USER_TOLD evidence remains resident because conduct and reflection consume its causal metadata. Inactive USER_TOLD wording remains reconstructable through canonical cold biography. No global resident count is implied.

The negative projections are semantic ablations, not proposed production settings. A family is not evictable merely because downstream state survives. Its first-person experience must also be reconstructable for the consumers that can ask for or retrieve it.
