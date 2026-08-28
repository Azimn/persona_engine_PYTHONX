# Minimum Viable Individual Ablation Plan

Wayfarer must not collapse `minimum character` and `minimum renderer` into one experiment. They are separate engineering questions and require separate ablation studies.

## Study A: character-kernel ablation

Question:

> How much deterministic character machinery can be removed while the same individual remains recognizably continuous and behaviorally attributable to itself?

Renderer is held fixed across every condition.

Candidate ablations include body state, affect/pressure, relationship state, rich memory, interpretation, habits, symbols, consolidation/dream mechanisms, private cognition, proactive/offscreen life, phenotype richness, social authority, commitments, and world model.

Primary measurements:

- identity continuity,
- relationship differentiation,
- autobiographical continuity,
- belief/commitment stability,
- believable longitudinal change,
- social-pressure behavior,
- decision consistency,
- human recognizability,
- CPU/RAM/storage savings.

A negative result in this study is attributed to character machinery because renderer capability is controlled.

## Study B: renderer-capability ablation

Question:

> Holding the exact same character state and decision machinery fixed, how little language-generation capability is needed before human-visible believability breaks down?

Character kernel and scenario history are held fixed.

Candidate renderer conditions include:

- full frontier renderer,
- larger local model,
- small local model,
- sub-1B SLM where practical,
- statistical/n-gram lexicalizer,
- deterministic compositional renderer.

Primary measurements:

- preservation of resolved semantic intent,
- unsupported-claim rate,
- consistency-layer severity profile,
- repetition/canned-language rate,
- conversational naturalness,
- character recognizability,
- latency,
- memory/compute cost.

A negative result in this study is attributed to expression bandwidth because canonical character machinery is controlled.

## Study order

Run Study A first with one stable renderer, then Study B with one frozen character kernel. Only after the main effects are understood should Wayfarer run factorial combinations such as `reduced character kernel + tiny renderer`.

This avoids a common attribution error where poor language makes a strong character architecture appear weak, or a powerful language model masks a weak character substrate.

## Release artifact

M19 should eventually publish two reports rather than one:

- `MINIMUM_CHARACTER_SUBSTRATE.md`
- `MINIMUM_RENDERER_SUBSTRATE.md`

A later `MINIMUM_VIABLE_INDIVIDUAL.md` may synthesize them into deployment tiers, but it must preserve the distinction between character cost and renderer cost.
