# Persona Engine Human Testing UI

This build adds a local web console for human testing. The UI is deliberately thin. It renders public organism state and sends user text or bounded sensor observations through the normal engine channels. It does not directly write private state.

## Run the UI

Install optional UI dependencies:

```bash
python -m pip install -r requirements-ui.txt
```

Start the app from the repository root:

```bash
python -m uvicorn "persona_engine.ui:create_app" --factory --reload
```

Or use the installed entry point after `python -m pip install -e .`:

```bash
persona-engine-ui
```

Open the local URL printed by Uvicorn.

## What testers can do

Testers can select any cartridge in `persona_engine/cartridges`, reset that character's local session, chat through the normal input channel, simulate a few bounded audio and vision observations, inspect public organism status, see avatar-safe state, see voice-plan output, and see interpretive beliefs exposed for the current turn. The Renderer Lab discovers locally installed Ollama models and applies provider, model, thinking mode, timeout, and token-budget settings to the active cartridge session.

Renderer configuration is scoped by cartridge. Switching characters restores that cartridge's own renderer settings instead of carrying the previous character's selection across. Offline rendering is always available. When an Ollama turn fails, the runtime falls back to offline expression and exposes the reason without changing organism state.

The Renderer Lab shows conservative model-family capability hints and recommends thinking mode, timeout, and token budget. Nonthinking model profiles disable the thinking selector; thinking-capable profiles retain `auto`, `on`, and `off` for comparison. Session headers identify new, resumed, and freshly reset sessions.

The UI does not receive raw private pressure values in normal mode. Normal
status is served from `/api/status` and contains only categorical public status,
the active cartridge, tester id, and avatar-safe projection. Debug mode can be
enabled for developer inspection by passing `debug=True` to `create_app`; the
frontend toggle is still off by default.

Read-only debug workspace summaries include retrieved-memory IDs, source type, tags, timestamp, and first-person content. This provenance is not exposed by normal public status.

With debug mode enabled, the life inspector also shows current activity, intention, attention, objective world events, linked subjective experiences, retrieval reasons, bounded vitality events, and capability artifacts. It is a projection of engine state and has no mutation controls.

The private inspector also groups append-only autobiographical meaning by
experience, including current and historical versions, evidence links,
deferred reconsiderations, activation reasons, and conservative use outcomes.
Normal public status exposes none of this private history.

The report workspace can export the current transcript and report draft with canonical replay events and diagnostic turn records. Import validates the bundle and cartridge checksums, creates a separate replay database, and replays only approved engine/world/session inputs. The original session database is not overwritten. Replay verifies deterministic state, not exact generated prose. Bundles may include private debug or submitted context and should be handled as sensitive local test artifacts.

API endpoints:

- `GET /` serves the human testing UI.
- `GET /api/cartridges` lists `.snp` cartridges and the active cartridge.
- `GET /api/renderers` discovers offline, Ollama, and future local-HF providers and reports the current runtime.
- `POST /api/renderer/config` validates and applies renderer settings to the active cartridge session.
- `POST /api/session/select` switches cartridge through session construction.
- `POST /api/session/reset` resets the current local session database.
- `POST /api/session/export` creates a versioned, checksum-verified JSON session bundle.
- `POST /api/session/replay` validates a bundle and replays approved events in an isolated session.
- `GET /api/status` returns public categorical status only.
- `GET /api/proactive` returns read-only proactive proposals.
- `POST /api/chat` sends text through the engine.
- `POST /api/chat/stream` streams the already-computed response.
- `POST /api/sensor/audio` accepts bounded mock audio observations.
- `POST /api/sensor/vision` accepts bounded mock vision observations.

## Interface invariant

The interface displays organism state. It does not author organism state.

Allowed UI actions:

- Submit user text through `agent.say`.
- Submit bounded audio observations through `observe_audio`.
- Submit bounded vision observations through `observe_vision`.
- Select a cartridge, which creates a new engine instance.
- Reset a local session database for testing.
- Configure the surface renderer through the session's validated renderer channel.
- Export and replay validated session bundles through the session service.

Forbidden UI actions:

- Directly mutate body, world, pressure, relationship, memory, symbol, belief, identity, or habit state.
- Invent second thoughts.
- Interpret raw private floats into emotion labels.
- Promote generated speech into canonical truth.

## Mobile readiness

The frontend is responsive and dependency-light. Sensor buttons are mock events for now. A mobile host can later replace those buttons with platform adapters that emit the same bounded observation payloads.

The deterministic core still requires no microphone, camera, TTS, avatar engine, network, GPU, or Ollama to run tests.
