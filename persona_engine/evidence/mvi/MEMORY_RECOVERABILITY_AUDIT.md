# Memory Recoverability Audit

Production policy changed: `False`.  
Blanket eviction safe: `False`.  
Runtime memory families: `observed, reflection, user_told`.  
Unsafe to blanket-evict active families: `observed, reflection`.

| Family | Content | Causal metadata | First-person experience | Cold reader | Current eviction rule |
| --- | --- | --- | --- | --- | --- |
| user_told | True | False | True | True | only when no current consumer requires original causal metadata |
| observed | False | False | False | False | pin until a typed autobiographical reconstruction path is demonstrated |
| reflection | False | False | False | False | pin until reflection experience is either canonically represented or proven behaviorally redundant |
| inferred | False | False | False | False | unused; fail closed if introduced without an archive contract |
| core_identity | True | True | False | False | unused as autobiographical memory; identity remains owned by cartridge/ledger |

## Runtime inventory

Memory counts by source: `{'observed': 1, 'reflection': 1, 'user_told': 28}`.  
Canonical event counts: `{'input': 28, 'sensorium': 28, 'state_transition': 28}`.

Cold storage is not one property. User-statement wording is recoverable today, but current cold candidates do not recreate the original causal metadata needed by unresolved-history consumers. Observed and reflection memories do not yet have a direct first-person cold reconstruction path. A production hot-set policy must therefore evict by recoverability and current role, never by age or count alone.

The critical distinction is: content recoverability does not imply causal recoverability. An old user statement may be safe to page for expression after its relationship conflict is repaired, while the same statement must remain hot while its unresolved-at-the-time metadata still participates in conduct or reflection.
