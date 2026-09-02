# Wayfarer Local Testing: Codex Operator Protocol

This file is the short path for a Codex session whose only job is to execute the frozen Wayfarer actual-model tests on a Windows machine with Ollama.

## Do not investigate the project first

For this execution-only task, do **not** read the full roadmap, architecture documents, research notes, or test suite before running the harness. Do not redesign, repair, refactor, or tune Wayfarer. Do not pull or install an Ollama model automatically.

The harness already knows:

- which branch must be active;
- whether the working tree is clean;
- whether Ollama is reachable;
- which models are already installed;
- which installed models are unsuitable embedding/reranking models;
- which installed small model is the preferred smoke-test candidate;
- whether a distinct medium comparison model is already available;
- the frozen renderer-degradation requests and scoring checks;
- the frozen 16-case Wayfarer-versus-prompt-only request pack;
- how to reject Ollama fallback so template output cannot be mistaken for model evidence.

## Step 1: preflight only

From the repository root:

```powershell
git switch wayfarer
python tools/local_eval.py preflight
```

Or on Windows, double-click/run:

```text
Run_Wayfarer_Local_Eval.cmd
```

The command writes:

```text
.wayfarer-local-eval/
  preflight.json
  NEXT_STEPS.txt
```

Read `NEXT_STEPS.txt`. Do not infer a different model choice yourself.

If preflight says `BLOCKED`, **stop**. Return `preflight.json` to the owner/ChatGPT. Do not spend tokens exploring the repository or attempting repairs unless explicitly asked.

## Step 2: one smoke run

If preflight says `READY`, run the exact smoke command written in `NEXT_STEPS.txt`.

The smoke phase performs only the frozen five-seed fixed-state degradation experiment. It is intentionally the cheapest actual-model test.

A successful smoke run writes:

```text
.wayfarer-local-eval/
  degradation-<model>.json
  SESSION_SUMMARY.json
  SESSION_SUMMARY.md
```

If `SESSION_SUMMARY.json` says `VALID_ACTUAL_MODEL_RUN`, **stop** and return that file. Do not automatically continue to the 16-case comparison.

If it says `INVALID_MODEL_RUN`, stop and return the summary. The harness has already captured whether Ollama fell back and why.

## Step 3: full paired comparison only when explicitly requested

A later instruction may tell you to run the prepared full command in `NEXT_STEPS.txt`:

```powershell
python tools/local_eval.py full --model "<selected installed model>"
```

This first repeats the five-seed model-validity/degradation gate. Only if that remains a real Ollama run does it execute the frozen 16-case paired comparison:

- Wayfarer `expression-brief-v1` arm;
- prompt-only role-play arm;
- same local model;
- same deterministic seed within each pair;
- alternating arm order across cases.

The full run writes raw responses separately from the answer key/reference file so later evaluation can remain blinded.

## Token-saving stop rules

Codex should stop and return a compact result when any of these occurs:

1. preflight is blocked;
2. Ollama is unreachable;
3. no eligible installed small/medium text model exists;
4. any request falls back to the zero-model renderer;
5. the smoke run completes successfully;
6. the explicitly requested full run completes successfully.

Do not use model output to modify Wayfarer during the same collection session. The frozen evaluation must remain frozen after outputs are observed.

## What to return

Return only:

1. the exit code;
2. the path to `.wayfarer-local-eval/SESSION_SUMMARY.json` or `preflight.json` if blocked;
3. at most a few lines describing any machine-level failure that prevented the harness from writing those files.

Do not paste raw 32-response benchmark output into the Codex conversation. Those files are for later analysis by the owner/ChatGPT.

## Model policy

The preflight selector targets an already-installed model near 3B parameters for the smoke role and an already-installed model near 8B for the later comparison role. It will not automatically select a model above the medium tier and will never run `ollama pull`.

If the desired tier is missing, stop after preflight. Model installation should be a deliberate separate decision, not something an execution agent improvises.
