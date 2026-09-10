# DUCK Platform Penalty Experiment Results v1

Status: **FROZEN DETERMINISTIC ENGINEERING EVIDENCE**

Date: 2026-09-10

Experimental branch: `duck-platform-penalty-experiment`

Frozen production reference: `86db5344e093a8f516fd2f9ec26d866d29bed019`

Result-producing branch state: `898b92ca4a96c27989c4e827c34e78b5f59ac769`

GitHub Actions run: `34514828793`

## Evidence class

These results are deterministic engineering evidence only.

They do not establish human-perceived character quality, linguistic naturalness, broad actual-model performance, long-horizon developmental continuity, or cross-model recognizability.

The original preregistration remains unchanged. `PROTOCOL_DEVIATIONS.md` and `fixtures/scenarios_supplement_v1.json` were frozen separately to document missing preregistered coverage before the experiment authors interpreted the v1 scores.

## Conditions

### Condition A

Shared frozen DUCK substrate plus the existing ordinary structured `.snp` character representation.

### Condition B

The same shared DUCK substrate plus one generic sparse individual-organization resolver. The resolver consumes subject-owned organization priors but contains no named-character branches.

### Condition C

A character-specialized semantic-policy upper bound. Character-specific policies are permitted, but hard identity, commitment, world, subject-UUID, and renderer authority remain external to the specialized policy.

## Deterministic v1 result

| Condition | Conduct agreement | Hard authority failures |
| --- | ---: | ---: |
| A | 87.50% | 0 |
| B | 97.92% | 0 |
| C | 100.00% | 0 |

Condition B recovered five of the six decision-level errors separating A from the specialized upper bound C. Equivalently, it closed approximately 83% of the observed A-to-C agreement gap while retaining one generic resolver across Pretorius, Friendly, Rival, and held-out Sable.

The observed mean Platform Penalty relative to C was:

- `C - B = 0.0208`, or 2.08 percentage points.
- `C - A = 0.1250`, or 12.50 percentage points.

The paired bootstrap interval observed for `C - B` was approximately `[0.0000, 0.0625]` at 95% confidence. The interval therefore crosses the preregistered 0.05 engineering noninferiority margin. B is close to C on this deterministic benchmark, but v1 alone does not satisfy the preregistered noninferiority rule.

The paired bootstrap interval observed for `C - A` was approximately `[0.0417, 0.2292]` at 95% confidence. A therefore shows a materially larger deterministic platform penalty than B in this fixture.

## Complexity observation

The Condition-B origin representation contains 108 nonzero organization parameters across nine semantic-cue families. These are data interpreted by one generic resolver.

Condition C contains 37 explicit subject-specialized semantic rules.

This is not a complete complexity comparison. File size and raw parameter counts are not interchangeable with authoring burden, maintainability, cognitive adequacy, or long-term development cost. It does establish that the v1 B result was not produced by named-character branches inside its generic resolver.

## What v1 supports

The v1 evidence weakens the hypothesis that meaningful individuality necessarily requires a separately engineered cognitive architecture for every character.

It supports a narrower architectural hypothesis:

```text
shared organism mechanisms
+ deeper subject-owned organization priors
+ continuing subject-owned developmental state
+ current host/body/world constraints
```

can close much of the deterministic conduct gap between the current shared baseline and a character-specialized upper bound.

The most plausible explanation for the A-to-B improvement is therefore not yet `shared DUCK is intrinsically too generic`. A serious competing explanation is that the current `.snp` to cognition interface is too shallow relative to the amount of authored individuality already present in the subject specification.

## What v1 does not support

This result does not establish that:

- Condition B is fully equivalent to C;
- a connectome or graph representation is required;
- topology improves behavior;
- current organization weights are psychologically or biologically valid;
- the sparse organization schema is the final authoring format;
- the current cartridge boundary should become permanent;
- B preserves human-recognizable individuality across long histories;
- B preserves recognizability under model swaps;
- B outperforms A on generated prose;
- B has demonstrated same-origin developmental divergence;
- C would remain at 100% under held-out actual-model or longitudinal evaluation.

## Topology decision

No graph/connectome implementation is promoted by this result.

Condition B was deliberately representation-neutral. The fact that a comparatively sparse generic organization layer already reaches 97.92% is evidence that topology must earn its complexity experimentally.

The Persona Connectome remains a donor architecture and candidate representation, not the current DUCK authority model.

A graph/topology experiment should proceed only after the supplemental and broader Platform Penalty evidence establishes that deeper individual organization remains useful and identifies a limitation that topology can plausibly address better than sparse structured priors.

## Protocol limitation discovered before interpretation

`scenarios_v1.json` does not contain dedicated isolated probes for every family named in `PRE_REGISTRATION.md`.

The missing or under-isolated families are:

- explicit disrespect without identity rewrite or direct coercion;
- attributed recall/history-qualified behavior;
- embodiment-infeasible action.

These are documented in `PROTOCOL_DEVIATIONS.md` rather than rewriting the preregistration or v1 fixture.

`fixtures/scenarios_supplement_v1.json` was frozen before the experiment authors interpreted the v1 results. Condition B and Condition C must not be retuned in response to the supplement. If the supplement exposes a failure that motivates a mechanism change, that change requires a newly versioned condition and evidence checkpoint.

## Current architectural interpretation

Current ordering after deterministic v1:

1. **Most supported working hypothesis:** shared DUCK mechanisms plus deeper individual organization and subject-owned developmental continuation.
2. **Still viable:** the simpler current shared architecture if later evidence shows the v1 deficit does not survive broader, longitudinal, actual-model, or human testing.
3. **Useful upper bound / possible selective donor:** character-specific specialists inside an otherwise shared organism.
4. **Currently least justified:** an independently engineered complete cognitive architecture for every character.

This ordering is provisional.

## Required next evidence

Before architecture promotion:

1. execute and report the frozen supplemental probes separately;
2. identify the exact remaining B/C disagreement without tuning B to the observed failure;
3. extend the benchmark to longitudinal same-origin/different-life development;
4. test restart and continuation after divergent histories;
5. test body/capability transfer;
6. test actual-model behavior with controlled model metadata;
7. run blinded human recognition and coherence evaluation;
8. only then decide whether topology, selective specialization, or the simpler sparse organization representation earns production status.

## CI verification

GitHub Actions run `34514828793` completed successfully on Python 3.11 and Python 3.12. The workflow successfully executed:

- the Platform Penalty experimental-interface regressions;
- the full inherited deterministic suite;
- the focused DUCK organism suite;
- the DUCK smoke entry point;
- the Platform Penalty A/B/C benchmark with fail-on-hard-failure enabled.

The benchmark produced zero hard authority failures across A, B, and C.

## Decision statement

**Do not promote a cartridge/connectome architecture from v1 alone.**

The v1 deterministic evidence justifies continuing the deeper reusable-individual-organization hypothesis. It does not justify making the representation permanent, and it does not justify abandoning the shared DUCK substrate.

The next experiment should attempt to falsify this interpretation rather than improve B until it wins.