# Persona Engine v12 Human UI

Persona Engine is a deterministic character-organism prototype with cartridge-driven identity and a local human-testing UI. The LLM is a renderer only: generated prose is speech evidence, not canonical truth. Character identity, body profile, world preferences, belief schema, voice constraints, and interpretation biases live in `.snp` cartridges. Mutable lived history lives in local session persistence.

## Core Doctrine

- The engine is character-agnostic.
- All character-specific content belongs in `.snp` cartridges.
- Session state stores lived history.
- The LLM is a renderer only.
- Renderer output is not canonical truth.
- World Authority owns objective facts.
- The character owns subjective interpretation.
- Interpretive belief objects are subjective readings, not objective truth.
- The UI displays organism state. It does not author organism state.
- Sensors report bounded observations only.
- Voice and avatar layers perform state only. They do not decide state.

## What Is Here

- Installable `persona_engine` package.
- Strict `.snp` cartridge validation.
- Deterministic pressure, relationship, body, world, memory, intention, habit, symbol, belief-ledger, interpretation, and replay/debug systems.
- World Authority for objective facts.
- Noncanonical, traceable interpretive belief objects.
- Mock-safe audio and vision observation plumbing.
- Voice-plan and avatar-safe state projection.
- FastAPI human-testing UI with cartridge selection, session reset, streamed chat, public status, current beliefs, proactive proposals, mock sensors, and optional read-only debug details.
- Scripted simulators for deterministic checks.

## Install

From the repository root:

```bash
python -m pip install -e .
```

For the full local developer/test setup:

```bash
python -m pip install -r requirements-dev.txt
```

Dependency files:

- `requirements.txt`: core runtime dependencies.
- `requirements-ui.txt`: optional UI server dependencies.
- `requirements-test.txt`: test dependencies, including FastAPI TestClient support.
- `requirements-dev.txt`: combined local development setup.

Ollama is optional. Tests and simulators pass through the mock renderer fallback and do not require Ollama, a network model, microphone, camera, TTS, avatar engine, GPU, or mobile runtime.

## Verify The Package

```bash
python -c "import persona_engine; print('ok')"
```

Expected output:

```text
ok
```

## Run Tests

```bash
python -m pytest persona_engine/tests -q
```

Current expected result:

```text
92 passed
```

## Run Simulators

```bash
python persona_engine/simulator.py --script persona_engine/simulator_scripts/pretorius_basic.yaml --cartridge persona_engine/cartridges/pretorius.snp
python persona_engine/simulator.py --script persona_engine/simulator_scripts/interpretation_basic.yaml --cartridge persona_engine/cartridges/pretorius.snp
python persona_engine/simulator.py --script persona_engine/simulator_scripts/organism_basic.yaml --cartridge persona_engine/cartridges/pretorius.snp
python persona_engine/simulator.py --script persona_engine/simulator_scripts/interpretation_anchored_misread.yaml --cartridge persona_engine/cartridges/pretorius.snp
```

After editable install, the simulator entry point is also available:

```bash
persona-engine-sim --script persona_engine/simulator_scripts/pretorius_basic.yaml --cartridge persona_engine/cartridges/pretorius.snp
```

## Run The Human UI

Install UI dependencies if you did not install `requirements-dev.txt`:

```bash
python -m pip install -r requirements-ui.txt
```

Run with Uvicorn:

```bash
python -m uvicorn "persona_engine.ui:create_app" --factory --reload
```

Or use the installed entry point:

```bash
persona-engine-ui
```

Open the local URL printed by Uvicorn. The UI supports cartridge selection, session reset, streamed chat, public organism status, avatar-safe state, voice-plan inspection, current interpretive beliefs, proactive proposals, mock audio observations, mock vision observations, and optional read-only debug details.

## Human Testing

Use one report per cartridge session:

- `persona_engine/docs/HUMAN_TESTING_PROTOCOL.md`
- `persona_engine/docs/HUMAN_TESTING_REPORT_TEMPLATE.md`

The report template captures continuity, boundedness, memory, resistance, time/consequence, grounded interpretation, fact leakage, verbatim excerpts, and failures to convert into simulator scripts or regression tests.

## Cartridges

Cartridges live in `persona_engine/cartridges/`. They are strict TOML `.snp` files. Character-specific identity, voice, body profile, world profile, interpretation bias, belief values, and belief rules belong there, not in engine modules.

Included cartridges:

- `neutral.snp`
- `pretorius.snp`
- `pretorius_v6.snp`
- `friendly.snp`
- `kiki.snp`
- `mentor.snp`
- `quiet.snp`
- `rival.snp`

## Renderer Backends

By default, the renderer falls back to bounded mock output if Ollama is not installed or reachable. This is intentional so tests, simulators, and UI smoke tests remain dependency-light.

Optional local Ollama experiment:

```bash
python -m pip install "ollama>=0.3.0"
```

Then configure cartridge `model_name` values to match locally available Ollama models. Renderer output still remains noncanonical speech evidence.

## Known Limitations

- No real microphone input is implemented.
- No real camera input is implemented.
- No real TTS output is implemented.
- No real avatar engine is implemented.
- GPU support is not required or tested.
- Mobile-native app support is not implemented.
- Autonomous background execution is limited to local engine idle hooks, not a full agent runtime.
- The human UI uses mock-safe sensor controls and state plans.
- Debug mode is local and read-only.

## More Docs

- `AGENTS.md`
- `persona_engine/docs/ARCHITECTURE_LOCK.md`
- `persona_engine/docs/LAZARUS_MAPPING.md`
- `persona_engine/docs/CURRENT_STATUS.md`
- `persona_engine/docs/HUMAN_TESTING_UI.md`
- `persona_engine/docs/HUMAN_TESTING_PROTOCOL.md`
- `persona_engine/docs/HUMAN_TESTING_REPORT_TEMPLATE.md`
- `persona_engine/docs/V9_INTERFACE_NOTES.md`
- `persona_engine/docs/V10_SENSORY_EMBODIMENT_NOTES.md`
- `persona_engine/docs/C99_PORTING_NOTES.md`
