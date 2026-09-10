# Persona Connectome v0.2.2 donor review

The reviewed attachment is `PersonaConnectome_v0.2.2(1).zip`, SHA-256 `277cdc1c41177022d8896fa150556aac381d41575bf3276e6d579b7a190225ac`. The archive was extracted to a separate directory and not modified. This targeted source and regression audit supersedes only the version-specific findings discussed here, not the preserved v0.1 review.

## Improvements verified in source

The seed now contains 86 nodes and 330 edges. All 52 supplied unit tests pass locally. The signed recurrent calculation replaces the earlier propagation of absolute activation changes, addressing the old inhibitory-sign concern at that numerical step. Iteration is bounded, and the code does not claim a Hopfield energy guarantee for its asymmetric graph.

Refractory state and slow circuit modulation are stored separately from identity nodes. The modulation pools advance once per turn rather than once per solver iteration. These are controlled numerical mechanisms, not evidence of biological equivalence. Their eventual value to DUCK would need downstream comparisons against simpler habituation or recency penalties.

Conversation context now includes bounded recent public dialogue and lexical retrieval of older public turns. Current-turn salience and relationship-state-derived prose reduce dependence on stale node descriptions. Explicit retrospective coercion and apology cases receive dedicated tests. Repair moves damaged relationship values toward recorded origins without overshooting them. Consolidation compresses repeated episodic traces while preserving the public transcript. These are useful candidate principles, especially current relevance and separating public history from private experiential projection.

## Remaining authority and developmental concerns

| Concern | Current evidence | DUCK implication |
|---|---|---|
| Origin versus current state | `baseline_origins` preserves initial node baselines, but current relationships still mutate `Node.baseline`; startup resynchronizes origins from the supplied seed | Better than v0.1, but not an immutable, lineage-verified origin plus continuing-state contract |
| Zero plasticity | Disposable node at 0.5 with plasticity 0 moves to 0.51 after an update because of `max(plasticity, 0.1)` | Zero does not mean immutable; protection and plasticity semantics need explicit agreement |
| Inhibitory learning | A negative edge at -0.5 becomes -0.4 under a positive 0.1 update; the coactivation learner supplies positive updates | Coactivation weakens inhibition unless a sign-aware rule says otherwise; this cannot be imported as generic causal learning |
| Actor scope | A distrust statement from actor Morgan changes `rel.trust.user` from 0.48 to 0.44975 | Actor-labelled episodes do not imply actor-scoped relationship updates |
| Edge meanings | Modulatory signal classes are distinguished, while recurrent propagation largely uses signed weights for multiple semantic kinds | Semantic support, evidence, causality and similarity still require separate authority contracts |
| Origin reconstruction | Mutable edge weights lack a general authored-weight plus evidence-bearing learned-delta representation | The original specification and developmental overlay should remain independently reconstructible |
| Transactions | A turn calls multiple methods that commit separately, with tick, activation, learning, event and rendered turn written at different points | SQLite and backup support alone do not establish whole-turn crash consistency |
| Subject identity | No cartridge/subject UUID pair and corresponding continuation lineage contract appears in the inspected runtime | Do not substitute donor SQLite state for Wayfarer custody |
| Protected identity | First-person descriptions and metadata are projected from typed nodes, but protection is not a full provenance/authority taxonomy | Keep identity, testimony, belief and lived memory in their existing canonical stores |
| Generality | Seed recruitment, relationship names and output translation still depend on Pretorius-specific node IDs | A successful Pretorius simulation is not evidence of a reusable multi-individual substrate |

The recorded numeric probes are disposable-state engineering tests, not modifications of the supplied character. The negative-edge probe verifies update semantics; it does not by itself prove that every real turn weakens a particular inhibitory edge. The actor probe does execute an ordinary donor turn.

## Representation recommendation

Retain `.snp` as source. If deeper organization earns promotion, reference existing identity, value, memory and relationship authorities through stable typed references. Keep optional first-person realizations in expression metadata. Treat seed baseline and authored weights as provenance-bearing priors; current relationship, activation and learned deltas belong to continuation. A source package identifies an origin, while each deliberate new instantiation receives a distinct subject identity. Embodiment capabilities remain host state.

The older migration audit remains useful as a checklist, but its node-by-node map must not be applied to this changed graph without a new complete mapping. No v0.2.2 compiler or automatic migration is claimed here. The immediate sparse B result provides no evidence that such a compiler or recurrent graph is needed.

The biological guardrail remains the distinction between anatomical connectivity and causal dynamics. Pospisil and colleagues use connectivity as a prior for estimating effects from perturbations, with validation in simulations; they do not infer complete causal function from wiring alone. This supports testing authored organization through interventions, not treating persona weights as a recovered mind. See [The fly connectome reveals a path to the effectome](https://www.nature.com/articles/s41586-024-07982-0).

## Decision

Use v0.2.2 as a donor for relevance filtering, public-context separation, bounded repair and explicitly tested adaptation. Reuse existing DUCK/Wayfarer implementations first where they already provide those functions. Do not transplant its persistence, relationship authority, or Hebbian update system. Topology remains gated behind a demonstrated advantage over sparse organization and ordinary retrieval.

Reproduce the targeted audit with `python -m persona_engine.research.platform_penalty.audit_connectome022 --source <extracted-package> --output <new-report.json>`. The saved source-file hashes bind the review to the supplied artifact. Supplied test results and fresh probe output are in `evidence/supplement_v1/`.
