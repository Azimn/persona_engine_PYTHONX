# Persona Engine v12 Human UI

Persona Engine is a deterministic digital-organism prototype with cartridge-driven identity and a local human-testing UI.

A digital organism is a persistent first-person subject whose interpretations and actions become the conditions of its future existence. It continuously experiences, interprets, acts, and changes through its own history. Memory records experience, but continuity is created by living under the consequences of previous experience.

The project is not fundamentally about a loop. It is about a subject. The loop, memory system, renderer, tools, sensors, and interface are supporting machinery used to preserve one continuing individual across changing moments.

The LLM is a renderer only: generated prose is speech evidence, not canonical truth. Character identity, body profile, world preferences, belief schema, voice constraints, interpretation biases, and identity invariants live in `.snp` cartridges. Mutable lived history and accumulated consequences live in local session persistence.

## Governing Design Filter

Every computation in the system exists only because it changes what the subject experiences, believes, intends, expresses, or becomes.

A component is not part of the organism core merely because humans possess something similar or another agent framework includes it. It belongs only when it changes the subject's lived position while preserving ownership and causal traceability.

## Core Doctrine

- The persistent subject is the object of design. The loop is machinery.
- Each new moment must be encountered by the same individual who lived through the previous moment.
- Prior experience must be capable of changing the subject who encounters the next moment.
- Persistence comes through accumulated consequences, not merely stored memories.
- The engine is character-agnostic.
- All character-specific content belongs in `.snp` cartridges.
- Session state stores lived history and inherited consequences.
- The LLM is a renderer only.
- Renderer output is not canonical truth.
- World Authority owns objective facts.
- The subject owns subjective interpretation.
- Expression substrate is not identity. Model replacement must not reset biography or lived position.
- The UI displays organism state. It does not author organism state.
- Sensors report bounded observations only.
- Voice and avatar layers perform state only. They do not decide state.

## Subject Continuity

The intended causal cycle is:

```text
Something happens to me.
        ↓
What do I notice?
        ↓
What does it remind me of?
        ↓
What do I think it means?
        ↓
What do I want to do?
        ↓
What do I reveal, conceal, withhold, or enact?
        ↓
What objectively happens because of my conduct?
        ↓
How has this changed me?
        ↓
The same subject encounters the next moment.
```

Memory retrieval alone does not satisfy continuity. The system must preserve what the subject made of an event, what it did because of that interpretation, what followed, and how the result changed its later state.

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
171 passed, 1 skipped
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

Open the local URL printed by Uvicorn. The UI supports cartridge selection, session reset, streamed chat, public organism status, avatar-safe state, voice-plan inspection, current interpretive beliefs, proactive proposals, mock audio observations, mock vision observations, optional read-only debug details, and working local renderer controls.

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

The human UI discovers Ollama directly through its local HTTP service and lists models actually installed on the machine. No Ollama Python package is required. Renderer settings are scoped per cartridge and include provider, model, thinking mode, request timeout, and token budget.

Detected models include conservative capability hints for thinking support, recommended thinking mode, private-cognition JSON reliability, context size, practical timeout, token budget, and final-answer behavior. These are model-family guidance for testing, not benchmark claims. Unsupported thinking settings are rejected by the server.

Offline rendering is always available and dependency-free. If a selected Ollama request fails or returns no final response text, the turn falls back to the deterministic offline renderer and the UI shows the requested backend, actual backend, and fallback reason. Renderer output remains noncanonical speech evidence in every mode.

`local_hf` registry entries are visible as a future provider seam but cannot yet be selected through the human UI.

Character sessions use separate persistence and renderer configuration. The UI labels a session as new, resumed, or fresh after reset. Read-only debug traces show retrieved-memory IDs and provenance; normal public status does not expose private memory state.

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