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

Commit `10c33e6a3616b266a81fd55e25a25597db4c06f2` separated cognitive ticks from elapsed subject time, added circular Beat-Time routine learning, persisted future-runtime operational state, made DUCK checkpoint writes atomic, and added live body transfer plus restart tests.

The tranche adds `TimedSubjectProxy`, so internal cognition can occur without manufacturing elapsed time while explicit civil-time observations advance Wayfarer's existing subject clock by the observed duration. `TemporalPatternBank` can learn recurring timing patterns across the `@000` boundary and convert deviations into explicit temporal evidence.

## Future-build tranche 3

The third integration makes embodiment cognitively bidirectional rather than merely an execution sink. `EmbodimentCognitiveService` projects body state and affordances into the same noncanonical candidate field as drives, memories, prediction errors, and optional model hypotheses. Body affordances can therefore influence ordinary workspace competition and action proposal without bypassing the action selector.

Body transfer now emits a high-self-relevance `body_transfer` event so the organism can cognitively process a changed body rather than the host silently replacing hardware underneath it. Built-in cognitive services are de-duplicated when provider sets are swapped.

The focused suite adds optional-service failure isolation. A broken proposal service must appear in `service_errors` while the cycle, subject identity, and canonical state transition remain valid.

`tools/run_duck_future_probe.py` adds a deterministic multi-cycle production integration probe with explicit Beat time, learned temporal routines, persistence/restart, live body transfer, action execution, subject continuity, and service-error assertions. Future-branch CI now runs that probe in addition to the inherited suite and standard DUCK smoke test.

## Evidence state

Each tranche must return branch CI to green before the next is treated as integrated. The future product specification remains a target. Code completeness and longitudinal evidence completeness are separate finish lines.

After tranche 3 is green, remaining high-value work is no longer missing macroarchitecture. It is integration depth and validation: connect more mature Wayfarer body/private-cognition/relationship/dream state through adapters, exercise a real local model in the complete future runtime, harden external tool sandboxes, add migration/backup/restore drills, and run long-horizon plus human continuity studies.
