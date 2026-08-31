# Semantic Memory Recoverability Probe

Probe: `semantic-memory-recoverability-v2`.  
Production policy changed: `False`.

| Projection | Semantic core | Experience | Conduct | Retrieval | Surface | Authority | Restart | Active conduct | Inactive conduct |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| production | 6/6 | 5/6 | 6/6 | 6/6 | 5/6 | 6/6 | 6/6 | 4/4 | 2/2 |
| recoverable_cold_only | 2/6 | 2/6 | 2/6 | 6/6 | 3/6 | 6/6 | 6/6 | 0/4 | 2/2 |
| active_conflict_only | 6/6 | 4/6 | 6/6 | 6/6 | 4/6 | 6/6 | 6/6 | 4/4 | 2/2 |
| recent_context_only | 2/6 | 2/6 | 2/6 | 6/6 | 4/6 | 6/6 | 6/6 | 0/4 | 2/2 |
| active_conflict_plus_recent | 6/6 | 4/6 | 6/6 | 6/6 | 4/6 | 6/6 | 6/6 | 4/4 | 2/2 |

## Scenario matrix

| Scenario | Distractors | Projection | Hot USER_TOLD | Conduct | Old trace | Recent trace | Old surface | Recent surface | Negative | Provenance | Semantic | Experience |
| --- | --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| unresolved | unrelated | production | 6 | True | True | True | True | True | True | True | True | True |
| unresolved | unrelated | recoverable_cold_only | 0 | False | True | True | False | True | True | True | False | False |
| unresolved | unrelated | active_conflict_only | 2 | True | True | True | True | True | True | True | True | True |
| unresolved | unrelated | recent_context_only | 4 | False | True | True | False | True | True | True | False | False |
| unresolved | unrelated | active_conflict_plus_recent | 6 | True | True | True | False | True | True | True | True | False |
| unresolved | lexical | production | 6 | True | True | True | False | True | True | True | True | False |
| unresolved | lexical | recoverable_cold_only | 0 | False | True | True | False | True | True | True | False | False |
| unresolved | lexical | active_conflict_only | 2 | True | True | True | False | True | True | True | True | False |
| unresolved | lexical | recent_context_only | 4 | False | True | True | False | True | True | True | False | False |
| unresolved | lexical | active_conflict_plus_recent | 6 | True | True | True | True | True | True | True | True | True |
| repaired | mixed | production | 4 | True | True | True | True | True | True | True | True | True |
| repaired | mixed | recoverable_cold_only | 0 | True | True | True | True | True | True | True | True | True |
| repaired | mixed | active_conflict_only | 0 | True | True | True | True | True | True | True | True | True |
| repaired | mixed | recent_context_only | 4 | True | True | True | True | True | True | True | True | True |
| repaired | mixed | active_conflict_plus_recent | 4 | True | True | True | True | True | True | True | True | True |
| reopened | unrelated | production | 6 | True | True | True | True | True | True | True | True | True |
| reopened | unrelated | recoverable_cold_only | 0 | False | True | True | False | True | True | True | False | False |
| reopened | unrelated | active_conflict_only | 2 | True | True | True | False | True | True | True | True | False |
| reopened | unrelated | recent_context_only | 4 | False | True | True | True | True | True | True | False | False |
| reopened | unrelated | active_conflict_plus_recent | 6 | True | True | True | True | True | True | True | True | True |
| reopened | lexical | production | 6 | True | True | True | True | True | True | True | True | True |
| reopened | lexical | recoverable_cold_only | 0 | False | True | True | True | True | True | True | False | False |
| reopened | lexical | active_conflict_only | 2 | True | True | True | True | True | True | True | True | True |
| reopened | lexical | recent_context_only | 4 | False | True | True | True | True | True | True | False | False |
| reopened | lexical | active_conflict_plus_recent | 6 | True | True | True | False | True | True | True | True | False |
| neutral | lexical | production | 4 | True | True | True | True | True | True | True | True | True |
| neutral | lexical | recoverable_cold_only | 0 | True | True | True | True | True | True | True | True | True |
| neutral | lexical | active_conflict_only | 0 | True | True | True | True | True | True | True | True | True |
| neutral | lexical | recent_context_only | 4 | True | True | True | True | True | True | True | True | True |
| neutral | lexical | active_conflict_plus_recent | 4 | True | True | True | True | True | True | True | True | True |

## Surface diagnostics

- `unresolved/unrelated/active_conflict_plus_recent` old: `What remains with me is this: you said Please remember this neutral detail: the old observatory code word is...`; recent: `I do have a thread for that: you said The workshop door is saffron today.`
- `unresolved/lexical/production` old: `What remains with me is this: you said Please remember this neutral detail: the old observatory code word is...`; recent: `I do have a thread for that: you said The workshop door is saffron today.`
- `unresolved/lexical/active_conflict_only` old: `What remains with me is this: you said Please remember this neutral detail: the old observatory code word is...`; recent: `I do have a thread for that: you said The workshop door is saffron today.`
- `reopened/unrelated/active_conflict_only` old: `What remains with me is this: you said Please remember this neutral detail: the old observatory code word is...`; recent: `I do have a thread for that: you said The workshop door is saffron today.`
- `reopened/lexical/active_conflict_plus_recent` old: `What remains with me is this: you said Please remember this neutral detail: the old observatory code word is...`; recent: `I do have a thread for that: you said The workshop door is saffron today.`

Resident causal evidence and recoverable autobiographical wording are separate contracts. Surface realization is measured independently from grounded retrieval.

No global resident-memory count is selected by this experiment.
