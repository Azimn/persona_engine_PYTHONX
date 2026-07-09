# Human Testing Protocol

This protocol is for local, nontechnical testing of the Persona Engine human-testing UI. The UI displays public organism state; it does not author private organism state.

## Install Dependencies

From the package parent directory:

```bash
python -m pip install -e .
python -m pip install -r requirements-dev.txt
```

## Run The UI

From the package parent directory:

```bash
python -m uvicorn "persona_engine.ui:create_app" --factory --reload
```

Or use the installed entry point:

```bash
persona-engine-ui
```

Open the local URL printed by Uvicorn. The UI requires no microphone, camera, TTS, avatar engine, GPU, network model, mobile runtime, or Ollama.

## Select A Cartridge

Use the Character selector in the top bar, then choose Load. The active cartridge is shown in the session status line. Cartridges are loaded from `.snp` files without editing code.

Use Reset session to clear lived session state for the active cartridge. Reset does not modify cartridge files.

## Basic 10-Minute Test

1. Load a cartridge and send a neutral greeting.
2. Ask a factual or personal-continuity question.
3. Send a mild contradiction or resistance.
4. Wait briefly, then use Simulate silence.
5. Trigger one mock audio event and one mock vision event.
6. Ask a follow-up that should reflect continuity.
7. Check public status, current beliefs, voice-plan state, avatar-safe state, and proactive proposals.

## What To Look For

Look for continuity across turns, bounded responses, memory of lived interaction, resistance to identity rewrites, time and consequence after silence, grounded interpretation, and no leakage of hidden facts as objective truth.

Current beliefs are subjective interpretations. They may be wrong, but they should be grounded in visible facts.

## What Not To Expect Yet

Do not expect full voice, real camera, real microphone, an avatar engine, true autonomy, GPU support, or mobile-native support. The sensor, voice, and avatar surfaces in this UI are mock-safe adapters or state plans.

## Report A Failure

Record the cartridge name, session status, the exact user prompts, any mock sensor buttons used, what appeared in public status, and what response seemed wrong.

For leakage issues, note whether the fact was visible to the character or hidden server truth. Hidden server truth must not appear as an objective claim.

## Public Status Vs Debug State

Public status uses categorical buckets such as `low`, `steady`, `high`, `quiet`, `present`, or `guarded`. It should not expose raw pressure, trust, shame, fear, attachment, belief ledger values, private memories, or hidden server truth.

Debug state is read-only and off by default. When server debug mode is enabled and the tester turns on the UI toggle, debug may show event IDs, workspace summaries, validator actions, replay/debug references, and a private snapshot for developer inspection. Debug mode must never provide a way to mutate private state.
