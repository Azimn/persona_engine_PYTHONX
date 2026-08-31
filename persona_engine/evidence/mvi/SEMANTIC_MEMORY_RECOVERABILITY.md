# Semantic Memory Recoverability Probe

Probe: `semantic-memory-recoverability-v2`.  
Production policy changed: `False`.

| Projection | Semantic core | Experience | Conduct | Retrieval | Surface | Authority | Restart | Active conduct | Inactive conduct |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| production | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 4/4 | 2/2 |
| recoverable_cold_only | 2/6 | 2/6 | 2/6 | 6/6 | 6/6 | 6/6 | 6/6 | 0/4 | 2/2 |
| active_conflict_only | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 4/4 | 2/2 |
| recent_context_only | 2/6 | 2/6 | 2/6 | 6/6 | 6/6 | 6/6 | 6/6 | 0/4 | 2/2 |
| active_conflict_plus_recent | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 4/4 | 2/2 |

## Scenario matrix

| Scenario | Distractors | Projection | Hot USER_TOLD | Conduct | Old trace | Recent trace | Old surface | Recent surface | Negative | Provenance | Semantic | Experience |
| --- | --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| unresolved | unrelated | production | 6 | True | True | True | True | True | True | True | True | True |
| unresolved | unrelated | recoverable_cold_only | 0 | False | True | True | True | True | True | True | False | False |
| unresolved | unrelated | active_conflict_only | 2 | True | True | True | True | True | True | True | True | True |
| unresolved | unrelated | recent_context_only | 4 | False | True | True | True | True | True | True | False | False |
| unresolved | unrelated | active_conflict_plus_recent | 6 | True | True | True | True | True | True | True | True | True |
| unresolved | lexical | production | 6 | True | True | True | True | True | True | True | True | True |
| unresolved | lexical | recoverable_cold_only | 0 | False | True | True | True | True | True | True | False | False |
| unresolved | lexical | active_conflict_only | 2 | True | True | True | True | True | True | True | True | True |
| unresolved | lexical | recent_context_only | 4 | False | True | True | True | True | True | True | False | False |
| unresolved | lexical | active_conflict_plus_recent | 6 | True | True | True | True | True | True | True | True | True |
| repaired | mixed | production | 4 | True | True | True | True | True | True | True | True | True |
| repaired | mixed | recoverable_cold_only | 0 | True | True | True | True | True | True | True | True | True |
| repaired | mixed | active_conflict_only | 0 | True | True | True | True | True | True | True | True | True |
| repaired | mixed | recent_context_only | 4 | True | True | True | True | True | True | True | True | True |
| repaired | mixed | active_conflict_plus_recent | 4 | True | True | True | True | True | True | True | True | True |
| reopened | unrelated | production | 6 | True | True | True | True | True | True | True | True | True |
| reopened | unrelated | recoverable_cold_only | 0 | False | True | True | True | True | True | True | False | False |
| reopened | unrelated | active_conflict_only | 2 | True | True | True | True | True | True | True | True | True |
| reopened | unrelated | recent_context_only | 4 | False | True | True | True | True | True | True | False | False |
| reopened | unrelated | active_conflict_plus_recent | 6 | True | True | True | True | True | True | True | True | True |
| reopened | lexical | production | 6 | True | True | True | True | True | True | True | True | True |
| reopened | lexical | recoverable_cold_only | 0 | False | True | True | True | True | True | True | False | False |
| reopened | lexical | active_conflict_only | 2 | True | True | True | True | True | True | True | True | True |
| reopened | lexical | recent_context_only | 4 | False | True | True | True | True | True | True | False | False |
| reopened | lexical | active_conflict_plus_recent | 6 | True | True | True | True | True | True | True | True | True |
| neutral | lexical | production | 4 | True | True | True | True | True | True | True | True | True |
| neutral | lexical | recoverable_cold_only | 0 | True | True | True | True | True | True | True | True | True |
| neutral | lexical | active_conflict_only | 0 | True | True | True | True | True | True | True | True | True |
| neutral | lexical | recent_context_only | 4 | True | True | True | True | True | True | True | True | True |
| neutral | lexical | active_conflict_plus_recent | 4 | True | True | True | True | True | True | True | True | True |

## Surface diagnostics

- none

Resident causal evidence and recoverable autobiographical wording are separate contracts. Surface realization is measured independently from grounded retrieval.

No global resident-memory count is selected by this experiment.
