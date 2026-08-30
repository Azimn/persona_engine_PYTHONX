# Continuous Hot-Memory Probe

Probe: `continuous-hot-memory-v1`

| Hot budget | Passed | Restart hot count | Trust act | Cold old-fact recall | Commitment act | Identity act |
| ---: | :---: | ---: | --- | :---: | --- | --- |
| 1 | True | 1 | qualified_response | True | decline | protect_boundary |
| 2 | True | 2 | qualified_response | True | decline | protect_boundary |
| 4 | True | 4 | qualified_response | True | decline | protect_boundary |
| 8 | False | 6 | respond | True | decline | protect_boundary |

Smallest passing experimental budget: `1`.

A passing budget is not a production recommendation. The experiment asks only whether the already-demonstrated causal behaviors survive when the compact working set exists throughout the history instead of being imposed afterward.
