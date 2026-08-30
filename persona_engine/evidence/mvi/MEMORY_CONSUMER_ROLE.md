# Memory Consumer Role Probe

Production policy changed: `False`.  
Smallest role projection preserving current causal + retrieval-trace continuity: `causal2_recent1`.  
Visible mundane continuity missing in every variant: `True`.  
Post-repair reflection bug detected: `True`.

| Variant | Hot | Reflection | Trust | Workshop trace | Workshop visible | Lighthouse visible | Core |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| full | 25 | False | qualified_response | False | False | True | False |
| causal2_only | 8 | True | qualified_response | False | False | True | True |
| causal2_recent1 | 9 | True | qualified_response | True | False | True | True |
| causal3_recent1 | 9 | True | qualified_response | True | False | True | True |
| causal3_recent2 | 10 | True | qualified_response | True | False | True | True |

## Repair reflection check

Conflict before repair: `0.2`  
Conflict after repair: `0.0`  
Historical unresolved memories retained: `2`  
False post-repair reflection trait: `True`.

Hot autobiography should protect current consumer roles rather than a raw item count. This probe also treats visible mundane continuity and post-repair fixation as experience-level gates, not merely internal-state concerns.
