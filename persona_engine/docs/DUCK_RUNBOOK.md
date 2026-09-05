# DUCK Future Runtime Runbook

Status: production-candidate operating instructions for `duck-future-build`.

## Install

From a checkout of the repository:

```bash
python -m pip install -e '.[ui]'
```

Python 3.11 and 3.12 are the continuously tested runtime versions.

## Create or reopen one persistent subject

The easiest path uses the bundled neutral cartridge on first creation and pins a copy into the host state directory:

```bash
persona-engine-duck status --root ./duck_state
```

To seed a new host from another cartridge:

```bash
persona-engine-duck status --root ./duck_state --cartridge ./persona_engine/cartridges/pretorius_v6.snp
```

After creation, the pinned cartridge in `duck_state/config/cartridge.snp` is authoritative for that host. Reopening with a conflicting cartridge is rejected rather than silently changing the individual.

## Terminal conversation

Deterministic offline renderer:

```bash
persona-engine-duck chat --root ./duck_state
```

Local Ollama renderer:

```bash
persona-engine-duck chat --root ./duck_state --provider ollama --model qwen3:8b
```

List detected backends/models:

```bash
persona-engine-duck renderers --root ./duck_state
```

## Local API

```bash
persona-engine-duck serve --root ./duck_state --bind 127.0.0.1 --port 8765
```

The runtime refuses non-loopback binds unless `--allow-remote` is supplied explicitly. That flag is an operator acknowledgement, not authentication. A remotely exposed deployment should be placed behind an authenticated transport boundary.

Primary endpoints:

- `GET /health`
- `GET /v1/status`
- `POST /v1/messages`
- `POST /v1/observe`
- `POST /v1/step`
- `POST /v1/save`
- `GET /v1/renderers`
- `PUT /v1/renderer`

Trace and full debug status endpoints return 403 unless debug mode is explicitly enabled.

## Persistence tiers

DUCK keeps bounded state in its hot checkpoints and keeps durable historical evidence in append-only traces. Rendered speech is held in a bounded expression hot cache (256 entries by default). When an exact old utterance has left that cache, replay looks it up in the durable DUCK execution trace instead of asking the current renderer to regenerate the wording.

This distinction is intentional: a character may accumulate history for months or years without forcing every historical utterance into `future_runtime.json`.

## Action feasibility

The current embodiment constrains the action set before DUCK simulates and commits an intention. A text-channel body, for example, cannot commit to a physical `inspect` action merely because an exploration drive proposed it. If no proposed action is executable by the current body, the organism can select `wait`. The executor then performs the same capability check again before execution.

This keeps cognition autonomous without letting it confuse a desired action with an available effector.

## Backup

Save and create a portable archive:

```bash
persona-engine-duck backup --root ./duck_state ./duck-backup.zip
```

The archive contains host metadata, the pinned cartridge, a SQLite-consistent Wayfarer backup, DUCK state, traces, and future-runtime operational state. Payload files are SHA-256 listed in the backup manifest.

Restore to an empty location:

```bash
persona-engine-duck restore ./duck-backup.zip --root ./restored_duck
```

Restoring over a nonempty destination requires the explicit `--overwrite` flag. Stop any running DUCK host before restore.

## Deterministic probes

Cognitive/embodiment integration probe:

```bash
python tools/run_duck_future_probe.py --cycles 500
```

Production-boundary lifecycle probe using the actual local host, offline renderer, restart, backup/restore, bounded-state checks, and durable expression recovery:

```bash
python tools/run_duck_acceptance.py --cycles 360
```

The lifecycle probe respects autonomous action selection. It does not require DUCK to answer every input with speech; it requires the selected action to be feasible and successfully executed. Speech delivery is checked when `communicate` is selected.

A focused expression-cache eviction test is:

```bash
python tools/run_duck_acceptance.py --cycles 24 --expression-cache-limit 8 --require-expression-eviction
```

Real local-model probe, not faked in hosted CI:

```bash
python tools/run_duck_local_model_probe.py --model-a qwen3:8b --model-b gemma3
```

Use model names that actually appear in `ollama list` or `persona-engine-duck renderers`.

## Recovery discipline

Do not manually edit `wayfarer.sqlite3`, `duck/organism.json`, `duck/events.jsonl`, or `duck/future_runtime.json` on a live subject. Restore from a verified backup or use an explicit migration. DUCK rejects a checkpoint whose state digest does not match, a host whose pinned-cartridge checksum changes unexpectedly, a backup whose payload hashes fail, and future-runtime schemas newer than the installed code understands.

The `duck-organism` branch at commit `f36e72f31a8127f7f779a8946e1777d8ad842bd4` remains the pre-future-build rollback line for the experiment.

See `DUCK_PRODUCTION_CANDIDATE_GATE.md` for the architecture-freeze criteria and the remaining target-machine/research gates.
