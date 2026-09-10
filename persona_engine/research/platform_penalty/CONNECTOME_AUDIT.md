# Pretorius Persona Connectome v0.1.0 — Donor Audit

Evidence class: **source/artifact audit plus local deterministic engineering evidence**

Artifact audited: uploaded `PersonaConnectome_v0.1.0(1)(2).zip`

The archive was inspected as an experimental donor, not as a proposed replacement runtime. Its complete source tree, Pretorius seed graph, documentation and tests were reviewed. The artifact's own deterministic test suite passed locally: `11 passed`.

## Executive conclusion

The prototype contains one important representational idea worth testing in DUCK:

> an individual can be specified partly by sparse typed organization among already meaningful cognitive/subject structures, rather than only by a flat collection of descriptive traits and prose.

The current implementation should **not** be transplanted wholesale.

Its SQLite store conflates four responsibilities that DUCK/Wayfarer should keep separate:

1. immutable/authored origin semantics and topology;
2. current transient activation;
3. continuing learned structural change;
4. lived memories/relationships/turn history.

The useful donor is therefore the **structural-prior concept**, not the database, node ontology, activation equation or Hebbian rule.

## Artifact architecture

The prototype has:

- typed `Node` and `Edge` records;
- authored node baseline/plasticity/protection metadata;
- lexical/classification/optional embedding seeding;
- bounded multi-hop activation propagation;
- excitatory and inhibitory edge weights;
- motive competition;
- relationship updates;
- Hebbian-like edge strengthening;
- dynamic creation of memory nodes and learned associations;
- a prose-only experiential packet;
- replaceable renderer;
- SQLite persistence and backup;
- deterministic evaluation and validation.

The included Pretorius seed contains:

- 61 nodes;
- 70 edges;
- node types: 11 concepts, 9 relationship dimensions, 7 values, 7 motives, 7 behaviors, 6 styles, 5 emotions, 5 beliefs, 2 identity nodes, 1 self-model node and 1 trigger node;
- 37 protected nodes;
- 57 nodes with nonzero plasticity;
- 48 protected edges;
- 63 edges with nonzero plasticity;
- only 2 inhibitory/negative edges.

Edge kinds include `supports`, `elicits`, `social_bias`, `organizes`, `identity_support`, `decomposes`, `expresses`, `inhibits`, `constrained_by`, `protects`, `evokes`, `threatens`, `attends_to`, `associated` and `reframes`.

That vocabulary demonstrates that the prototype already recognized the inadequacy of one undifferentiated similarity edge. However, several edge kinds still lack sufficiently precise causal/semantic contracts for direct migration.

## 1. Semantic content and first-person prose are conflated

`Node.description` frequently contains semantic content while `metadata.experience` contains first-person renderer-facing prose for the same node. The firewall chooses `metadata.experience`, then description, then label.

This is better than exposing telemetry but still allows English realization text to become part of the cognitive representation.

### DUCK recommendation

Separate:

```text
semantic record
  id / kind / stance / scope / target / authored parameters

from

optional experiential realization
  first-person phrase templates / renderer hints
```

Cognitive activation and decision mechanics should depend on the semantic record. Renderer wording may be revised without changing cognitive topology.

## 2. Authored baseline and current state are not cleanly separated

The activation engine initializes/updates runtime activation from authored node baselines plus prior activation. The relationship updater directly changes node baselines such as `rel.trust.user`.

Thus one field called `baseline` can mean both an authored prior and a mutable current relationship state.

### DUCK recommendation

Use explicit layers:

```text
authored_prior
+ learned/developmental_delta
+ transient_activation
```

Current relationship state remains Wayfarer continuation authority and is referenced by organization; it is not stored as a mutable graph baseline.

## 3. Persona identity and continuing subject identity are conflated

The standalone prototype has persona metadata but no strong distinction equivalent to immutable origin UUID versus continuing subject UUID.

### DUCK recommendation

Require at least:

- `origin_uuid` / `cartridge_uuid` for the authored specification;
- `origin_hash` for exact compiled origin inputs;
- `subject_uuid` for a continuing instantiation, owned by Wayfarer.

Loading Pretorius origin twice must create two subjects unless performing explicit transfer/recovery.

## 4. Provenance and authority metadata are incomplete

