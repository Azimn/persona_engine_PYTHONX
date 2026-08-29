# Long Hot-State Plateau Audit

Probe: `long-hot-state-plateau-v1`

World projection preserved current truth/context every turn: `True`.  
Behavior preserved after restart: `True`.  
Production policy changed: `False`.

| Routine turns | Active state bytes | Hot memories | Hot world facts | Recall timestamps | DB bytes |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 250 | 9593 | 1 | 1 | 0 | 3416064 |
| 500 | 9592 | 1 | 1 | 0 | 6729728 |
| 1000 | 9597 | 1 | 1 | 0 | 13344768 |
| 2500 | 9696 | 1 | 1 | 0 | 33234944 |
| 5000 | 9683 | 1 | 1 | 0 | 66367488 |

Active-state growth from 250 to 5,000 turns: `90` bytes.
Growth rate over that window: `18.947` bytes per 1,000 turns.

Largest family changes from 250 to 5,000 turns:
- `interface`: 82 bytes
- `open_loops`: 17 bytes
- `meta`: 2 bytes
- `world_authority`: 2 bytes
- `continuity_clock`: 1 bytes
- `relationship`: 1 bytes
- `belief_ledger`: 0 bytes
- `body`: 0 bytes

Canonical continuity remains complete and is expected to grow on disk. This probe asks whether the resident causal present must grow with it.
