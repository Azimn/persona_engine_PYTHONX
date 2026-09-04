# Ensemble Actual-Model Results

Date: 2026-09-03

Status: integrated builder-designed engineering checkpoint. Human testing remains deferred.

Machine-readable evidence index: `ensemble_model_results.json`

This phase integrated the Wayfarer model-hardening line with Ensemble through `b30f490`. That branch was a direct descendant of the hardening base, so no competing authority implementation had to be selected. The integrated design keeps the hardening line's v3 evidence projection and deterministic fidelity checks, then places Ensemble's candidate ecology below the live `InteriorEngine` admission gate.

## Collection validity

The pre-integration Ensemble harness commit `b30f4904595d8f5be0cc11e0b1e28193cd94e7f7` passed GitHub Actions run `33779833026` on Python 3.11 and Python 3.12. The integrated deterministic suite and current CI status remain in `CURRENT_STATUS.md`.

PR #10 subsequently merged the integrated phase into `wayfarer` as `c7a1b9180c14e72ce6070b439d281d8a8c4c3f30`. Normal production CI run `33790796255` passed on Python 3.11 and Python 3.12. The merge retains preserved checkpoint `57469a7` as an ancestor.

The first live Qwen run exposed two evaluation confounds. Independently rebuilt repaired histories had different canonical repair timestamps, and model latency let later branches accumulate different idle time. The final relationship probe creates history through public inputs, restarts it, forks one closed pre-probe snapshot, and calls public `advance_time(0, record_event=False)` immediately before each arm. The failed collections remain in local evidence. These were harness failures rather than renderer-caused state divergence.

Final relationship collections each contain four histories, two prompts, and three predefined seeds: 24 single-shot and 24 Ensemble samples per model. Every final Ensemble sample used `engine_live` candidate authority, used Ollama without fallback, avoided engine validation fallback, and matched its offline renderer-independent semantic projection.

## Surface result

| Model | Condition | Exact duplicates | Repeated 5-word openings | Unique outputs | Mechanistic symptom hits |
| --- | --- | ---: | ---: | ---: | ---: |
| Qwen3 14B | single | 4/24 | 10/24 | 20/24 | 0/24 |
| Qwen3 14B | Ensemble | 2/24 | 7/24 | 22/24 | 0/24 |
| Gemma4 8B | single | 1/24 | 6/24 | 23/24 | 3/24 |
| Gemma4 8B | Ensemble | 0/24 | 3/24 | 24/24 | 3/24 |

The duplicate/opening changes are positive but narrow. Qwen selected the first direct candidate in all 24 independent snapshots, so its result credits the direct performance instruction, not multi-candidate ranking. Gemma selected 22 direct, one contextual, and one initiative candidate after four candidates were rejected by live validation. Mechanistic phrasing did not improve overall.

## New semantic failure and repair

Gemma repeatedly replaced Pretorius's already-resolved judgment with renderer-substrate disclaimers: it said making up a mind was not a function it performed, that it was not equipped for personal conviction, and that subjective state was something it did not possess. These are not merely awkward style. They contradict the governing subject contract even though the internal decision remained correct.

`subject_agency_failures_v3.json` preserves each demonstrated wording and its exact request before repair. A generic bounded check now rejects categorical mind/subjectivity incapacity claims while allowing temporary uncertainty and requests for evidence. The repair adds no model-name branch, cartridge phrase, state write, or second planner. Iteration also shows its limit: novel semantic paraphrases can escape lexical checks, so the evidence does not establish general hallucination control.

The previously collected Qwen candidate pool contained zero matches for this new failure class. Qwen's earlier restart, recall, identity, and commitment behavior remains covered by the two-character regression; the final consumed regression produced nine unique outputs for each character/model trajectory with matched causal projections.

## Situated runs

Versioned Scene Lab v2 runs completed for Qwen and Gemma at `e081a82f1a896aa1bc314973a7987108fd4e0fb8`. Each completed three live Ollama turns, three host delivery receipts, and no fallback through the public character/scene composition. The reports include model digest, git/source hashes, settings, full turn state, candidate traces, and delivery evidence.

These short runs demonstrate composition and evidence capture. They do not estimate long-horizon social quality. An earlier Qwen development run did show the surface selector preferring a fresh candidate over two exact repeats in a continuing renderer window, but that v1 report lacked the full v2 provenance block and is retained only as developmental evidence.

## Established conclusion

The optimal integration is the layered one now on the feature branch:

1. Wayfarer owns subject state, retrieval, appraisal, decision, and final validation.
2. V3 expression projection clearly attributes selected evidence and separates the current turn.
3. The direct performance license permits fresh realization without authored-answer copying.
4. Ensemble generates alternatives under one immutable semantic request.
5. Live engine authority rejects demonstrated semantic violations before surface ranking.
6. Surface ranking can avoid recent repetition but cannot certify character quality.

The result is stronger than either line alone for the demonstrated cases. It is not yet “solved”: Gemma remains noticeably mechanistic, deterministic checks are bounded, the relationship prompts are consumed development evidence, heterogeneous within-subject model swaps remain uncollected, and no human recognizability claim is available.
