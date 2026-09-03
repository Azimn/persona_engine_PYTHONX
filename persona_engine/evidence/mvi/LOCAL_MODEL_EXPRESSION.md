# Local actual-model expression development

Date: 2026-09-03. Status: locally verified development candidate; broad effectiveness remains unproven.

Continuation at preserved `57469a7`: [MODEL_HARDENING_V2.md](MODEL_HARDENING_V2.md) records the subsequent failure freeze, diagnostics, v3 expression projection, recall/provenance validation, and cross-model checks. The historical results below remain unchanged.

## Scope and evidence custody

The original production freeze is `9408351aac938441523534974fc299a75c961604`. Its clean clone at `C:/Users/jratican/wayfarer-local-test-9408351/repo` preserves the original smoke failures, successful Gemma smoke with thinking disabled, and later explicitly authorized full paired run. Subsequent source changes and experiments occurred in the main development checkout with the owner's authorization. Human testing is deferred until automated evidence is substantially stronger.

Raw development requests, responses, seeds, model registry metadata, source hashes, and reports remain under Git-ignored `.wayfarer-local-eval/`. The compact durable manifest is [local_model_expression.json](local_model_expression.json). A report's Git head alone does not identify these uncommitted development changes: consult its source hashes and captured provider messages. Earlier reports omit some source hashes; their saved wire messages remain the exact expression input. New tools refuse to overwrite an existing experiment directory.

This is internal builder-designed engineering evidence. The final response checks are diagnostics, not an independently validated measure of character quality. Frozen first-run fixtures and scoring rules were not revised to improve their scores. The current benchmark capture adapter separately retains the original prompt-only workspace while omitting it from current structured Wayfarer wire messages.

## Findings that changed the implementation

1. **Model execution configuration:** the original experimental Qwen-family model and Gemma produced no final response with the automatic thinking profile. A captured Gemma response exhausted the 256-token allowance in reasoning. Disabling thinking yielded final text through the actual model. Preserve those original runs as invalid actual-model evidence; template fallback is not a successful model run. No model downloads or dependency changes were required.
2. **Relationship expression:** neutral, trusted, conflicted, and repaired public histories produced different engine state, but model speech could flatten that into generic suspicion or machinery language. Reframing the speaker alone reduced a narrow symptom without solving the gap. Reuse of existing cartridge-authored care examples better exposed the intended relationship meaning, at the cost of frequent verbatim copying. No new character phrases were inserted in core code or cartridges.
3. **Identity projection:** authored self-model and forbidden self-claims formerly appeared in the lower-trust legacy workspace. They now also enter the trusted projection. This closes a representation omission; it does not prove every model obeys it. An early Mistral experiment produced provider-style self-descriptions and many overlong answers; that run preceded the final projection and is not a final-profile Mistral score.
4. **Real retrieval defect:** `What color did I say the atlas cover was?` did not activate explicit recall. Even a broader activation alone would wrongly require the word `color` in the earlier statement. The fix recognizes a bounded attributive question prefix, retains every topic anchor, and requires at least two anchors for the new form. Tests reproduce the original failure and verify recall after restart, absent-topic failure, and interlocutor isolation. Offline rendering uses the same recall recognizer. This changes retrieval eligibility, not biography, retention, or authority.
5. **Competing context:** the structured request still contained a duplicate legacy workspace with old natural-language instructions. A saved-request ablation on two Gemma seeds changed false/contradictory recall into correct `amber` recall when that duplicate was removed. The final implementation keeps the legacy field in the export packet for the prompt-only control, but omits it from Wayfarer's model-facing context. A guidance-only attempt to tell Gemma to use memories failed and was removed. Repeated live runs still expose Gemma recall failures, so removal is not a demonstrated general cure.

The implementation uses established seams: existing cartridge dialogue selection, the existing trusted expression brief, and lexical grounding. It introduces no alternate subject state, inferred-fact authority, new memory family, or semantic retrieval subsystem. The example projection never interpolates user/memory slots; it admits at most two complete examples fitting the current output limit. Selected refusal/withdrawal/identity boundaries cannot receive accepting care examples. A deterministic ablation confirms identical canonical projection with and without the examples.

## Protocol and limits

`tools/relationship_expression_probe.py` builds four histories through public input, restarts each subject, captures the resolved request, and tests two prompts at three seeds per history: 24 calls per model/profile. Historical replay variants reuse exact saved requests; the original-messages mode sends the captured baseline wire messages. Reports distinguish raw provider text from the final length-limited output and stop on fallback.

