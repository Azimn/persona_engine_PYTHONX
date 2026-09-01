# Expression Substrate Continuity V1

## Falsification target

The same resolved Wayfarer character moment should be realizable by a deterministic offline renderer, a local model, or a host-supplied frontier model without asking each substrate to independently infer the character's decision or developmental position from a role-play prompt. Accumulated relationship history should also be capable of changing visible offline performance, not only hidden state.

## Pre-fix gaps

- Ollama received explicit structured decision payload: `False`
- Ollama received a common expression-brief schema: `False`
- Local-HF expression prompt serialized a real `MemoryUnit`: `False` (`TypeError`)
- Offline renderer honored authored relationship-stance variants: `False`
- Pre-fix guarded/trusted outputs: `BASE CARE` / `BASE CARE`

The pre-fix system therefore already protected semantic state from renderer swaps, but its language substrates did not all receive the same structured character moment and the deterministic renderer had no deliberate relationship-stance selection contract.

## Post-fix result

Permanent probe passed: `True`.

- common brief schema visible to external renderer: `True`
- explicit semantic decision visible to external renderer: `True`
- explicit history-conditioned relationship stance visible: `True`
- same developed moment produced equal semantic projection under offline and external/frontier-like realization: `True`
- conflicted offline response: `Hello. We can continue, but continuation is not the same thing as repair.`
- trusted offline response: `Hello. I am glad the thread is still intact.`
- conflicted relationship trust/tension: `0.3000000000000001` / `0.36000000000000004`
- trusted relationship trust/tension: `0.7000000000000002` / `0.0`

Targeted verification: `50 passed, 1 skipped in 0.86s`.

Full deterministic Python 3.11 suite: `354 passed, 1 skipped, 1 warning in 28.41s`.

## Contract

`expression-brief-v1` is JSON-safe, noncanonical renderer input. It carries the resolved semantic decision, selected relevant memories, relationship posture, slow developmental state, affect, voice constraints, continuity cues, workspace context, and expression constraints. It explicitly tells a language substrate that it is realizing a character moment rather than authoring identity or history.

Ollama and local-HF now consume this same brief. `ExternalChatRenderer` accepts any host callback that consumes standard chat messages, making the core provider-neutral with respect to OpenAI/ChatGPT, Anthropic/Claude, xAI/Grok, or another remote/local service. A failed external renderer falls back to the same deterministic expression request rather than replacing the character.

The deterministic offline renderer may select optional cartridge-owned relationship variants such as `greeting__conflicted` or `care__trusted`. Generic engine code owns only the stance labels; character prose remains in the cartridge.

## Scope and limitation

This is Tier A internal engineering evidence. The external condition is a deterministic frontier-like callback used to falsify the integration seam, not a claim that ChatGPT, Claude, Grok, or another frontier model has already been shown to preserve perceived identity. Real model swaps and blinded human-visible evaluation are still required for that stronger claim.
