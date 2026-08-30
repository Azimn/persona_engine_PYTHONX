# Canonical Root Projection Probe

Passed: `True`.  
Production policy changed: `False`.  
Semantic replay equal: `True`.  
Cold biography retained: `True`.  
Submitted host context preserved: `True`.

| Representation | Events | Event bytes | Payload bytes |
| --- | ---: | ---: | ---: |
| Current canonical | 21 | 29,685 | 18,794 |
| Root-only projection | 9 | 7,934 | 3,245 |

Event-byte reduction: `21,751 B` (`73.27%`).  
Payload-byte reduction: `15,549 B` (`82.73%`).

Current event types: `{'commitment_adopted': 1, 'input': 6, 'sensor_observation': 1, 'sensorium': 6, 'state_transition': 6, 'time_advance': 1}`.  
Projected event types: `{'commitment_adopted': 1, 'input': 6, 'sensor_observation': 1, 'time_advance': 1}`.

This is an experimental projection, not a new ledger schema. Passing means current replay, cold biography, host-context replay, commitment continuity, subject time, and bounded sensory roots do not require routine derived state_transition/sensorium rows or derived metadata embedded in input roots for this mixed scenario.
