# Subject Clock Ownership Probe

Probe: `subject-clock-ownership-v1`

| Observation | Result |
| --- | ---: |
| Alice/Bob same subject UUID | `True` |
| Alice elapsed after explicit 8h | `28800.0` seconds |
| Alice elapsed after restart | `28800.0` seconds |
| Bob elapsed on same database | `28800.0` seconds |
| Latest canonical subject elapsed | `28800.0` seconds |
| Same-interlocutor restart preserved | `True` |
| Bob matches canonical subject time | `True` |
| Diagnosis | `subject_clock_is_shared_across_interlocutors` |

The minimum property under test is ownership, not psychology. `ContinuityClock` should remain one monotonic clock for one `subject_uuid`; changing the active relationship context must not create a second timeline. This probe does not infer sleep, loneliness, relationship cooling, or any other off-screen behavior from elapsed time.

No clock persistence rule is changed by this probe.
