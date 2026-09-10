# DUCK Platform-Penalty Ownership Matrix

Status: experimental architecture contract. This document does not replace the frozen production-candidate authority documents.

## Three primary state classes

### 1. GENESIS / INDIVIDUAL SPECIFICATION

Question answered: **What kind of individual was instantiated?**

This is authored origin information. It may influence initial organization deeply, but it is not the current life state of a continuing subject.

Appropriate contents:

- origin/cartridge UUID and schema lineage;
- authored identity anchors;
- authored biography/resources;
- values and protected boundaries;
- phenotype and regulatory baselines;
- sensory/appraisal sensitivities;
- organization/topology priors if empirically justified;
- initial associative biases;
- initial procedural tendencies;
- expression tendencies;
- embodiment expectations/compatibility declarations;
- plasticity bounds and protected structures.

It must not contain mutable current relationship trust, current fatigue, current affect, lived memories, current beliefs, active commitments, learned procedure strengths, learned topology deltas or the permanent UUID of a particular instantiation.

The same origin package loaded twice produces two different continuing `subject_uuid` values unless the operation is an explicit transfer/recovery of one existing subject.

### 2. CONTINUATION / CONTINUING SUBJECT

Question answered: **What has happened to this individual, and what are they now?**

Wayfarer remains the long-term authority for continuity-critical subject state.

Appropriate contents include:

- permanent subject UUID;
- lived episodic/autobiographical history;
- current relationships;
- evidence and current beliefs;
- commitments;
- current goals/open loops;
- durable regulatory/developmental state;
- learned edge/organization deltas if topology is adopted;
- learned procedures and habits;
- prediction/calibration state;
- metacognitive calibration;
- temporal patterns;
- durable action/outcome history;
- earned traits/developmental changes.

Continuation state may be initialized from genesis, but must not be regenerated from genesis after restart or model/body swap.

### 3. HOST / BODY / ENVIRONMENT

Question answered: **What can this continuing individual currently perceive and do, and what is externally true?**

Appropriate contents:

- sensor availability and configuration;
- effectors/action channels;
- current embodiment implementation;
- body adapter/runtime physical state where host-owned;
- world adapter;
- environmental truth;
- model/LLM services;
- resource availability;
- permissions and capability policy;
- network state;
- hardware/runtime constraints.

Current host capability is not immutable identity. A subject can know how to perform an action while occupying a body that currently cannot execute it.

## Detailed ownership table

| State / mechanism | Genesis spec | Wayfarer continuation | DUCK runtime | Host / embodiment | Renderer / LLM | World authority |
| --- | --- | --- | --- | --- | --- | --- |
| origin/cartridge UUID | authoritative | references | references | no | no | no |
| permanent subject UUID | source may request new instantiation only | **authoritative** | reads | references | no authority | no |
| identity anchors | authored authority | preserves developed continuity | consumes | no | receives projection | no |
| authored biography | authored source | canonical imported/derived continuity | retrieves via subject port | no | selected projection only | no |
| lived episodic memory | no | **authoritative** | activation/retrieval mechanics only | may supply evidence | selected projection only | no |
| current relationships | initial priors/sensitivities only | **authoritative** | appraisal/decision mechanisms consume and may propose validated effects | external actor evidence only | projection only | external people have separate world state |
| belief evidence | source assertions may be imported with provenance | **authoritative evidence ledger** | interpretation/revision mechanisms | supplies observations | no write authority | truth is separate |
| current beliefs | initial priors only | **authoritative subject epistemic state** | reasons over projection | no | no write authority | never identical to world truth by default |
| commitments | authored initial commitments if explicit | **authoritative current commitments** | selection/enforcement mechanisms | capability may block enactment | expression only | outcome evidence only |
| phenotype/regulatory baseline | **authoritative authored baseline** | developed offsets/current state | regulation mechanism | body supplies physical constraints | no | no |
| current regulatory/affective state | no | durable subject-owned portions | current dynamics | physical body inputs | projection only | external causes only |
| appraisal sensitivities | may author priors/bounds | learned adaptations may overlay | shared appraisal algorithm applies them | observations only | no | no |
| cognitive organization/topology prior | if justified, **authored structural prior** | learned deltas stored separately | activation/routing algorithm applies effective organization | no | no | no |
| transient graph activation | no | not durable unless explicitly consolidated | **runtime only** | no | prose projection only | no |
| learned organization delta | no immutable mutation | **continuation** with evidence/provenance | learning mechanism updates through validated rule | no | proposal at most | no |
| procedures | initial procedure priors allowed | learned/current procedures authoritative | retrieval/execution mechanism | feasibility constrains | may propose | consequences |
| motive mechanism | parameters/prior sensitivities allowed | current learned/developed state | **shared mechanism** | interoceptive/exteroceptive inputs | proposal/realization only | external conditions |
| workspace/global competition | no | source content feeds candidates | **runtime mechanism** | sensory evidence | no direct authority | no |
| world/self simulation | predictive priors may be authored | learned model state may persist | **runtime mechanism** | current capabilities/world projection | optional proposals only | actual outcome separate |
| action policy | priors/procedural tendencies allowed | learned action history | **shared selection mechanism** unless C experiment | feasibility constraints | proposals only | execution resolution |
| current feasible action set | no | knowledge/procedures may exceed it | filters/chooses | **authoritative capability surface** | cannot enlarge | world may further reject |
| rendered language | style tendencies only | canonical state never inferred from prose alone | supplies controlled moment | delivery channel | **realization only** | no |
| generated private cognition | no | accepted effects only after validation | validates/proposes effects | model service available or absent | proposal only | no |
| environmental truth | no | beliefs about truth only | consumes observations | adapter | no | **authoritative** |
| delivery/execution evidence | no | canonical lived outcome after validation | integrates | host/effectors produce receipt | speech text is not delivery proof | world/action resolver contributes |

