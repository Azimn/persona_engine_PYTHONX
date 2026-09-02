# Methods and Evaluation Scaffold

This file separates tests used to **build** Wayfarer from evaluations used to **judge claims about** Wayfarer.

## 1. Development evidence

Development tests may be designed with knowledge of the implementation. Their purpose is to expose causal gaps, localize failures, prevent regressions, and justify the minimum mechanism added to production.

Examples include:

- pre-fix falsification probes;
- unit and integration tests;
- causal ablations;
- replay/restart checks;
- storage and resource measurements;
- deterministic longitudinal fixtures.

These are necessary engineering evidence, but they are not independent validation.

## 2. Held-out adversarial evaluation

Before making strong thesis-level claims, freeze:

1. the candidate implementation;
2. the claim being tested;
3. the public interfaces and allowed setup;
4. the scoring criteria.

Then give an independent evaluator the claim and supported interfaces without giving it the builder's intended solution or existing fixture-construction rationale.

Its explicit task should be to find a minimized counterexample.

Potential attack families include:

- restart and replay;
- model/renderer substitution;
- interlocutor switching;
- long time gaps and temporal discontinuities;
- conflicting memory and lexical distractors;
- repair/reopened social history;
- commitment pressure;
- identity-rewrite pressure;
- host migration and stale writers;
- disconnected copies and intentional branching when implemented;
- combinations of several obligations in one continuing history.

If a held-out attack fails the system, preserve the original attack unchanged, repair the implementation, and rerun the frozen attack. Do not rewrite the evaluator's test to match the repair.

## 3. Comparative conditions

For a future model-substitution study, useful conditions may include:

1. raw conversation/history transfer;
2. conventional persona-prompt transfer;
3. persistent Wayfarer subject-state transfer;
4. persistent subject state plus model-specific renderer adaptation.

The exact comparison should be selected only after the renderer-independence contract is mature enough to test fairly.


### Real-renderer collection discipline

The first actual-model renderer runs should preserve the frozen builder-designed cases rather than tuning them after outputs are observed. Record provider/model identity, available sampling configuration, request hashes, raw responses, Wayfarer code checkpoint, and whether any fallback occurred. A fallback response may be diagnostically useful but cannot be counted as evidence for the requested model tier.

Fixed-state degradation and Wayfarer-versus-prompt-only comparison answer different questions. The former asks which identity-critical signals remain recoverable as renderer capability decreases. The latter holds the underlying model constant and asks whether the externalized Wayfarer subject state preserves the developed character better than ordinary prompt-based role-play. Mechanical semantic checks and human recognizability/linguistic-quality judgments should remain separate outcomes.

For local collection, the execution agent should be treated as an operator rather than an evaluator: environment discovery and installed-model selection are machine-generated, model downloads are prohibited during collection, the smoke gate is completed before the larger paired run, and raw outputs are preserved unchanged for later scoring. This separation reduces both coding-agent intervention and the risk of tuning the implementation while observing evaluation responses.

## 4. Outcome families

Do not collapse every result into one "lifelikeness" score.

Possible dependent measures include:

- trajectory invariance under model substitution;
- commitment consistency;
- relationship-specific continuity;
- grounded autobiographical recall;
- resistance to unauthorized identity mutation;
- developmental replay equivalence;
- cross-host state equivalence;
- branch/copy discrimination;
- expressive-style distance;
- human judgment of "same character/person";
- task-relevant believability;
- kernel CPU, memory, storage, and latency measured separately from renderer cost.

## 5. Human-visible evaluation

Where the research claim concerns perceived identity or believability, internal state invariants are insufficient.

A later human study could use blind transcript or interaction comparisons in which participants judge whether two sessions appear to belong to the same continuing character. Model identity and condition should be hidden where practical. The study design should distinguish behavioral continuity from surface fluency.

Any human-subject study must follow the applicable institutional ethics/IRB process before data collection.

## 6. Threats to validity to track

- builder-designed fixtures can share assumptions with the mechanism they test;
- deterministic fixtures may underrepresent open-ended linguistic behavior;
- one character or one interlocutor history may not generalize;
- one renderer family may make continuity easier or harder than another;
- repeated tuning on a benchmark converts it from evaluation data into development data;
- a coherent internal state does not guarantee human-perceived continuity;
- high-quality language generation can mask weak continuity, while weak rendering can mask strong continuity;
- engineering parameter values are not automatically psychologically valid.

## 7. Reproducibility rule

Research-facing results should retain the exact code/test checkpoint, evidence artifact, condition definition, and negative controls needed to reproduce the claim. Dated summaries may interpret results, but the underlying test/evidence artifact remains authoritative.
