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
- Append-only objective world events, per-character subjective experience traces, bounded memory lifecycle, and explained hybrid retrieval.
- Persisted current activity and interruption context plus a separate seeded vitality channel for bounded whim, limitation, and rare chaos events.
- Derived integration capacity and bounded field width, with inspectable situated synthesis and action-completion records.
- One canonical typed action per situated turn, selected from synthesis rather than by intrinsic motivation or the renderer.
- Deterministic fallible self-monitoring that can miss conflict, overestimate capacity, conceal uncertainty, delay, clarify, correct, withdraw, or double down through synthesis-selected regulation.
- Non-destructive autobiographical reconsolidation preserves original experience while versioning later evidence-backed meaning, including bounded deferral when contradiction is missed under strain.
- Developmental Life v1 adds explicit evidence routing, bounded memory connections, procedural skills, relationship expectations, dyadic rituals, slow cartridge-authorized trait evidence, and observable-only automated playtesting.
- Bounded `uint32` actor identities keep relationship histories and actor-tagged memories separate across users, NPCs, genesis figures, and duplicate names without pretending ambiguous aliases are certain identity.
- Genesis years produce realistic historical age while sparse chapter summaries represent long periods without fabricating a lifetime of daily memories.
- Portable offline conversation uses bounded input acts, memory-grounded reminiscence, capability-tagged pending topics, nonverbal acknowledgements, and persistent shuffle cooldowns without model calls.
- Cartridge-authored Behavioral Richness tendencies expose probing, comparison, speculation, curiosity, and continued work through synthesis-selected actions and deterministic activity callbacks.
- Immutable performance plans that permit speech, gesture, silence, observation, delay, withdrawal, world action, or continued activity without forcing an expression-model call. Deterministic private cognition is the portable default, so non-speech turns can complete with zero renderer calls.
- Cartridge-authored deterministic offline realization for distinct character voices without character language in core modules.
- A small read-only semantic substrate for structured generic features, inheritance, associations, and candidate affordances.
- Validated capability-tier artifacts that remain usable by the same organism after a higher-capability renderer disappears.
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
341 passed, 1 skipped
```

## Run Simulators

```bash
python persona_engine/simulator.py --script persona_engine/simulator_scripts/pretorius_basic.yaml --cartridge persona_engine/cartridges/pretorius.snp
python persona_engine/simulator.py --script persona_engine/simulator_scripts/interpretation_basic.yaml --cartridge persona_engine/cartridges/pretorius.snp
python persona_engine/simulator.py --script persona_engine/simulator_scripts/organism_basic.yaml --cartridge persona_engine/cartridges/pretorius.snp
python persona_engine/simulator.py --script persona_engine/simulator_scripts/interpretation_anchored_misread.yaml --cartridge persona_engine/cartridges/pretorius.snp
python persona_engine/simulator.py --script persona_engine/simulator_scripts/synthesis_strain_recovery.yaml --cartridge persona_engine/cartridges/neutral.snp
python persona_engine/simulator.py --script persona_engine/simulator_scripts/self_monitor_strain.yaml --cartridge persona_engine/cartridges/pretorius.snp
python persona_engine/simulator.py --script persona_engine/simulator_scripts/self_monitor_correction.yaml --cartridge persona_engine/cartridges/kiki.snp
python persona_engine/simulator.py --script persona_engine/simulator_scripts/autobiographical_reconsolidation_weeks.yaml --cartridge persona_engine/cartridges/pretorius.snp
python -m persona_engine.behavioral_eval --scenario persona_engine/simulator_scripts/pretorius_kiki_paired.yaml
python -m persona_engine.playtest --scenario persona_engine/playtest_scenarios/steady_collaborator_30_days.yaml --actor-mode scripted --judge deterministic --output-dir playtest_output/steady
```

Compare a fresh Pretorius with the same organism after authored history has
passed through ordinary perception, consolidation, forgetting, and retrieval:

```bash
python -m persona_engine.genesis --cartridge persona_engine/cartridges/pretorius.snp --db genesis_eval.db --compare-fresh
```

See `persona_engine/docs/GENESIS_REPLAY.md` and
`persona_engine/docs/PERSONAL_JOURNAL.md` for authority and portability rules.

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

Open the local URL printed by Uvicorn. The UI supports cartridge selection, session reset, streamed chat, public organism status, avatar-safe state, voice-plan inspection, current interpretive beliefs, proactive proposals, mock audio observations, mock vision observations, optional read-only debug details, working local renderer controls, and checksum-verified session export/replay.

When the server is started with `--debug`, the debug tab includes a read-only life inspector for current activity, intention, attention, recent objective events, subjective experience versions, recall reasons, vitality events, learning artifacts, synthesis, performance, and semantic candidates.

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

Private cognition is independently configured as `deterministic`,
`model_optional`, or `model_required`. The portable default is deterministic.
Turn results and the debug inspector report private-cognition renderer calls,
expression renderer calls, fallback reasons, and total task calls separately.

`local_hf` registry entries are visible as a future provider seam but cannot yet be selected through the human UI.

Character sessions use separate persistence and renderer configuration. The UI labels a session as new, resumed, or fresh after reset. Read-only debug traces show retrieved-memory IDs and provenance; normal public status does not expose private memory state.

## Session Export And Replay

The report workspace can export a versioned JSON bundle containing the transcript, report draft, renderer configuration, cartridge checksum, canonical replay events, diagnostic turn records, stable turn seeds, and final state digest. Generated speech and renderer output are retained for human review but are never promoted into the canonical replay event stream.

Importing a valid bundle creates an isolated replay database and replays only approved input, bounded sensor, and world-action events. Checksums and cartridge identity are verified before replay. Deterministic state is compared with the exported digest; exact LLM prose reproduction is not promised. Export bundles can contain private debug and submitted context, so treat them as sensitive local test artifacts.

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
- `persona_engine/docs/V02_LIFE_SIMULATION.md`
- `persona_engine/docs/SEMANTIC_SUBSTRATE.md`
- `persona_engine/docs/INTRINSIC_MOTIVATION.md`
- `persona_engine/docs/AUTOBIOGRAPHICAL_RECONSOLIDATION.md`
- `persona_engine/docs/LONG_DURATION_MEMORY_PROOF.md`
- `persona_engine/docs/DEVELOPMENTAL_LIFE_V1.md`
- `persona_engine/docs/AUTOMATED_PLAYTESTING.md`
- `persona_engine/docs/CHARACTER_CROSSPLAY.md`
- `persona_engine/docs/BEHAVIORAL_RICHNESS.md`
- `persona_engine/docs/CHARACTER_BEHAVIOR_AUTHORING.md`
- `persona_engine/docs/NEXT_STAGES.md`
- `persona_engine/docs/ARCHITECTURE_LOCK.md`
- `persona_engine/docs/LAZARUS_MAPPING.md`
- `persona_engine/docs/CURRENT_STATUS.md`
- `persona_engine/docs/HUMAN_TESTING_UI.md`
- `persona_engine/docs/HUMAN_TESTING_PROTOCOL.md`
- `persona_engine/docs/HUMAN_TESTING_REPORT_TEMPLATE.md`
- `persona_engine/docs/V9_INTERFACE_NOTES.md`
- `persona_engine/docs/V10_SENSORY_EMBODIMENT_NOTES.md`
- `persona_engine/docs/C99_PORTING_NOTES.md`
