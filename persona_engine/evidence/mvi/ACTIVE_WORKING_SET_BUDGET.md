# Active Working-Set Budget Probe

Probe: `active-working-set-budget-v1`  
Useful 100-turn longitudinal baseline: `True`

The full canonical biography remains persisted. This experiment temporarily reduces only the live working set used by the character before the final trust and disclosure prompts.

Baseline after 100 neutral turns: `106` live memories, `78,281` serialized bytes, trust conduct `qualified_response`, disclosure conduct `decline`.

Current-world compaction alone reduces world-authority facts from `101` to `1` while preserving server truth: `True` and visible context: `True`. Serialized state becomes `53,409` bytes.

| Memory policy | Budget | Kept | Unresolved kept | Total state | Memories | World authority | Trust conduct | Disclosure | Matches baseline |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| `recent` | 1 | 1 | 0 | 10,352 B | 343 B | 250 B | `respond` | `decline` | `False` |
| `recent` | 2 | 2 | 0 | 10,693 B | 684 B | 250 B | `respond` | `decline` | `False` |
| `recent` | 4 | 4 | 0 | 11,375 B | 1,367 B | 250 B | `respond` | `decline` | `False` |
| `recent` | 8 | 8 | 0 | 12,744 B | 2,735 B | 250 B | `respond` | `decline` | `False` |
| `recent` | 16 | 16 | 0 | 15,479 B | 5,470 B | 250 B | `respond` | `decline` | `False` |
| `recent` | 32 | 32 | 0 | 20,948 B | 10,939 B | 250 B | `respond` | `decline` | `False` |
| `salience` | 1 | 1 | 1 | 12,214 B | 2,206 B | 250 B | `qualified_response` | `decline` | `True` |
| `salience` | 2 | 2 | 2 | 14,418 B | 4,409 B | 250 B | `qualified_response` | `decline` | `True` |
| `salience` | 4 | 4 | 3 | 16,983 B | 6,975 B | 250 B | `qualified_response` | `decline` | `True` |
| `salience` | 8 | 8 | 3 | 18,350 B | 8,341 B | 250 B | `qualified_response` | `decline` | `True` |
| `salience` | 16 | 16 | 3 | 21,084 B | 11,076 B | 250 B | `qualified_response` | `decline` | `True` |
| `salience` | 32 | 32 | 3 | 26,556 B | 16,547 B | 250 B | `qualified_response` | `decline` | `True` |

Smallest salience-aware memory budget matching baseline: `1`  
Projected state at that budget: `12214` bytes  
Smallest recency-only budget matching baseline: `None`  
Projected state at that budget: `None` bytes

The salience policy is intentionally primitive: unresolved memories first, then identity/relationship relevance, emotional intensity and recency. It is not a new production memory architecture. The result is evidence about how much active history the existing behavior actually requires.
