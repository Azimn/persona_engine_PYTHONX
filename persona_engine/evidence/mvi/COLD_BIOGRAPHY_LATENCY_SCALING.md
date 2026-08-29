# Cold Biography Latency Scaling

Probe: `cold-biography-latency-scaling-v1`

| Canonical inputs | DB bytes | First lookup ms | Median repeat ms | Transient peak bytes | Target found |
| ---: | ---: | ---: | ---: | ---: | :---: |
| 100 | 135168 | 2.022 | 1.765 | 23911 | True |
| 1000 | 614400 | 12.800 | 12.579 | 23911 | True |
| 5000 | 2838528 | 61.852 | 61.512 | 23911 | True |
| 10000 | 5623808 | 120.926 | 122.244 | 23911 | True |

The reader streams canonical input history and retains only the fixed-size candidate heap. Archive growth should therefore primarily appear as lookup latency rather than a proportional resident-memory requirement.

No index is justified by this probe alone. An index should be added only if measured latency crosses a practical interaction budget on target-like hardware.
