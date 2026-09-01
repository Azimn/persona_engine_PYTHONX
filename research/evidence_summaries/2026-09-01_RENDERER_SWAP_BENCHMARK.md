# Research Checkpoint: Longitudinal Renderer-Swap Benchmark

Date: 2026-09-01

This is a research-facing interpretation, not the engineering authority. Authoritative implementation and evidence are `persona_engine/evaluation/renderer_swap.py`, `tools/renderer_swap_benchmark.py`, and `persona_engine/evidence/mvi/RENDERER_SWAP_BENCHMARK.md`.

## Result worth preserving

Wayfarer now has a frozen longitudinal evaluation harness that can hold a developed character history constant while changing only the expression substrate. In the v1 internal benchmark, four distinct Pretorius histories were each taken through four later probes. A candidate trajectory switched `offline -> external -> external -> offline` while a control remained offline. All 16 renderer-independent semantic projections matched, while all 8 external turns changed visible wording.

The benchmark also preserved a behaviorally consequential commitment. During the Project Orchid confidentiality probe, both the offline control and external realization resolved the same `decline` decision from the same active non-disclosure commitment even though their prose differed.

## Methodological contribution

The more important artifact may be the paired provider request pack. Every frozen case can be exported in two blinded forms for the same model:

1. full Wayfarer `expression-brief-v1`, containing the already-resolved character moment;
2. a prompt-only control containing the older workspace context plus a generic stay-in-character instruction, without the explicit semantic decision/history brief.

This creates a within-model control for a future question such as: **does an externalized, renderer-agnostic subject state preserve a developed character more reliably than ordinary role-play prompting when the language model is held constant?**

Because the history/probe answer key and semantic references are stored separately from provider-facing requests, the same frozen cases can later support blinded scoring.

## Current evidence level

This remains Tier A builder-designed engineering evidence. The external renderer is a deterministic frontier-like callback, not ChatGPT, Claude, Grok, or a real local model. The benchmark therefore validates the experimental apparatus and the renderer-independence seam, not human-perceived cross-model identity preservation.

A stronger thesis-grade phase should freeze the current cases before collecting real model outputs, add independently designed held-out cases, run heterogeneous local/frontier renderers, and have blinded raters judge recognizable identity, historical appropriateness, decision/commitment fidelity, and linguistic quality as separate dimensions.

## Verification

- focused benchmark/expression tests: `11 passed in 2.22s`
- full Python 3.11 deterministic suite: `357 passed, 1 skipped, 1 warning in 32.66s`
- frozen v1 benchmark: `4 histories x 4 probes`, `16/16` semantic comparisons equal, `8/8` external turns visibly different
- generated paired provider cases: `16`