Nodes and edges have free-form metadata, but important structural relationships do not uniformly answer why they exist, who authored them, what authority class they have or which evidence changed them.

### DUCK recommendation

A future structural prior should support fields such as:

- `source`;
- `authority_class`;
- `confidence` where meaningful;
- `protected`;
- `evidence_refs` for learned deltas;
- `created_by` / compiler source;
- `schema_version`;
- `lineage`.

## 5. Edge semantics need stricter contracts

The prototype correctly uses named kinds rather than one generic edge. But a numeric `weight` still changes propagation similarly across kinds even when the relation semantics differ.

For example, `supports`, `identity_support`, `social_bias`, `organizes` and `elicits` all propagate scalar influence despite representing different claims.

### DUCK recommendation

Do not let edge labels be decorative.

A future taxonomy should distinguish at least these functional classes when they are required by evidence:

- associative/evocative access;
- excitatory organizational bias;
- inhibitory organizational bias;
- value support/conflict;
- motive relevance;
- appraisal sensitivity;
- procedural prerequisite/tendency;
- evidential reference;
- temporal/causal reference.

Some relations may not participate in spreading activation at all. Evidential and canonical-reference edges should not automatically behave like excitatory synapses.

## 6. Authored weight and learned change are conflated

`PersonaStore.update_edge_weight()` mutates the stored edge weight. The original authored value is not a separately queryable immutable authority once learning changes it.

### DUCK recommendation

Use conceptually:

```text
effective_weight = authored_weight + bounded_learned_delta
```

with separate persistence and lineage. The origin package remains reconstructible and checksum-verifiable.

## 7. Plasticity is too broad for identity-safe development

The prototype's Hebbian rule strengthens unprotected co-active edges and creates new memory associations. The Pretorius seed gives nonzero plasticity to 57/61 nodes and 63/70 edges. Although protection flags reduce risk, plasticity is not strongly tied to evidence type, developmental authority or semantic edge class.

### DUCK recommendation

Plasticity must be:

- bounded by edge/node role;
- disabled or heavily constrained for protected identity anchors;
- provenance-bearing;
- outcome/evidence-aware where possible;
- stored as continuation delta rather than rewriting genesis;
- inspectable and reversible for experimental replay.

Routine co-activation is not sufficient authority to rewrite core values or relationships.

## 8. Relationship nodes currently mix priors and current relationships

Pretorius includes values such as `rel.trust.user = 0.48` in the graph. The relationship updater then modifies those node baselines after praise/confiding/insult/threat.

This is a valid standalone simulation design but conflicts with Wayfarer's existing relationship authority.

### DUCK recommendation

An origin may specify something like:

```text
relationship_prior.default_trust
relationship_sensitivity.betrayal
relationship_sensitivity.repair
```

but actual `trust toward current interlocutor` remains continuation state. Topology may reference that state through a typed port.

## 9. Learned memories should not become origin graph nodes

The learning engine creates `memory.turn.*` nodes directly inside the same canonical graph database.

### DUCK recommendation

Wayfarer remains memory authority. A structural layer can create a reference/association to a memory ID, but does not duplicate memory content as a second canonical memory node.

Distinguish:

- authored biographical events/resources;
- lived episodic memories;
- generated summaries/reflections;
- structural associations referencing those records.

## 10. Motive/emotion nodes mix disposition and transient activation

The graph contains motive/emotion nodes with authored baselines, dynamic activations and plasticity. This makes it unclear whether a number denotes a stable disposition, current regulatory pressure or temporary salience.

### DUCK recommendation

Keep:

- authored motive/appraisal sensitivity in genesis;
- current need/drive/affect in DUCK/continuation state;
- transient activation in the current cognitive cycle.

Topology may alter the coupling among these structures without replacing them.

## 11. Schema and lineage are underdeveloped

The seed is JSON and the database has metadata, but the individual graph is not yet a compiler-produced, lineage-aware origin artifact with exact source checksums and migration semantics comparable to mature `.snp` and DUCK backup engineering.

### DUCK recommendation

If a compiled individual substrate is justified later, include:

- origin schema version;
- compiler version;
- source `.snp` hash;
- organization source hash;
- resource hashes;
- origin UUID;
- parent/version lineage;
- deterministic manifest checksum.

## 12. Extension without engine forks is directionally good

The prototype's data-driven graph can add nodes/edges without `if persona == Pretorius` inside the engine. This is worth preserving.

