# DUCK Future Build Status

Branch: `duck-future-build`
Rollback branch: `duck-organism`
Rollback commit: `f36e72f31a8127f7f779a8946e1777d8ad842bd4`

## Experiment rule

The future-build branch attempts direct integration toward the finished-product architecture. The rollback branch is not modified during the experiment. A future-build mechanism is not considered complete merely because a file exists. It must be wired to a production boundary or test and must preserve subject authority, canonical write rules, replayability, and failure isolation.

## Baseline already present before this experiment

The starting branch already includes the DUCK cognitive cycle, homeostatic drives, memory activation through the Wayfarer subject, global workspace competition, world/self simulation, action generation and selection, intention, execution policy, prediction error, learned world-model reliability, procedural learning, metacognition, canonical reducers, persistence/replay, proposal-only cognitive services, Ollama JSON services, model swap tests, and Wayfarer subject integration.

The broader repository already provides the mature Wayfarer identity/continuity substrate, relationship and belief systems, ContinuityClock, body state, sensorium, private cognition, proactive-event logic, dream machinery, renderer controls, and long-horizon evidence probes. Future DUCK work should reuse these rather than build competing copies.

## Added by the first future-build integration

- `duck/timebase.py`: explicit UTC observations plus Swatch Internet Time derived as `bmt_date` and `@beat`, while logical tick and subject elapsed time remain separate.
- `duck/embodiment_port.py`: replaceable body interface plus a world-model adapter that routes committed actions through the body while retaining independent internal simulation.
- `duck/endogenous.py`: bounded background-cognition trigger policy and proposal-only reflection specialist. Reflection cannot directly speak or write canonical state.
- `duck/capabilities.py`: declared action/tool capabilities and execution-policy derivation.
- `duck/future_runtime.py`: production-facing composition root around the existing DuckOrganism and Wayfarer subject.
- `tests/test_duck_future_runtime.py`: focused tests for Beat Time, clock regressions, body execution, sensor ingestion, capability policy, and endogenous cycles.
- `docs/DUCK_FUTURE_PRODUCT_SPEC.md`: finished-product target and promotion gates.

## Evidence state

No new mechanism is considered verified until branch CI reports green. The future product specification is a target, not an assertion that all production validation has already occurred.

After CI is green, the next direct-integration tranche should prioritize reuse of Wayfarer continuity/body/private-cognition components inside the future composition root, richer temporal expectation learning, crash-safe future-runtime persistence, body-swap tests, long-run resource probes, and real local-model end-to-end evaluation.
