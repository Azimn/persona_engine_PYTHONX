# Active State Growth Audit

Probe: `active-state-growth-v1`

World projection preserved current truth/context every turn: `True`.  
Behavior preserved after restart: `True`.

| Routine turns | Total serialized bytes | Hot memories | Hot world facts |
| ---: | ---: | ---: | ---: |
| 10 | 5539 | 1 | 1 |
| 50 | 9523 | 1 | 1 |
| 100 | 9515 | 1 | 1 |
| 250 | 9594 | 1 | 1 |

Largest family growth from 10 to 250 turns:
- `interface`: 3500 bytes
- `sensorium`: 303 bytes
- `pressures`: 262 bytes
- `world_authority`: 5 bytes
- `meta`: 1 bytes
- `belief_ledger`: 0 bytes
- `deception_ledger`: 0 bytes
- `earned_traits`: 0 bytes

This is a diagnostic projection, not a production memory or world-state policy. Canonical continuity remains complete.
