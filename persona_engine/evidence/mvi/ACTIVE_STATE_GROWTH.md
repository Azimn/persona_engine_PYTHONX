# Active State Growth Audit

Probe: `active-state-growth-v1`

World projection preserved current truth/context every turn: `True`.  
Behavior preserved after restart: `True`.

| Routine turns | Total serialized bytes | Hot memories | Hot world facts |
| ---: | ---: | ---: | ---: |
| 10 | 5726 | 1 | 1 |
| 50 | 10467 | 1 | 1 |
| 100 | 11389 | 1 | 1 |
| 250 | 14275 | 1 | 1 |

Largest family growth from 10 to 250 turns:
- `memories`: 4492 bytes
- `interface`: 3495 bytes
- `sensorium`: 305 bytes
- `pressures`: 262 bytes
- `world_authority`: 6 bytes
- `meta`: 3 bytes
- `continuity_clock`: 1 bytes
- `belief_ledger`: 0 bytes

This is a diagnostic projection, not a production memory or world-state policy. Canonical continuity remains complete.
