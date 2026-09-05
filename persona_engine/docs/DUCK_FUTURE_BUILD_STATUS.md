# DUCK Future Build Status

Branch: `duck-future-build`
Rollback branch: `duck-organism`
Rollback commit: `f36e72f31a8127f7f779a8946e1777d8ad842bd4`

## Experiment rule

The future-build branch attempts direct integration toward the finished-product architecture. The rollback branch is not modified during the experiment. A mechanism is not considered complete merely because a file exists. It must be wired to a production boundary or test and must preserve subject authority, canonical write rules, replayability, and failure isolation.

## Baseline already present before this experiment

The starting branch already included the DUCK cognitive cycle, homeostatic drives, memory activation through the Wayfarer subject, global workspace competition, world/self simulation, action generation and selection, intention, execution policy, prediction error, learned world-model reliability, procedural learning, metacognition, canonical reducers, persistence/replay, proposal-only cognitive services, Ollama JSON services, model-swap tests, and Wayfarer subject integration.

The broader repository supplies the mature Wayfarer identity/continuity substrate, relationship and belief systems, ContinuityClock, body state, sensorium, private cognition, proactive-event logic, dream machinery, renderer controls, and long-horizon evidence probes. Future DUCK work reuses these rather than building competing copies.

## Integrated future-build tranches

### Tranche 1: production-facing organism shell

Commit `c849a340c1da26c629ea382f09392f19d5cb3135` added the production-facing composition root, explicit UTC plus Beat Time, replaceable embodiment execution, bounded endogenous reflection, capability policy, focused tests, and the finished-product specification. CI `33979909723` passed on Python 3.11 and 3.12.

### Tranche 2: time, routine learning, restart, and body transfer

Commit `10c33e6a3616b266a81fd55e25a25597db4c06f2` separated cognitive ticks from elapsed subject time, added circular Beat-Time routine learning, persisted future-runtime operational state, made DUCK checkpoint writes atomic, and added live body transfer plus restart tests. CI `33980170651` passed on Python 3.11 and 3.12.

### Tranche 3: bidirectional embodiment and product probe

Commit `b12cbf29c44b7b1414847e4a06f1d6eecc72aebd` made embodiment cognitively bidirectional, added body-transfer events, optional-service failure isolation, and the deterministic multi-cycle future-product probe. CI `33980524552` passed on Python 3.11 and 3.12.

### Tranche 4: selected-intention language expression

Commit `b867a9e77d928e2627a62465fa1d2eaaa5503f63` completed the selected-intention expression loop. `ExpressionActionPreparer` runs only after DUCK selects and commits a `communicate` action. A renderer may realize that semantic intention but cannot change the selected action ID/type. Renderer realization metadata is excluded from the canonical action ledger. CI `33982247866` passed on Python 3.11 and 3.12, including renderer-swap canonical invariance and exact expression replay.

### Tranche 5: installable host, API, CLI, backup, and recovery

`FutureDuckHost` is the production composition root for one persistent individual. It pins the character cartridge, opens Wayfarer and DUCK persistence together, verifies subject identity on restart, owns the reference text body, exposes validated renderer switching, and provides message/observation/save/status operations without becoming a new canonical authority.

The local FastAPI surface and `persona-engine-duck` CLI expose controlled operation. `DuckBackupManager` creates checksum-verified portable archives with a SQLite-consistent Wayfarer backup and rejects traversal, corruption, subject mismatch, unmanifested payloads, and accidental overwrite.

The hardening sequence through commit `beff946c309aad92a6a025639d9c2d382cc046c4` added versioned runtime-state migration, future-schema refusal, adversarial action-preparer tests, policy-before-preparation checks, deterministic renderer-failure fallback, backup corruption detection, and bounded canonical ledgers. CI `33982847215` passed.

### Tranche 6: bounded expression history with durable replay

Commit `25d0600261e9629eb1d9ad7b3db542366e97e10e` converted `ExpressionJournal` from an unbounded operational dictionary into a bounded hot cache (256 entries by default). Older exact realizations remain durable in the append-only DUCK execution trace and can be recovered without re-calling the renderer. Legacy journal state migrates into the bounded representation. Runtime status exposes cache size/limit and archive availability.

CI `33987772528` passed on Python 3.11 and 3.12. The run included delivery, renderer-swap invariance, replay, host/API/backup tests, adversarial hardening tests, the full inherited suite, the focused DUCK suite, smoke test, and the 500-cycle future integration probe.

## Current release-candidate phase

The macroarchitecture is now treated as frozen for the production-candidate experiment. The next gate is not another cognitive box. It is the production lifecycle acceptance probe in `tools/run_duck_acceptance.py`, which exercises the actual `FutureDuckHost` through repeated conversation, checkpointing, backup/restore, process restart, bounded hot-state assertions, and historical expression recovery while enforcing a stable subject identity.

The criteria are formalized in `DUCK_PRODUCTION_CANDIDATE_GATE.md`.

## Evidence state

Code-completeness and longitudinal evidence are separate finish lines. After all hosted release-candidate gates are green, the remaining work is predominantly empirical and operational:

- run actual installed Ollama models on the target machine and perform renderer swaps;
- run longer production-boundary soak tests and record memory/disk growth;
- perform multi-day or multi-week continuity testing;
- conduct blind model-swap and character-recognition evaluation;
- run lesion/ablation studies against frozen baselines;
- test additional embodiment/environment transfers.

A green production-candidate build is sufficient for controlled research use. It is not by itself evidence of consciousness, sentience, or phenomenal experience, and it is not yet a public-production release claim.
