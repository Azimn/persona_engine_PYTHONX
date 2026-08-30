# Production Resident-State Plateau Probe

Passed: `True`.  
Experimental projection helpers used: `False`.  
Active growth, turn 250 to 5000: `205 B`.  
Database growth, turn 250 to 5000: `7,438,336 B`.

| Turn | Active bytes | DB bytes | Memories | USER_TOLD | Unresolved USER_TOLD | World facts | Canonical inputs |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 250 | 12,553 | 1,142,784 | 7 | 6 | 2 | 1 | 253 |
| 500 | 12,602 | 1,531,904 | 7 | 6 | 2 | 1 | 503 |
| 1000 | 12,605 | 2,293,760 | 7 | 6 | 2 | 1 | 1003 |
| 2500 | 12,688 | 4,628,480 | 7 | 6 | 2 | 1 | 2503 |
| 5000 | 12,758 | 8,581,120 | 7 | 6 | 2 | 1 | 5003 |

## Restart behavior

Same subject UUID: `True`  
Trust/cooperation act: `qualified_response`  
History evidence active: `True`  
Old lighthouse visible from cold biography: `True`  
Non-disclosure act: `decline`  
Identity rewrite act: `protect_boundary`.

## Repair boundary

USER_TOLD before repair: `6`  
USER_TOLD after repair: `4`  
Conflict returned to zero: `True`  
Stale unresolved-tension loops: `0`.

This is the first long-horizon resident-state measurement using the production memory and WorldAuthority policies without experimental projection helpers. Database growth represents the retained biography; active state growth identifies any still-resident family that scales with life length.
