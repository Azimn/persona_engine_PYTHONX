# Pre-LLM architecture review: impact on Project Ensemble

Date: 2026-09-03

## Conclusion

The legacy conversational-agent research did not merely justify a historical comparison. It changed the successor architecture.

The strongest pre-LLM systems repeatedly converged on an important pattern: believable behavior was rarely produced by unrestricted surface generation alone. Persistent state, goals, discourse control, authored landmarks, initiative, candidate generation, ranking, world state and host consequences surrounded comparatively weak language generation.

Modern LLMs change which component is strongest, but they do not remove the value of that surrounding architecture. Actual Qwen/Gemma testing additionally showed a modern failure mode: a control plane can become so strict that the language substrate is reduced to repetitive realization. Project Ensemble therefore keeps external subject authority while giving the model more freedom inside a candidate ecology.

## Principles now implemented

### Persistent simulation outside language generation

Identity, biography, relationships, commitments, authored values, memory provenance, world truth and final semantic decisions remain outside the model.

### Candidate generation plus selection

One resolved character moment may now produce several alternative model performances. The default candidates use distinct direct, contextual and initiative-capable performance licenses rather than being seed-only paraphrases.

### Validation before soft ranking

Candidate outputs now reuse the deterministic production consistency contracts before they compete on surface diversity. Hard and critical violations are removed from the pool rather than being allowed to win because they are novel.

### Sparse authorship rather than giant response banks

Typed relationship/act-selected authored examples can enter Ensemble as peer candidates. They are not shown to the model as sentences to imitate and are not automatically selected.

### Initiative and agenda

`ConversationalAgenda` projects existing intentions, open loops, shared symbols, habits and relationship state into an explicit initiative pressure. This creates an inspectable cause for a model candidate to ask, observe or reconnect to something the character already carries.

There is no conversation-length or engagement-maximization objective.

### Situated causal interaction

Scene Lab now provides a bounded sibling host with actors, locations, actor-specific visibility, server truth, movement, events and speech delivery.

### Intended speech is not automatically world reality

Speech delivery receipts distinguish complete delivery, interruption and no delivery. A model-generated sentence that never reaches another actor is therefore representable as a failed action rather than as completed social history.

### Subject-relative meaning

A typed experimental appraisal layer now separates event annotation from subject-specific meaning. The same event can have different goal, relationship, identity, controllability and threat/opportunity significance for different subjects without rewriting the shared event record.

## Principles deliberately not adopted

- No engagement-maximization objective such as maximizing conversation length.
- No universal drama manager that owns character goals.
- No giant hand-authored dialogue tree.
- No model-specific personality branch.
- No LLM judge with hidden canonical write authority.
- No free-form model reflection automatically promoted to canonical biography.
- No assumption that historical architectures should be copied literally.

## Current implementation map

| Legacy lesson | Ensemble mechanism |
| --- | --- |
| multiple response possibilities | `EnsembleLLMRenderer` candidate ecology |
| response ranking | deterministic candidate validation + surface ranking |
| authored high-value behaviors | sparse `AUTHORED` candidate source |
| discourse agenda / initiative | `ConversationalAgenda` + initiative performance mode |
| world model / situated interaction | `SceneLab` server truth + visible context |
| actual action consequence matters | `SpeechDeliveryReceipt` |
| same event means different things to different characters | typed `SubjectRelativeAppraisal` |
| explicit state around weak language generation | inherited Wayfarer persistent subject kernel |

## Evaluation architecture

`tools/ensemble_relationship_probe.py` reuses the hardened Wayfarer relationship histories while changing the realization substrate.

`tools/compare_ensemble_reports.py` compares matched single-shot and Ensemble reports using artifact-grounded measurements including duplicate rates, repeated openings, narrow symptoms, candidate survival, selected source/mode, prevalidation rejection counts and initiative availability.

These measurements are intentionally separated from identity-fidelity claims. A response can be novel and still be wrong.

Future evaluation therefore needs three distinct layers:

1. **surface quality**: repetition, stiffness, truncation, mechanistic narration;
2. **semantic fidelity**: decision, recall, commitment, provenance, disclosure and world truth;
3. **perceived continuity**: paired human recognition and cross-model character identification.

## Remaining research frontier

The architecture is no longer waiting on a candidate-selection prototype. The important open work is causal integration and ablation.

### Engine-owned candidate orchestration

Candidate prevalidation currently uses the authority already projected into `ExpressionRequest`; the engine then performs its normal final validation.

A stronger endpoint is engine-owned orchestration where every candidate is evaluated against the complete live authority context without copying additional privileged state into the renderer.

### Appraisal consumers

The subject-relative appraisal representation is only useful if controlled tests show it changes a necessary downstream behavior. Candidate consumers include attention, memory salience, retrieval, pressure persistence, disclosure and semantic action.

### Delivery consequence integration

The core continuing subject still assumes normal response delivery during its canonical post-speech update. Scene Lab can now represent partial/failed delivery, so the next causal experiment is to determine which subject state should be updated from the delivery receipt rather than from intended text.

### Persistent conversational agenda

Current agenda is a rebuildable projection of existing state. New canonical agenda fields such as pending questions or intended disclosures should be added only when scenes demonstrate that existing intentions/open loops/symbols/habits cannot preserve the required continuity.

### Cross-character / cross-model ablation

The final useful question is not whether each mechanism sounds plausible. It is which combination is actually required for recognizable continuity, initiative and life-like situated behavior across different models.

## Current hypothesis

The emerging architecture is not “LLM plus memory” and not “deterministic character system plus text renderer.”

It is closer to:

```text
persistent subject
    +
causal world/history authority
    +
replaceable generative cognitive-language organ
    +
multiple noncanonical proposals
    +
explicit validation/selection
    +
actual host consequences
```

The language model is allowed to contribute substantially more than phrasing, but contribution and authority remain different concepts.
