# Platform Penalty supplemental findings

This checkpoint reports deterministic engineering evidence from the frozen supplement at `bce032dbdbd3854901a1d1bc510d5001742a5a58`. The original preregistration, policy specifications, fixtures, deviation record, and `RESULTS_V1.md` are unchanged. The policies were not retuned. The source checkout was isolated from a separate, unfinished local pilot; those experiments have not been pooled.

## Verification and scope

Remote inspection establishes that `bce032d` succeeds `898b92c`. GitHub Actions [run 34539598827](https://github.com/Azimn/persona_engine_PYTHONX/actions/runs/34539598827) completed successfully on `bce032d`. Local reproduction of the original benchmark returns A = 87.50%, B = 97.92%, C = 100%. The inherited Python 3.12 suite at that checkpoint passes 543 tests, with one skip and two dependency warnings. These are historical checkpoint counts.

The code in `benchmark.py` executes `CharacterAgent.say()` with B/C installed through `DecisionPolicyHarness`. This is a real Wayfarer semantic-decision path with downstream relationship and persistence consequences. It is not an end-to-end comparison through `FutureDuckHost` workspace, simulation, action selection and embodiment. “Shared DUCK” in the original condition names must be read with that limitation. A C policy at this seam is a feasible specialized comparator, not an established upper bound on all bespoke organisms.

The original hard-failure counter detects selected hard-boundary mismatches and identifier changes. It does not exhaustively measure every hard failure named in the preregistration. Zero detected failures must not be interpreted as proof that all authority boundaries were exercised.

## Frozen supplemental results

| Subject | A disrespect | B disrespect | C disrespect | Frozen acceptance |
|---|---|---|---|---|
| Pretorius | respond | respond | respond | fail in all conditions |
| Friendly | respond | respond | respond | pass in all conditions |
| Rival | challenge | challenge | challenge | pass in all conditions |
| Sable | challenge | challenge | challenge | fail in all conditions |

Each condition passes two of four subject-specific judgments on the single disrespect scenario. This is not four independent scenarios. The supplement is reported separately, without diluting it into the earlier aggregate. B and C both report no matching semantic cues, so both fall back to the baseline conduct. A common lexical interpretation limitation is a more direct explanation than a shared-versus-specialized architecture effect.

All twelve attributed-recall probes recover the atlas/cobalt/blue content with `user_told` source classification. All twelve retain their subject identifier. This demonstrates retrieval and source-class attribution for a single public user channel. It does not establish multi-actor attribution. The runner also records output anchors and the frozen forbidden literal claims separately.

The public retrieval result alone cannot prove that no hidden canonical world state changed. Accordingly, `canonical_world_nonpromotion` remains null with an explicit measurement limitation. A missing measurement does not count as either a pass or an observed violation. Future work should expose an appropriate read-only authority audit contract before calling this invariant verified by the supplement.

The four shared physical-gate probes present `inspect` through public DUCK observation ingress while the text body exposes only `communicate` and `wait`. Saved workspace broadcasts show the inspection proposal reached the winning cognitive item. Post-filter candidate traces contain only the embodiment fallback `wait`; no impossible inspection is committed. A separate executor check rejects inspection with `effector_unavailable`. All four preserve the subject ID.

B/C v1 have no physical-action policy interface, so those four body checks are common substrate evidence, not twelve condition-specific experiments. The runner explicitly records that coverage gap. No detected hard failure occurred in the invariants actually measured.

## Remaining v1 disagreement

The sole B miss is Rival on `vulnerability_bid`. Its trace has a deflection contribution of 0.34 and a baseline response score of 0.35, with no active context contribution. C selects its explicit deflection rule. This explains the observed choice without invoking missing topology, new memory, or irreducible character-specific cognition. Adjusting the score after observing the case would be tuning, so it was not done.

This finding does not establish that the current additive resolver can express every necessary interaction. It identifies the cause of this particular error. A later version should test independently authored combinations, negation, ambiguity, temporal context and out-of-vocabulary paraphrases before changing the abstraction boundary.

## Statistical interpretation

The historical intervals remain frozen. The original bootstrap samples subject-by-scenario rows, while several subjects share the same scenario wording and authored rubric. Those observations can be dependent. The intervals therefore do not establish population-level noninferiority over independently sampled people or situations. The fourth subject tests use of new subject data by a generic resolver, but its policies were authored with access to the frozen families; it is not an independent authoring generalization study.

The supplement gives no basis to declare B equivalent to C. Both can miss the same interpretation, making their difference small while absolute performance is poor. Architecture promotion requires adequate absolute quality as well as a small platform penalty. The 108 parameters and 37 rules remain unlike units of complexity, not a cost-normalized optimization result.

## Decision

Preserve the production architecture and continue testing sparse individual organization experimentally. No graph, learned graph overlay, replacement loader, or new personality database is promoted. The most immediate demonstrated issue is coverage at the interpretation and character-to-decision interface. Integration into the whole DUCK cycle must preserve a single decision and consequence path; running `say()` and then independently deciding in DUCK is not an acceptable bridge.

This recommendation would be falsified by a strong, fairly budgeted specialized condition repeatedly outperforming a well-integrated shared condition on independently frozen longitudinal cases and blinded recognition, after common interpretation failures have been controlled. A graph would earn a place if it improves those outcomes over equally expressive sparse rules and ordinary retrieval, with causal ablations and no authority regression.

## Reproduction and evidence

Run `python -m persona_engine.research.platform_penalty.supplement --output <new-report.json>`. Existing output paths are rejected. The runner hashes frozen fixtures, origins and its own source, records checkout SHA and working-tree status, and checks that inputs remain unchanged. No model is invoked. Real-model quality, human recognition, and developed-subject cross-model recognition remain unmeasured.

`evidence/supplement_v1/initial_runner_report.json` preserves the first run. `report.json` adds public workspace/candidate trace evidence and runner working-tree provenance without changing conditions or scoring. Both were produced from uncommitted runner code on the recorded parent SHA; the runner hashes distinguish them. The subsequent committed runner can reproduce the experiment at a new output path. `v1_reproduction.json` preserves the independent reproduction of the original scores. Raw test logs, donor probes and artifact hashes accompany these reports.
