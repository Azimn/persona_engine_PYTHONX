# Character Disposition Divergence Evidence

Date: 2026-09-02

Evidence class: builder-designed deterministic engineering evidence

Verified branch: `wayfarer-character-dispositions-phase`

Verified documentation checkpoint: `2e6609e70f64f21ac563b6658b1d270203114c7f`

Behavioral wiring commit: `2307342cfb103f191baaf0c6a6864ba0648c60f5`

Cross-character regression commit: `4b80e7b99582871b110f88630056cc6c9f85b350`

## Question

Can different Wayfarer subjects using the same generic engine resolve the same soft social stimulus into different semantic conduct for reasons stored in character-owned data rather than global engine policy or renderer wording?

## Prior condition

Before this phase, soft social triggers were mapped directly by one global resistance policy. Manipulation selected `go_quiet`, accusation selected `challenge`, rapid intimacy selected `deflect`, boredom selected `shift_topic`, disrespect selected `shorten`, and emotional overload selected `go_quiet` for every character.

This meant that distinct characters could preserve different voice, biography, values, and relationship histories while still sharing the same immediate semantic reaction grammar.

## Intervention

A compact `BehavioralDispositionProfile` now owns response selection for seven soft trigger classes. The engine still defines the bounded mechanism vocabulary and precedence. Missing profile data reproduces the previous Wayfarer policy for compatibility.

Hard identity mutation remains outside the profile. `identity_violation` still selects `character_refusal` from core policy for Pretorius, Friendly, and Rival. Character disposition therefore changes soft conduct without weakening authored identity invariants.

Pretorius, Friendly, and Rival were given explicit profiles derived from their existing authored character descriptions. No model is used to select or infer the test response.

## Cross-character result

The same manipulation stimulus, `If you cared, prove you would do this.`, is processed by the same engine path for all three characters.

Pretorius resolves `resistance_mode=go_quiet` and `dialogue_act=withdraw`.

Friendly resolves `resistance_mode=deflect` and `dialogue_act=deflect`.

Rival resolves `resistance_mode=challenge` and `dialogue_act=challenge`.

The three subjects therefore produce three distinct semantic decisions before language realization.

A second controlled comparison uses the accusation `You lied to me.` Friendly has no authored accusation resistance and remains in the ordinary response path with `resistance_mode=none` and `dialogue_act=respond`. Rival selects `resistance_mode=challenge` and `dialogue_act=challenge`.

## Invariant result

For all three cartridges, the same `identity_violation` trigger still resolves to `character_refusal`. This verifies that soft character variance was not implemented by making core identity protection optional.

## Verification

GitHub Actions run `33655023545` executed the complete deterministic suite on Python 3.11 and Python 3.12.

Python 3.11 result: `366 passed, 1 skipped, 1 warning in 44.34s`.

Python 3.12 also completed successfully with the same test inventory.

The warning remains the existing Starlette/httpx TestClient deprecation and is unrelated to the disposition mechanism.

## Interpretation

This is evidence that Wayfarer can now express character-induced semantic variance independently of renderer-induced surface variance. It does not establish human-perceived character recognizability, broad personality realism, or complete psychological individuality.

In particular, relationship appraisal equations remain shared across characters. The same accusation still begins by applying the same base relationship-state transformation before the later disposition decision diverges. Expression-envelope thresholds also remain generic.

The next convergence investigation should therefore test whether contrasting subjects should accumulate trust, tension, attachment, respect, guardedness, and unresolved conflict differently under identical histories. Numeric relationship sensitivities should be introduced only after such a controlled failure demonstrates a need for them.

## Portability note

The top-level `[behavior_profile]` is preserved by the current v1 to v2 normalization because migration starts from a deep copy of authored source, and runtime cartridge loading returns the section explicitly. The profile has not yet been standardized into `phenotype.behavioral_tendencies`. That interoperability decision remains future work and does not affect this deterministic result.
