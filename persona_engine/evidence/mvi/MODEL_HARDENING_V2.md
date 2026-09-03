# Actual-model hardening v2

2026-09-03. This phase starts from preserved commit `57469a7` on the dedicated `wayfarer-local-model-hardening` branch. The checkpoint was pushed before changes. Original v1 reports and fixtures remain unchanged.

## Failure freeze and diagnostic contract

`persona_engine/evaluation/fixtures/local_model_failures_v2.json` freezes the exact Gemma denial request/response, Qwen's tentative motive implication, and repeated authored-example requests from the previous checkpoint. A replay of the same Gemma denial messages and seed reproduced the same denial twice before any behavioral repair (`.wayfarer-local-eval/v2-frozen-replay/report.json`). Selected canonical user-statement evidence reaches the request verbatim. This is class C, model disregard/contradiction of supplied evidence, with class D context interpretation a possible contributing cause. It is not missing retrieval.

`tools/model_hardening_v2.py` observes canonical inputs, selected memories and provenance, coverage in the wire request, appraisal input, interpretation, expression request, resolved act/behavioral contract, raw model calls, final validation, and semantic projections. It compares continuing offline/model trajectories for Pretorius and Friendly. Instrumentation never changes a decision or retrieves additional evidence for the model. Versioned development and reserved confirmation prompts were defined before running repairs.

The repetition analyzer detects exact/normalized duplicates, similar token sequences, repeated openings, repeated five-word phrases, and refusal reuse. It records whether colliding outputs came from different semantic projections. Shared voice is not automatically a failure; variation alone is not a quality score.

The old Qwen phrase `as if it were a detail you hoped I'd forget` is tentative, rather than an established fact assertion. Under the owner's clarified allowance for speculation, it is a provenance/wording case, not automatically a hard contradiction. Tests must distinguish it from an unsupported confident assertion such as `I know you hoped I would forget`. Neither may write biography or relationship truth.

Normal CI now runs for Wayfarer feature branches and PRs targeting `wayfarer`, as well as existing targets. This replaces reliance on local-only verification; current counts remain in `CURRENT_STATUS.md`.
