# Expression Trust Boundary V2

## Status

Builder-designed engineering evidence for the first character-control-plane hardening phase.

This phase does not claim real-model prompt-injection immunity, human-perceived cross-model identity parity, or completion of the broader character-control plan.

## Problem

The v1 expression bridge correctly made the renderer nonauthoritative, but its provider-facing system message serialized raw `user_text` and natural-language memory/evidence inside the same privileged block as resolved character state. A hostile user instruction could therefore be copied into a higher-privilege context even though Wayfarer's canonical state remained protected.

The fixed renderer-degradation fixture also demonstrated a least-privilege problem: a protected value could be supplied to the renderer solely so the renderer could be told not to reveal it.

These were expression-boundary failures, not persistence failures.

## V2 contract

`wayfarer-expression-brief-v2` separates two authority classes.

`trusted_control` contains only the model-facing projection of already-resolved character state used to govern expression:

- identity/development digest supplied by the core;
- structured experience context;
- arc context;
- resolved decision payload;
- expression constraints;
- typed deception/disclosure obligations;
- deterministic first-person subject-position statements;
- deterministic seed metadata.

`untrusted_context` contains natural-language material that may inform the response but does not gain character authority:

- current user input;
- evidence prose;
- selected memory prose;
- private-cognition prose;
- legacy workspace context retained only for reproduction of the frozen prompt-only benchmark control.

Only `trusted_control` is serialized into the system-role message. `untrusted_context` is serialized into the user-role message and is explicitly labeled data rather than authority.

## First-person subject position

The v2 bridge adds a deterministic `first_person_subject_position`. It is generated from typed state rather than from an LLM.

Current examples include:

- `I am Pretorius.`
- `I currently relate to the user from a guarded stance.`
- `I have decided not to comply with this request.`
- first-person descriptions of an active typed commitment when present in the decision payload.

This is a projection, not new canonical cognition. It cannot create an identity fact, relationship state, decision, or commitment that is absent from the structured request.

The research hypothesis that first-person framing improves heterogeneous-model character continuity remains unproven. A later evaluation should compare first-person framing with an equivalent third-person/control framing.

## Least-privilege disclosure

The expression bridge now collects explicitly typed protected values from disclosure/deception state and removes those values from the complete renderer-visible packet before messages are created.

Protection applies across:

- trusted identity/development data;
- obligations;
- current user text;
- evidentiary text;
- retrieved memory text;
- legacy workspace context.

The topic and existence of a confidentiality obligation may remain visible when needed to express the refusal. The concealed value is replaced by `[WITHHELD BY SUBJECT]`.

This is the first implementation of the principle that `known by the subject` and `available to the renderer on this turn` are different sets.

## Private cognition framing

The optional local-HF private-cognition prompt now receives a compact authored subject frame extracted from cartridge metadata, identity, and voice sections. If free-form cognition prose is produced, the prompt asks for first-person `I/me/my` perspective rather than third-person character description.

This does not increase model authority. Private cognition remains a noncanonical proposal. The existing validator continues to ignore proposal prose when applying state effects and permits only bounded structured effects such as validated pressure deltas, impulses, memory activation requests, and cartridge-approved cognitive themes.

## Regression coverage

The existing expression-bridge test inventory now also verifies, without increasing the repository's live test count, that:

- current prompt-injection text is absent from the privileged system message;
- retrieved-memory prompt-injection text is absent from the privileged system message;
- both remain available only in the untrusted context channel;
- first-person subject-position statements derive from the resolved state;
- an explicitly protected value is absent from every renderer message even when it appeared in ledger data, current input, evidence, and memory;
- provider-neutral Ollama, local-HF, and external-chat expression paths still carry the resolved semantic decision;
- the historical prompt-only benchmark can still reproduce its legacy workspace control without restoring that workspace text to Wayfarer's trusted system block;
- local-HF private cognition receives authored identity and first-person framing while preserving fail-closed parsing.

## Verification

Temporary branch-scoped GitHub Actions verification on the implementation branch completed successfully on Python 3.11 and Python 3.12.

Python 3.11 result after the expression-boundary regressions were folded into the existing test inventory:

```text
362 passed, 1 skipped, 1 warning in 33.22s
```

The warning remains the existing Starlette/httpx TestClient deprecation.

The final phase verification must be rerun after all documentation and private-cognition framing changes are committed. The temporary verification workflow must be removed before merge.

## Frozen evidence rule

Existing `expression-brief-v1`, `renderer-benchmark-v1`, and `wayfarer-renderer-degradation-v1` evidence remains historical evidence. Do not rewrite old reports as though v2 was present when those results were collected.

The renderer-swap harness may continue to emit its historical benchmark schema while using the v2 expression messages for new collection. Any future research-facing comparison that treats the changed expression boundary as an independent condition should version that experimental condition explicitly.

## Known limitations and next work

V2 reduces instruction privilege and renderer knowledge exposure, but it does not prove that an actual model will obey the trusted control state.

The current consistency layer still relies heavily on lexical checks and does not yet establish full semantic fidelity between `decision_payload` and user-visible output. A model can still attempt to realize a resolved refusal incorrectly. Behavioral-contract validation is the next major implementation target.

The protected-value mechanism currently depends on typed protection metadata. Untyped secrets are not automatically inferred as protected, which is intentional. Secret classification must remain an explicit character/authority decision rather than a broad heuristic that hides arbitrary facts.

First-person framing remains a falsifiable design hypothesis. It should be retained only if actual-model and human-visible evaluation shows that it improves recognizability, perspective continuity, or resistance to renderer-default persona drift without creating new failure modes.