Condition B should have the same property: generic mechanism code consumes a sparse organization specification and contains no named-character branches.

## 13. Sparse authoring should be preserved

61 nodes and 70 edges are manageable for one research persona, but scaling this directly to many characters could become burdensome if every supported cognitive concept requires explicit authoring.

### DUCK recommendation

Use a rich shared vocabulary/port system with sparse per-character overrides. Absence means generic/default behavior; it should not require hundreds of meaningless zero-valued nodes.

## 14. Circuit-level grouping may be useful later

The graph is mostly flat. Biological connectome work motivates asking whether small functional coalitions are more meaningful than uniform all-to-all connectivity.

### DUCK recommendation

If topology proves useful, allow optional named organization groups such as:

- identity-protection coalition;
- exploratory/epistemic coalition;
- affiliation/repair coalition;
- status/autonomy conflict coalition.

These are engineering groupings, not claims about biological neural circuits. Groups should alter routing/normalization/plasticity only when an ablation demonstrates benefit.

## 15. Inspectability is good but incomplete

The prototype dashboard/exporter makes graph state visible, which is a major strength. Learned changes, however, do not preserve enough causal/evidence provenance to explain why an edge reached its present value.

### DUCK recommendation

Every learned structural delta should be attributable to one or more subject-owned evidence/outcome records where practical.

## Activation-engine critique

The current activation equation is a reasonable toy experiment, not a mechanism to transplant:

```text
initial activation = baseline contribution + previous activation inertia
+ lexical/classification/embedding seeds
+ bounded multi-hop weighted propagation
```

Positive and negative edges both contribute to the same additive delta and values are clamped to `[0,1]`. Inhibitory propagation can therefore only reduce a target indirectly when combined with positive activation, and frontier propagation uses absolute activation change. The prototype also has hard-coded Pretorius-oriented `CLASS_SEEDS`, including specific IDs such as `motive.resist_servility`.

That is acceptable for a single-person research prototype but unsuitable as a generic DUCK individual-organizer without redesign.

Condition B must avoid these named semantic IDs in generic code.

## Learning-engine critique

The Hebbian-style update:

`delta ~= learning_rate * activation(source) * activation(target)`

captures co-activation but not whether the relation was useful, false, harmful, contradicted or causally responsible for an outcome. It can therefore strengthen associations merely because concepts were simultaneously salient.

The connectome/effectome distinction is directly relevant: structural adjacency or co-activation is not sufficient evidence of causal effect.

DUCK should treat authored topology as a structural prior and estimate learned influence from developmental/outcome evidence separately.

## Firewall critique

The connectome firewall is directionally aligned with DUCK: the renderer receives prose categories rather than node IDs/weights/activation telemetry.

However, its validation is largely forbidden-token matching and its cognitive packet takes English `experience` strings directly from graph metadata. DUCK's existing renderer/authority system is more mature and should remain the boundary.

Do not import the connectome firewall in place of DUCK's current renderer isolation.

## Persistence critique

SQLite/WAL and backup are sound local engineering for the standalone prototype. But making this SQLite database canonical inside DUCK would duplicate Wayfarer identity/memory/relationship authority and compete with DUCK's current persistence/backup system.

Do not import it.

If topology is adopted, store immutable compiled origin separately and learned structural overlay in continuing subject state through existing authority/persistence infrastructure.

## Revised hypothesis after audit

The Persona Connectome does **not** currently justify a mandatory graph architecture.

It does justify testing whether the ordinary `.snp` representation lacks a way to express sparse character-specific **relations among mechanisms**.

The clean experimental sequence is therefore:

1. compare A versus representation-neutral deep organization B versus specialized C;
2. only if B adds measurable individuality, compile existing character semantics into a richer origin specification with topology disabled and verify parity;
3. then enable typed topology as an ablation-controlled feature;
4. only if static topology contributes meaningful downstream behavior should learned structural deltas be added.

## Biological analogy boundary

The prototype name does not establish biological equivalence.

The useful analogy is structural:

- shared mechanisms can support different behavior through different organization;
- sparse routing and inhibition can matter;
- sensory-to-motor organization matters at organism level;
- structural connectivity is not identical to causal dynamics.

DUCK nodes are not neurons, edge weights are not synapses, and graph activation is not evidence of a brain or consciousness.
