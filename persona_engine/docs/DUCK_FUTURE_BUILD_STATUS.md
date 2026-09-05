# DUCK Future Build Status

Branch: `duck-future-build`
Rollback branch: `duck-organism`
Rollback commit: `f36e72f31a8127f7f779a8946e1777d8ad842bd4`

## Experiment rule

The future-build branch attempts direct integration toward the finished-product architecture. The rollback branch is not modified during the experiment. A future-build mechanism is not considered complete merely because a file exists. It must be wired to a production boundary or test and must preserve subject authority, canonical write rules, replayability, and failure isolation.

## Baseline already present before this experiment

The starting branch already includes the DUCK cognitive cycle, homeostatic drives, memory activation through the Wayfarer subject, global workspace competition, world/self simulation, action generation and selection, intention, execution policy, prediction error, learned world-model reliability, procedural learning, metacognition, canonical reducers, persistence/replay, proposal-only cognitive services, Ollama JSON services, model swap tests, and Wayfarer subject integration.

The broader repository already provides the mature Wayfarer identity/continuity substrate, relationship and belief systems, ContinuityClock, body state, sensorium, private cognition, proactive-event logic, dream machinery, renderer controls, and long-horizon evidence probes. Future DUCK work should reuse these rather than build competing copies.

## Future-build tranche 1

Commit `c849a340c1da26c629ea382f09392f19d5cb3135` added the production-facing composition root, explicit UTC plus Beat Time, replaceable embodiment execution, bounded endogenous reflection, capability policy, focused tests, and the finished-product specification.

GitHub Actions DUCK CI run `33979909723` completed successfully on Python 3.11 and 3.12. The workflow ran the full inherited deterministic suite, the focused DUCK suite, and the DUCK smoke entry point. This establishes regression compatibility for tranche 1, not full production validation.

## Future-build tranche 2

The second integration closes several production gaps exposed by the first pass:

- cognitive cycles no longer have to imply one second of lived time in the future runtime. `TimedSubjectProxy` supplies explicit elapsed duration to Wayfarer's existing subject clock, while internal reflection can consume zero civil duration.
- Beat Time now accompanies elapsed-between-observation metadata and remains independent of logical ticks.
- `TemporalPatternBank` learns recurring event timing using circular Beat Time statistics, including patterns around `@000`, and can mark deviations as prediction evidence.
- future-runtime operational state is persisted atomically alongside DUCK state so temporal anchors, learned timing patterns, endogenous cooldowns, event counters, and body history survive restart.
- DUCK checkpoints now use atomic replace plus fsync, and trace appends are flushed before return.
- live `swap_embodiment()` can attach a different body to the same subject while preserving learned world-model state and routing later executions through the new body.
- tests now cover temporal duration, background-time behavior, learned timing, body transfer, and future-runtime restart.

## Evidence state

Each tranche must return branch CI to green before the next is treated as integrated. The future product specification remains a target. Code completeness and longitudinal evidence completeness are separate finish lines.

The next high-value integration should connect more of the mature Wayfarer private-cognition, body/sensorium, relationship, dream, and temporal-continuity components through explicit adapters rather than recreating them. It should also add long-run future-runtime probes, service/model failure tests, body-loss recovery, and local-model end-to-end evaluation.
