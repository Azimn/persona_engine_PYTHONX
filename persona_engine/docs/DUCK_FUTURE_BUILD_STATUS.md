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

GitHub Actions DUCK CI run `33979909723` completed successfully on Python 3.11 and 3.12.

## Future-build tranche 2

Commit `10c33e6a3616b266a81fd55e25a25597db4c06f2` separated cognitive ticks from elapsed subject time, added circular Beat-Time routine learning, persisted future-runtime operational state, made DUCK checkpoint writes atomic, and added live body transfer plus restart tests.

GitHub Actions DUCK CI run `33980170651` completed successfully on Python 3.11 and 3.12.

## Future-build tranche 3

Commit `b12cbf29c44b7b1414847e4a06f1d6eecc72aebd` made embodiment cognitively bidirectional, added body-transfer events, optional-service failure isolation, and the deterministic multi-cycle future-product probe.

GitHub Actions DUCK CI run `33980524552` completed successfully on Python 3.11 and 3.12, including the future-product integration probe.

## Future-build tranche 4

The fourth integration closes the most important remaining architectural loop: selected cognition can now become language without handing the language model control of cognition.

`ExpressionActionPreparer` runs only after DUCK has selected and committed a `communicate` action. It may realize that semantic intention through a Wayfarer renderer, deterministic fallback, or another future expression provider, but it is forbidden from changing the selected action ID or action type. The renderer's output is therefore an execution-stage realization rather than a second planner.

`WayfarerExpressionPort` reuses the existing Wayfarer v2 expression trust boundary and output validator instead of creating a competing prompt architecture. `ExpressionJournal` records rendered output by stable speech ID so replay can reuse the actual utterance instead of silently asking a model to invent a new one.

`TextChannelEmbodimentPort` is the first complete reference body. It receives text as sensory input, exposes communication as an affordance, delivers the realized utterance as an effector action, emits a host-authoritative `SpeechDeliveryReceipt`, and lets the runtime feed that receipt back into the Wayfarer subject's lived history.

`FutureDuckRuntime.ingest_user_message()` now turns a message into a perceptual event plus an ordinary candidate communication action. A user message does not call a renderer directly. It must survive the same workspace, simulation, selection, policy, expression, embodiment, outcome, and learning path as every other action.

The focused tests verify that language follows selected intention, that delivery creates lived evidence, that changing expression models changes surface wording without changing DUCK canonical state, and that a recorded expression is reused without re-calling the renderer.

## Evidence state

Each tranche must return branch CI to green before it is treated as integrated. The future product specification remains a target. Code completeness and longitudinal evidence completeness are separate finish lines.

After tranche 4 is green, the remaining engineering work required for a production-candidate future version is concentrated at the host boundary: a stable local API, restart/backup/recovery tooling, a clean production composition builder, real local-model probe commands, migration/version checks, and longer adversarial/stability gates. The cognitive macroarchitecture itself is now represented by executable interfaces rather than architecture-only boxes.