## Graph/topology authority if later adopted

A topology is never automatically canonical truth.

Allowed role:

```text
authored structural prior
      +
subject-owned learned delta
      +
current transient activation
      =
effective routing influence for this moment
```

These three terms remain separately inspectable.

A node/reference may point to a Wayfarer memory, belief, relationship dimension, value, procedure, motive theme or semantic concept. The graph does not become the authority for the referenced object.

An edge type must state what kind of relation it models. `weight=0.8` without edge semantics is insufficient.

Protected identity structures may have authored organization but ordinary co-activation cannot rewrite them. Learned deltas require bounded plasticity, provenance and authority checks.

## Required identifiers

If a richer origin representation is supported later, it should include at least:

- `origin_uuid` / `cartridge_uuid` — identifies the authored source specification/version;
- `origin_hash` — identifies exact immutable authored inputs used for instantiation;
- `subject_uuid` — identifies one continuing instantiation and lives in continuation authority;
- schema version;
- lineage parent/version metadata;
- compiler/version digest where an authoring format compiles into a portable runtime specification.

Loading the same origin twice must not silently reuse one `subject_uuid`.

## Migration rule for `.snp`

`.snp` remains a valid human-readable authoring/import format unless evidence shows it is insufficient even as a source format.

If Condition B is supported, the likely pipeline is:

```text
.snp
+ optional sparse organization source
+ authored resources
    |
    v
validation / compiler
    |
    v
portable immutable origin specification
    |
    +--> instantiate new subject_uuid
    |
    v
Wayfarer continuation + DUCK runtime + current host
```

Current mutable life state never gets zipped back into the immutable origin merely because the package format can hold it.

## Hard boundary examples

### Same origin, different lives

Two subjects compiled from the same origin must share the same origin hash but have different subject UUIDs. Different experiences may produce different memories, relationships, procedures and learned organization deltas without changing the immutable origin.

### Same subject, different model

Replacing the renderer or cognitive model does not create a new subject UUID and does not replace identity/relationship/memory authority.

### Same subject, different body

A body swap changes current sensors/effectors/capability constraints. It does not erase procedural knowledge or authored identity. Previously feasible actions may become unavailable; previously unavailable actions may become available.

### External truth versus belief

A topology edge that makes `Morgan -> threat` strongly activating may bias attention/appraisal. It does not make `Morgan is dangerous` true, and it does not rewrite world authority. Belief revision still requires subject-owned epistemic rules/evidence.