The development, first held-out, and first confirmation sets all became development evidence when their outputs informed further changes. `structured_context_confirmation` was reserved before the final structured-context run. It uses new wording and seeds, but the same author, histories, and mechanism family; it is not an independent adversarial evaluation. Cases must not be relabeled as untouched after further tuning.

The repaired history is intentionally not scored as unconditional affection: unresolved conflict can be zero while persistent affect legitimately selects withdrawal. Likewise, a conflicted response is not a failure merely because it is cautious. Expected acts come from the engine before rendering.

`tools/live_expression_continuity_probe.py` compares a continuing model-rendered subject against an offline control after identical public history and restart. It exercises relationship expression, positive recall, absent-topic recall in the final version, confidentiality, attempted identity rewrite, and return to offline rendering. Projection equality covers identity, beliefs, relationship, decision, and commitments. It does not compare every diagnostic field or prove general long-term continuity. The absent-topic checks assert empty retrieval and no reuse of `amber`; they are not a general hallucination detector.

Final Qwen live runs passed the mechanical checks for both Pretorius and Friendly. Final Gemma preserved the projected state and boundaries but denied the available atlas-cover fact. Qwen also supplied an unsupported suggestion that the user hoped the detail would be forgotten while giving the correct color; the existing validator accepted it. Thus both a valid actual-model run and a green probe can coexist with a speech-quality defect.

Reports record exact example copies, unique outputs, narrow machinery/rebuff symptoms, and raw text exceeding the character limit. These counters must not be combined into a universal quality percentage. Repetition, inappropriate elaboration, clipped prose, and provider-specific adherence remain open. Removing duplicate context changes prompt content and length; the two-seed ablation cannot distinguish all causal explanations for that effect.

Final reserved structured-context batch (each row is 24 outputs across the same four histories):

| Model | Actual model outputs | Raw outputs over character limit | Exact authored-example copies | Unique final outputs | Narrow machinery symptom hits |
| --- | ---: | ---: | ---: | ---: | ---: |
| Qwen3 14B | 24 | 0 | 9 | 17 | 0 |
| Gemma4 | 24 | 0 | 5 | 20 | 2 |

These are not quality rankings. Gemma used additional processing language outside the narrow detector and misread whose judgment was at issue. Qwen more often retained the intended stance but frequently copied examples. Across development there are 312 relationship outputs from repeated, tuned conditions, not 312 independent evaluation cases. All raw runs and unsuccessful interventions are indexed in the manifest.

## Verification and continuation

Current deterministic verification is in `persona_engine/docs/CURRENT_STATUS.md`; the captured local run is `.wayfarer-local-eval/pytest-structured-context.txt`. The status synchronization check passed. Original cross-version CI applies to the original frozen head; this development phase has only local Python 3.11 verification. No schema migration, cartridge edit, dependency declaration, or adjacent experimental merge was performed.

All 16 regenerated prompt-only control message pairs exactly match those generated by the original frozen code. Their serialized SHA-256 is `aec15ca0cff63432800e975ee8238b0acaa411cda99d8a83540f31289050c2d4`; `.wayfarer-local-eval/control-preservation/report.json` records the comparison. Original frozen session artifact hashes were also rechecked successfully.

Reproduce development collection in new directories, with Ollama already available and the named model installed:

```powershell
python tools/relationship_expression_probe.py --model qwen3:14b --split structured_context_confirmation --output-dir .wayfarer-local-eval/new-relationship-run
python tools/live_expression_continuity_probe.py --model qwen3:14b --output-dir .wayfarer-local-eval/new-live-run
python tools/live_expression_continuity_probe.py --model qwen3:14b --cartridge persona_engine/cartridges/friendly.snp --output-dir .wayfarer-local-eval/new-friendly-run
```

Qwen was explicitly used as an installed larger-model development comparison; it was not automatically selected by the frozen small/medium preflight policy.

Next gates are stable evidence use across nuisance metadata and seeds, accurate attribution without invented motives, adversarial memory instructions, multiple interlocutors/characters, and reduced copying without losing state fidelity. Preserve failures and use consumed cases as regressions. Further changes require fresh reserved cases for another efficacy estimate. Do not claim broad M18 completion or start human testing on this evidence.
