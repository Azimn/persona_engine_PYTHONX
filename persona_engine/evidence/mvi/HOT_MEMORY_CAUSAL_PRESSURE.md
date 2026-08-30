# Hot-Memory Causal Pressure Probe

Probe: `hot-memory-causal-pressure-v2`.  
Production policy changed: `False`.  
Fixture valid: `True`.

| Budget | Hot | Unresolved | Reflection earned | Context target | Explicit cold recall | Trust act | Core pass |
| ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 1 | 1 | 1 | False | True | True | qualified_response | True |
| 2 | 2 | 2 | True | True | True | qualified_response | True |
| 3 | 3 | 2 | True | True | True | qualified_response | True |
| 4 | 4 | 2 | True | True | True | qualified_response | True |
| 8 | 7 | 2 | True | True | True | qualified_response | True |
| full | 7 | 2 | True | True | True | qualified_response | True |

Smallest tested finite budget preserving the currently demonstrated causal roles: `2`.
Full-resident retrieval interference demonstrated: `False`.
Ordinary contextual retrieval gap across every variant: `False`.
Explicit cold recall preserved across every variant: `True`.

The unconstrained resident store is not treated as a gold standard. The experiment asks which representation preserves demonstrated causal roles. It also separates active-memory interference from the independent gap in ordinary non-explicit contextual retrieval.
