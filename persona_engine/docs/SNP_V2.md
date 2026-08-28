# Wayfarer `.snp` v2 Contract

This document describes the first portable-source schema implemented by Project Wayfarer. Runtime validation in `persona_engine/core/cartridge.py` and `cartridge_v2.py` is authoritative. `schema/wayfarer_snp_v2.schema.json` is a machine-readable companion for external tooling.

## Identity key

`metadata.entity_uuid` is the permanent subject identifier. `entity_name` is a display label and may change without creating a new subject. Legacy v1 source receives a deterministic UUIDv5 derived from its `entity_id` under the fixed Wayfarer migration namespace. The migration algorithm is versioned as `wayfarer-v1-to-v2-1`.

The migration does not rewrite a v1 file on disk. `load_cartridge()` preserves the source schema and exposes a normalized v2 portable representation in memory.

## Structured self-model

`[self_model]` owns authored ontology. The engine does not enumerate human and artificial as the only possible kinds of subject.

Each `[[self_model.claims]]` entry has a stable `id`, a free semantic `domain`, an unconstrained TOML `value`, authored `certainty`, and one of four mutability classes: `fixed`, `developmental`, `evidence_revisable`, or `uncertain`.

`substrate_awareness` describes whether substrate language is unspecified, opaque, contextual, or explicit. Expression restrictions may exist at self-model or claim level. They are projected into the existing v1 output-validation seam so v2 can ship without creating a second identity authority.

Legacy `[identity].forbidden_self_claims` remains accepted for compatibility. Native v2 source should prefer structured self-model claims.

## Authored phenotype

`[phenotype]` is authored baseline, never current lived state. Its `state_semantics` must be `authored_baseline`.

Stable namespaces are `personality`, `social_behavior`, `values`, `behavioral_tendencies`, `communication`, `preferences`, `capabilities`, `sensory_dispositions`, `embodiment`, `lifestyle_routine`, `self_model`, and `extensions`.

A runtime may ignore a namespace behaviorally, but it must preserve the source data. Unknown external descriptors belong under `phenotype.extensions` until a versioned crosswalk gives them native semantics.

Developmental offsets, learned relationships, memories, commitments, current affect, and other lived state remain outside the cartridge.

## Progressive fidelity

`[portability].minimum_fidelity_level` uses five capability levels:

| Level | Required semantic class |
|---|---|
| 1 | descriptive phenotype |
| 2 | identity and continuity preservation |
| 3 | developmental plasticity |
| 4 | social embedding and authority |
| 5 | longitudinal cross-host continuation |

`preserve_unknown_fields` is mandatory and must be true. `required_namespaces` states which phenotype namespaces a runtime must understand to claim support for this source.

The helper `runtime_supports_portable_source()` performs the minimum-level check without destructively projecting or deleting unsupported data.

## v1 migration

v1 migration is intentionally conservative. It adds a deterministic UUID, maps the existing identity/voice/body/sensory data into descriptive phenotype namespaces, maps `forbidden_self_claims` into v2 self-model expression restrictions, and marks the portable representation with the versioned migration semantics.

It does not invent positive ontology claims. A legacy phrase ban such as `i am an ai` does not prove that the authored subject is human, biological, fictional, or anything else. Rich positive ontology should be authored explicitly in v2.

## MatrAIx interoperability

The first crosswalk is frozen in `schema/matraix_crosswalk_v1.json`. It references `MatrAIx-ai/MatrAIx-Persona-8B` commit `39d850270917db25535dac3f7aa2561732050e82` and the `persona/schema/dimensions.json` blob `742a50ed79f106675311c09f016fff48951f841c`, whose upstream schema declares version `1.0` and 1,290 target dimensions.

Interoperability is lossless before it is clever. Every imported MatrAIx dimension, including dimensions unknown to Wayfarer, is preserved under `phenotype.extensions.matraix.dimensions`. The crosswalk then applies only explicit native projections.

Crosswalk relations are typed as `exact`, `approximate`, `one_to_many`, `many_to_one`, or `unsupported`. Exact mappings may be bidirectional. Approximate mappings are import-only unless a future crosswalk establishes a reversible semantic transform. One-to-many export occurs only when the native views remain consistent. Many-to-one mappings use explicit named bundles. Unsupported dimensions are preservation-only.

This prevents two opposite errors: discarding useful external phenotype information merely because a small runtime does not execute it, and pretending that similarly named concepts are semantically identical when they are not.

`persona_engine.core.matraix_interop` provides deterministic import/export helpers. `tools/matraix_crosswalk.py` exposes the same operations for offline JSON files. No network access or MatrAIx package installation is required at runtime.

The crosswalk is a projection layer, not a new identity authority. Importing `economic_motivation`, for example, may populate authored phenotype description but cannot create an executable goal. Imported demographic fields that lack a native Wayfarer namespace remain preserved external descriptors rather than being forced into unrelated internal state.

## Current boundary

The implemented M2 foundation now includes portable identity, structured self-model, phenotype namespaces, progressive fidelity, versioned v1 migration, and the first frozen MatrAIx interoperability layer. It does not introduce developmental plasticity constants, social authority, the M3 canonical continuity ledger, or cross-host writer leases. Those remain separate milestones with their own acceptance tests.
