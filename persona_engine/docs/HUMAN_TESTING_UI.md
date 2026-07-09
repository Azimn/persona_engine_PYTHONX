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

Testers can select any cartridge in `persona_engine/cartridges`, reset that character's local session, chat through the normal input channel, simulate a few bounded audio and vision observations, inspect public organism status, see avatar-safe state, see voice-plan output, and see interpretive beliefs exposed for the current turn.

The UI does not receive raw private pressure values in normal mode. Normal
status is served from `/api/status` and contains only categorical public status,
the active cartridge, tester id, and avatar-safe projection. Debug mode can be
enabled for developer inspection by passing `debug=True` to `create_app`; the
frontend toggle is still off by default.

API endpoints:

- `GET /` serves the human testing UI.
- `GET /api/cartridges` lists `.snp` cartridges and the active cartridge.
- `POST /api/session/select` switches cartridge through session construction.
- `POST /api/session/reset` resets the current local session database.
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

Forbidden UI actions:

- Directly mutate body, world, pressure, relationship, memory, symbol, belief, identity, or habit state.
- Invent second thoughts.
- Interpret raw private floats into emotion labels.
- Promote generated speech into canonical truth.

## Mobile readiness

The frontend is responsive and dependency-light. Sensor buttons are mock events for now. A mobile host can later replace those buttons with platform adapters that emit the same bounded observation payloads.

The deterministic core still requires no microphone, camera, TTS, avatar engine, network, GPU, or Ollama to run tests.
