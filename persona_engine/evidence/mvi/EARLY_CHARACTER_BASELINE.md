# Early Minimum Character Substrate Baseline

Scenario: `early-mvi-a1`  
Renderer control: deterministic offline renderer  
Cartridge: `pretorius.snp`

This is an early diagnostic Study-A baseline, not a final Minimum Viable Individual result. A zero difference means only that this fixed scenario did not expose a contribution.

| Condition | Decision turns changed | Risk buckets changed | Relationship L1 | Pressure L1 | Retrieval delta | Interpretation delta | Final memory delta | Digest equal |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| memory_retrieval_off | 0 | 0 | 0.000000 | 0.000000 | -30 | 0 | -1 | no |
| interpretation_off | 0 | 0 | 0.000000 | 0.000000 | 0 | -6 | 0 | yes |
| symbols_off | 0 | 0 | 0.000000 | 0.000000 | 0 | 0 | 0 | yes |
| habits_off | 0 | 0 | 0.000000 | 0.000000 | 0 | 0 | 0 | no |
| body_dynamics_off | 4 | 6 | 0.040000 | 1.675000 | 0 | 0 | -399 | no |
| clean_seams_combined_off | 4 | 6 | 0.040000 | 1.675000 | -30 | -6 | -399 | no |

## Method guardrails

The renderer, cartridge, user identifier, scenario order, and explicit elapsed-time steps are held fixed. Only the named character-kernel seam changes. This baseline intentionally begins with cleanly removable seams rather than deeply entangled relationship or pressure machinery.

Do not delete a subsystem because one row shows zero decision divergence. Expand the scenario or run human-visible evaluation first. The purpose of this artifact is to identify which longitudinal failures are observable enough to justify the next causal mechanism.
