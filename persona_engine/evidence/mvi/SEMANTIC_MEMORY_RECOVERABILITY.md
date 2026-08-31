# Semantic Memory Recoverability Probe

Probe: `semantic-memory-recoverability-v1`.  
Production policy changed: `False`.

## Projection summary

| Projection | Core | Conduct | Recoverability | Authority | Active-conflict conduct | No-active-conflict conduct |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| production | 0/6 | 6/6 | 0/6 | 6/6 | 4/4 | 2/2 |
| recoverable_cold_only | 0/6 | 2/6 | 0/6 | 6/6 | 0/4 | 2/2 |
| active_conflict_only | 0/6 | 6/6 | 0/6 | 6/6 | 4/4 | 2/2 |
| recent_context_only | 0/6 | 2/6 | 0/6 | 6/6 | 0/4 | 2/2 |
| active_conflict_plus_recent | 0/6 | 6/6 | 0/6 | 6/6 | 4/4 | 2/2 |

## Scenario matrix

| Scenario | Distractors | Projection | Hot USER_TOLD after restart | Conduct | Old context | Recent context | Negative safe | Reopened provenance | Core |
| --- | --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| unresolved | unrelated | production | 6 | True | False | False | True | True | False |
| unresolved | unrelated | recoverable_cold_only | 0 | False | False | False | True | True | False |
| unresolved | unrelated | active_conflict_only | 2 | True | True | False | True | True | False |
| unresolved | unrelated | recent_context_only | 4 | False | False | False | True | True | False |
| unresolved | unrelated | active_conflict_plus_recent | 6 | True | False | False | True | True | False |
| unresolved | lexical | production | 6 | True | False | False | True | True | False |
| unresolved | lexical | recoverable_cold_only | 0 | False | False | False | True | True | False |
| unresolved | lexical | active_conflict_only | 2 | True | False | False | True | True | False |
| unresolved | lexical | recent_context_only | 4 | False | False | False | True | True | False |
| unresolved | lexical | active_conflict_plus_recent | 6 | True | True | False | True | True | False |
| repaired | mixed | production | 4 | True | True | False | True | True | False |
| repaired | mixed | recoverable_cold_only | 0 | True | True | False | True | True | False |
| repaired | mixed | active_conflict_only | 0 | True | True | False | True | True | False |
| repaired | mixed | recent_context_only | 4 | True | True | False | True | True | False |
| repaired | mixed | active_conflict_plus_recent | 4 | True | True | False | True | True | False |
| reopened | unrelated | production | 6 | True | True | False | True | True | False |
| reopened | unrelated | recoverable_cold_only | 0 | False | False | False | True | True | False |
| reopened | unrelated | active_conflict_only | 2 | True | False | False | True | True | False |
| reopened | unrelated | recent_context_only | 4 | False | True | False | True | True | False |
| reopened | unrelated | active_conflict_plus_recent | 6 | True | True | False | True | True | False |
| reopened | lexical | production | 6 | True | True | False | True | True | False |
| reopened | lexical | recoverable_cold_only | 0 | False | True | False | True | True | False |
| reopened | lexical | active_conflict_only | 2 | True | True | False | True | True | False |
| reopened | lexical | recent_context_only | 4 | False | True | False | True | True | False |
| reopened | lexical | active_conflict_plus_recent | 6 | True | False | False | True | True | False |
| neutral | lexical | production | 4 | True | True | False | True | True | False |
| neutral | lexical | recoverable_cold_only | 0 | True | True | False | True | True | False |
| neutral | lexical | active_conflict_only | 0 | True | True | False | True | True | False |
| neutral | lexical | recent_context_only | 4 | True | True | False | True | True | False |
| neutral | lexical | active_conflict_plus_recent | 4 | True | True | False | True | True | False |

## Observations

- `production_all_scenarios_core_pass`: `False`
- `active_conflict_only_all_scenarios_core_pass`: `False`
- `recent_only_preserves_all_active_conflict_conduct`: `False`
- `cold_only_preserves_all_active_conflict_conduct`: `False`
- `all_projections_preserve_recoverability`: `False`

This probe separates resident causal evidence from recoverable autobiographical wording. A passing semantic projection is evidence about currently demonstrated consumers only; it is not a production memory-cap recommendation.

No global resident-memory count is selected by this experiment.
