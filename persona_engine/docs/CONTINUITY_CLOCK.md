# Project Wayfarer ContinuityClock Contract

## Purpose

M4 gives the portable individual one monotonic elapsed timeline. The clock records
how much time has passed for the subject. It does not decide what that duration
means emotionally, socially, or autobiographically.

## Two quantities must not be confused

**Subject elapsed time** is authoritative continuity state. An eight-hour absence
advances the clock by eight hours even on weak hardware and even if the process
was shut down for the whole interval.

**Dynamics integration time** is the amount of an existing subsystem's old update
rule that Wayfarer is currently willing to execute. Pre-M4 body and pressure
coefficients were tuned as short simulation ticks, not validated as real-hour
physiology or affect. M4 therefore retains a clearly labeled 1,000-second
compatibility budget for those legacy dynamics while preserving the full elapsed
duration in the clock.

This is deliberate. Numerical coefficients do not gain scientific meaning merely
because a real clock was added.

## Authority

Wall-clock observation and explicit host time advancement may create canonical
`time_advance` root events. Language-model output cannot advance subject time.
A backwards system-clock jump records a correction and advances subject time by
zero. Subject time never runs backwards.

## Replay

`time_advance` is an exogenous canonical replay root. Replay applies the recorded
elapsed duration through the same public time-advance interface before replaying
later experiences. Derived body, pressure, memory, and other consequences are not
replayed as independent causes.

## Timestep is not time

The historical `engine.timestep` remains a deterministic processing/work index for
compatibility. It is no longer an elapsed-time measurement. M3 schema 1.0's
`subject_time` column still uses that legacy processing index; the authoritative
M4 elapsed timeline is `ContinuityClock.subject_elapsed_seconds` and the canonical
`time_advance` payload. A future ledger-schema migration may normalize those two
representations, but M4 does not rewrite historical evidence.

## What M4 deliberately does not add

The clock does not add loneliness, attachment decay, routines, sleep, calendar
psychology, relationship cooling, or off-screen narrative. Those mechanisms must
be justified separately by longitudinal behavior that Wayfarer cannot otherwise
produce or preserve.
