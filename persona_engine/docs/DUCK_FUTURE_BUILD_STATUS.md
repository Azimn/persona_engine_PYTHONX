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

The selected-intention expression loop is now integrated and green at commit `b867a9e77d928e2627a62465fa1d2eaaa5503f63`. GitHub Actions run `33982247866` passed on Python 3.11 and 3.12, including focused gates for delivery, renderer-swap canonical invariance, recorded-expression replay, the full inherited suite, DUCK smoke test, and future-product integration probe.

`ExpressionActionPreparer` runs only after DUCK has selected and committed a `communicate` action. It may realize that semantic intention through a Wayfarer renderer, deterministic fallback, or another future expression provider, but it is forbidden from changing the selected action ID or action type. Renderer realization metadata is deliberately excluded from the DUCK canonical action ledger and retained in trace/runtime evidence instead.

`WayfarerExpressionPort` reuses the existing Wayfarer v2 expression trust boundary and output validator. `ExpressionJournal` records rendered output by stable speech ID so exact replay can reuse the actual utterance without silently asking a model to invent a replacement.

`TextChannelEmbodimentPort` is the first complete reference body. It receives text, exposes communication as an affordance, delivers the realized utterance as an effector action, emits a host-authoritative `SpeechDeliveryReceipt`, and lets the runtime feed the receipt back into the Wayfarer subject's lived history.

## Future-build tranche 5

The fifth integration turns the future architecture into an installable local product boundary rather than a library-only research assembly.

`FutureDuckHost` is the production composition root for one persistent individual. It pins a cartridge into the subject directory, opens Wayfarer and DUCK persistence together, verifies subject identity on restart, owns the reference text body, exposes validated renderer switching, and provides message/observation/save/status operations without becoming a new canonical authority.

`duck/api.py` adds a localhost-oriented FastAPI surface for health, messages, observations, stepping, saving, renderer discovery/configuration, and public status. Private trace/debug endpoints are disabled unless debug mode is explicitly enabled.

`persona-engine-duck` adds terminal `chat`, one-shot `send`, `status`, `renderers`, `serve`, `backup`, and `restore` commands. Server binding is loopback-only unless the operator explicitly supplies `--allow-remote`.

`DuckBackupManager` creates a portable checksum-verified archive containing the pinned cartridge, host metadata, a SQLite-consistent Wayfarer backup, and DUCK runtime/checkpoint state. Restore rejects path traversal, checksum mismatches, unmanifested files, subject mismatches, and accidental overwrite of a nonempty destination.

`tools/run_duck_local_model_probe.py` is an optional real-Ollama end-to-end probe. Hosted CI does not pretend to validate a local model it cannot access. The tool verifies persistent subject and organism identity while swapping one or two installed Ollama models.

The tranche's focused tests cover host restart continuity, local API routing and debug isolation, checksum-verified backup/restore, and overwrite refusal.

## Evidence state

Each tranche must return branch CI to green before it is treated as integrated. The future product specification remains a target. Code completeness and longitudinal evidence completeness are separate finish lines.

After tranche 5 is green, the remaining future-build work is production hardening and evidence rather than missing macroarchitecture: runtime schema migration tests, longer resource/stability probes, adversarial capability/preparer tests, backup corruption drills, real local-model execution on the target machine, and longitudinal/human continuity studies.
