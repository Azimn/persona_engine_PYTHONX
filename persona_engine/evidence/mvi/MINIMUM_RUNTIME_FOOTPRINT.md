# Minimum Runtime Footprint Probe

Probe: `minimum-runtime-footprint-v1`  
Renderer/network LLM required: `False`  
Python: `3.11.16`

This is a reproducible **Python reference footprint**, not a C99 minimum-hardware claim. Python interpreter, allocator, imported libraries and SQLite contribute overhead that the eventual low-level runtime does not need to preserve.

| Snapshot | Serialized character state | SQLite files | Memory units | Canonical events | Process RSS |
| --- | ---: | ---: | ---: | ---: | ---: |
| `fresh` | 1,706 B | 69,632 B | 0 | 0 | 29.133 MiB |
| `representative_plus_10` | 15,045 B | 245,760 B | 15 | 38 | 29.840 MiB |
| `representative_plus_100` | 78,287 B | 1,568,768 B | 106 | 308 | 32.789 MiB |
| `after_second_interlocutor` | 3,879 B | 1,568,768 B | 2 | 314 | 35.625 MiB |

Cartridge: `4,985` bytes  
Python package source: `589,634` bytes  
Observed process-RSS delta across the probe: `7.359 MiB`  
Initialization time on this CI runner: `0.0259` seconds  
Representative scenario time: `4.8570` seconds

## State-family size at final snapshot

| Family | Compact JSON bytes |
| --- | ---: |
| `memories` | 715 B |
| `interface` | 711 B |
| `world_authority` | 543 B |
| `belief_ledger` | 448 B |
| `intentions` | 244 B |
| `body` | 228 B |
| `world` | 210 B |
| `relationship` | 148 B |
| `continuity_clock` | 129 B |
| `earned_traits` | 121 B |
| `meta` | 109 B |
| `pressures` | 2 B |
| `open_loops` | 2 B |
| `symbols` | 2 B |
| `habits` | 2 B |
| `relationship_beliefs` | 2 B |
| `sensorium` | 2 B |
| `deception_ledger` | 2 B |

The state-family and database measurements are the important part for minimum-substrate work. They tell us how much actual character information exists independently of the language model and Python runtime. Future reduction experiments should compare against this same probe rather than treating total Python RSS as the character's intrinsic memory requirement.
