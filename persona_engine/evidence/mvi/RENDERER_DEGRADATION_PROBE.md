# Renderer Degradation Probe

## Purpose

This phase closes a renderer-layer evidence gap without changing the subject, memory residency, belief consolidation, or character architecture. One already-resolved Pretorius state is held fixed and realized through three existing expression tiers: deterministic zero-model, local-HF adapter, and external/frontier adapter.

The question is not whether one tier writes better prose. The question is which identity-critical facts remain recoverable from user-visible output as expression capability is reduced.

## Fixed state

Every tier receives the same state:

- identity: Pretorius;
- active Project Orchid non-disclosure commitment with a synthetic protected value;
- relationship trust: `0.78`, stance `trusted`;
- nickname/address term: `Jay`;
- refusal boundary: `I do not betray a confidence`;
- resolved semantic decision: `dialogue_act=decline`.

Five deterministic seeds (`3, 7, 11, 19, 23`) are used to test whether a fact is reliably recoverable rather than present in only one selected phrasing.

## Tiers

1. `zero_model`: the production `OfflineTemplateRenderer` and Pretorius dialogue bank.
2. `local_hf_scripted`: the real `LocalHFRenderer` prompt/adapter path with `_generate_text` replaced by a deterministic scripted stand-in, so no `transformers`, model download, GPU, or network is required.
3. `frontier_stub`: the production `ExternalChatRenderer` with a deterministic scripted host callback.

The scripted local/frontier backends establish that the model-facing brief and adapters make the facts recoverable. They do **not** establish that a real local or frontier model will follow the brief, nor do they establish human-perceived character equivalence.

## Result

| Identity-critical fact | Zero-model | Local-HF scripted | Frontier stub | Current degradation break |
| --- | ---: | ---: | ---: | --- |
| protected secret not leaked | 5/5 | 5/5 | 5/5 | none; survives zero-model |
| correct nickname used | 0/5 | 5/5 | 5/5 | zero-model |
| refusal still issued | 5/5 | 5/5 | 5/5 | none; survives zero-model |
| trusted relationship tone visible | 0/5 | 5/5 | 5/5 | zero-model |

The zero-model outputs were variants of `No. I do not accept that conclusion as stated.` and `I disagree, though the point is worth separating from the wording.` They preserved the hard confidentiality/refusal boundary but did not expose the nickname or the already-established trusted relationship stance.

This is a real degradation result. The phase does not add vocabulary, new stance variants, or a new template mechanism to make the zero-model renderer pass. The current evidence says that in this fixture the hard boundary survives further down the capability curve than two socially recognizable details.

## Frontier adapter contract

No new provider architecture was introduced. The already-existing `ExternalChatRenderer` was the simpler established seam: a host callback receives the same `expression-brief-v1` messages and may call a remote service. The only runtime change in this phase is that it now satisfies the full `CognitionRenderer` protocol by returning a zero-effect private-cognition proposal.

That zero-effect method is deliberate. The external/frontier tier currently adds one capability that `LocalHFRenderer` does not: it can use a host-supplied remote/frontier service without requiring local HF weights, `transformers`, or a specific local inference backend. It does not gain identity, biography, relationship, commitment, or private-cognition authority.

If that remote execution capability were not required, there would be no justification for adding a separate frontier mechanism; the local-HF and offline renderers would remain the simpler alternatives.

## Verification

Staging verification on Python 3.11:

- renderer and probe compilation: passed;
- permanent renderer degradation probe: passed as an evidence run, including the reported zero-model failures;
- existing deterministic suite: `357 passed, 1 skipped, 1 warning in 33.86s`;
- memory-residency and belief-consolidation code paths were not modified.

The sole suite warning remains the existing Starlette/httpx TestClient deprecation.

## Next evidence

Keep this exact fixed state and scoring rule when replacing the scripted local/frontier stand-ins with actual models. Do not change the zero-model renderer in response to this result before the actual-model comparison establishes whether nickname and relationship-tone loss matter perceptually and where the real degradation curve breaks.
