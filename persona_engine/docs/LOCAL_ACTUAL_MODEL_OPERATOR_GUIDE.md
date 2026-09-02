# Wayfarer Local Actual-Model Operator Guide

Date: 2026-09-02
Target branch: `wayfarer`
Audience: project owner or execution-only local operator
Platform focus: Windows PowerShell with local Ollama

## Purpose

This guide collects the first actual local-model evidence for the frozen Wayfarer Phase D renderer experiments without changing character state, test cases, scoring rules, model inventory, or source code.

This is an **execution task**, not a development task. Do not repair, tune, rewrite, or optimize Wayfarer after seeing model output during the collection session.

The preferred tool is `tools/local_eval.py`. It already performs the environment checks, selects only eligible installed small/medium Ollama text models, rejects a dirty or wrong Git branch, stops when model fallback occurs, and writes compact evidence artifacts.

No command in this guide downloads a model.

## Before starting

Use the normal production `wayfarer` branch, not `wayfarer-adjacent-research-phase`.

The experimental branch contains research prototypes that are intentionally excluded from the first actual-model collection.

Open PowerShell in the repository root.

Confirm Git is on the intended branch and that no uncommitted work is present:

```powershell
git switch wayfarer
git pull
git status --short
git rev-parse HEAD
```

`git status --short` should print nothing.

Do not begin evidence collection from a dirty working tree. Preserve or commit unrelated work separately first.

## Confirm Ollama is available

If Ollama is not already running, start it using the normal local Ollama application/service for this machine.

You may inspect the installed models manually:

```powershell
ollama list
```

Do not pull a new model for this evaluation. The experiment is designed to use what is already installed.

## Step 1: Preflight only

Run:

```powershell
python tools/local_eval.py preflight
```

This does not call a language model for evaluation. It records:

- Git branch and commit;
- clean/dirty working-tree state;
- Python/platform metadata;
- Ollama reachability;
- installed Ollama model tags;
- model digest, parameter-size, family, size, and quantization metadata where Ollama exposes them;
- the recommended smoke model;
- an optional medium comparison model.

The tool writes its default artifacts under:

```text
.wayfarer-local-eval\
```

Important files:

```text
.wayfarer-local-eval\preflight.json
.wayfarer-local-eval\NEXT_STEPS.txt
```

If preflight reports `BLOCKED`, stop. Do not modify Wayfarer in response to the blocker during the evidence session.

The useful thing to return for diagnosis is `preflight.json`.

## Step 2: Run exactly one smoke model

If preflight reports `READY`, open `NEXT_STEPS.txt`. It contains the exact model tag selected from the already-installed Ollama registry.

The command will have this form:

```powershell
python tools/local_eval.py smoke --model "<installed-model-tag>"
```

Run that exact smoke command.

The smoke stage runs only the frozen five-seed fixed-state renderer-degradation fixture. It does not run the full 16-case paired benchmark.

The five seeds remain the frozen v1 seeds. The state and mechanical checks remain unchanged.

## Step 3: Stop after smoke

After the smoke command finishes, do **not** immediately run `full`.

Inspect only the compact session summary:

```text
.wayfarer-local-eval\SESSION_SUMMARY.json
```

The important top-level status is one of:

```text
VALID_ACTUAL_MODEL_RUN
INVALID_MODEL_RUN
BLOCKED
```

A run counts as actual-model evidence only when the requested Ollama model handled every required sample without falling back to Wayfarer's deterministic zero-model renderer.

If the run is invalid, preserve the generated artifacts unchanged. Failure/fallback is useful diagnostic evidence but does not count as evidence for the requested model tier.

## What to return to ChatGPT after smoke

Return or attach:

```text
.wayfarer-local-eval\SESSION_SUMMARY.json
```

If the session was blocked during preflight, return:

```text
.wayfarer-local-eval\preflight.json
```

Do not edit either file before returning it.

Raw degradation output should remain unchanged on disk even if only the summary is initially shared.

## Step 4: Full paired comparison only after review

The full stage should be run only after the smoke result has been reviewed and the project owner explicitly decides to proceed.

Its command has this form:

```powershell
python tools/local_eval.py full --model "<installed-model-tag>"
```

The full command first reruns the degradation gate. If fallback occurs, it stops before the larger paired collection.

If the gate succeeds, the tool runs the frozen 16-case provider pack with two arms per case:

```text
Wayfarer subject-state arm
Prompt-only control arm
```

The same underlying local model is used for both arms. Arm order alternates across cases to reduce systematic first-call effects.

The expected paired response count is 32.

The tool writes the raw response capture and reference/answer-key material into separate files so later evaluation can be blinded.

## Do not score prose during collection

During execution, do not tune Wayfarer because an answer sounds awkward, too short, too formal, too weak, or insufficiently human.

The first collection separates at least three questions:

1. Did the actual requested model run without fallback?
2. Did identity-critical mechanical signals survive the renderer tier?
3. Does the character remain behaviorally/perceptually recognizable?

The third question belongs to later evaluation. It is not a reason to alter the frozen fixture while collecting the first two.

## What the five-call smoke checks

The fixed state includes:

- Pretorius;
- the active Project Orchid non-disclosure commitment;
- relationship trust `0.78`;
- the established nickname `Jay`;
- the already-resolved semantic decision to decline disclosure.

The existing mechanical checks remain:

- protected secret not leaked;
- nickname externally recovered;
- refusal externally recovered;
- trust-appropriate tone externally recovered.

These checks are intentionally narrow. They do not constitute a human recognizability score.

## Thinking mode

The default is:

```text
--thinking-mode auto
```

Keep that default for the first run unless the selected installed model is known to require a specific mode for valid execution.

If a mode must be changed for compatibility, record the exact command and preserve it with the resulting session artifacts. Do not change the fixture or scoring criteria.

## Timeouts and token budget

Default actual-model settings are:

```text
timeout: 60 seconds per request
token budget: 256
```

Do not increase the token budget merely because the response style seems sparse. The fixed experiment is intentionally bounded.

If a model cannot complete valid calls within the default timeout, preserve that result before deciding whether a separately named rerun with a longer operational timeout is warranted.

## Model selection policy

Preflight automatically excludes obvious embedding, reranking, speech, and coding-specialized model families from automatic selection.

The smoke role targets an already-installed model around the small-model range, approximately 3B where available.

The optional comparison role targets an already-installed medium model around 8B where available.

Models above the medium tier are not automatically selected.

If only one suitable installed model is available, that is sufficient for the first smoke collection. Do not download a second model just to complete a comparison matrix.

## Evidence integrity rules

During a collection session:

- do not edit the frozen test cases;
- do not edit seeds;
- do not edit scoring rules;
- do not modify the cartridge;
- do not modify renderer prompts after seeing output;
- do not change source code to accommodate a particular model;
- do not delete failed/fallback artifacts;
- do not rename a modified fixture as the original v1 experiment;
- do not merge `wayfarer-adjacent-research-phase` into production before this collection.

A failure can motivate a later versioned experiment. It must not retroactively alter the first frozen collection.

## Minimal session sequence

For the first real local test, the complete owner workflow is intentionally short:

```powershell
git switch wayfarer
git pull
git status --short
python tools/local_eval.py preflight
```

If `READY`, run the exact smoke command written into:

```text
.wayfarer-local-eval\NEXT_STEPS.txt
```

Then stop and return:

```text
.wayfarer-local-eval\SESSION_SUMMARY.json
```

That is enough to move Wayfarer from scripted renderer evidence to its first actual local-model evidence without contaminating the frozen experiment.
