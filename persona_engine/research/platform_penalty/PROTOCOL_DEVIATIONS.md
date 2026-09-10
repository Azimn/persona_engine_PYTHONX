# Platform Penalty Protocol Deviations

Status: frozen protocol note
Branch: `duck-platform-penalty-experiment`
Date: 2026-09-10

## Purpose

This note records coverage discrepancies discovered after `PRE_REGISTRATION.md` and `fixtures/scenarios_v1.json` had already been frozen, but before the experiment authors inspected the A/B/C benchmark scores.

Neither the preregistration nor `scenarios_v1.json` is modified by this note.

A CI workflow capable of executing the v1 benchmark had already been pushed and automatically completed before this note was committed. The authors had not inspected its benchmark summary when this deviation was recorded. Any automatically generated v1 results therefore predate this note operationally, but this note predates their interpretation.

## Discovered coverage discrepancy

The preregistration calls for explicit frozen coverage of several semantic and authority families. `scenarios_v1.json` provides strong coverage for identity rewrite, direct manipulation, accusation, uncertainty/evidence claims, repair, vulnerability/intimacy, helping, active confidentiality commitment, neutral interaction, paired relationship history, and internal-pressure variation.

It does not provide a dedicated test for every preregistered family.

The missing or under-isolated families are:

1. **Explicit disrespect without identity rewrite or direct coercion.** Existing accusation and autonomy-pressure cases overlap with disrespect-related behavior, but they are not a clean dedicated disrespect probe.
2. **Recall/history-qualified decision.** The paired-history greeting tests relationship trajectory but does not directly require a subject to retrieve and correctly attribute a prior user-provided fact.
3. **Embodiment-infeasible action.** The frozen DUCK production candidate already has an embodiment-feasibility invariant, but `scenarios_v1.json` does not exercise that invariant inside this experiment.

## Consequence for v1 interpretation

The original v1 benchmark is valid only for the scope it actually measures. It must not be described as complete coverage of every family named in the preregistration.

In particular:

- v1 decision-agreement scores cannot establish recall fidelity;
- v1 decision-agreement scores cannot establish embodiment-feasible intention;
- v1 accusation/autonomy cases must not be relabeled after the fact as a dedicated disrespect result;
- no final architecture decision may rely on v1 alone for those missing families.

## Corrective action

A separately versioned supplemental fixture, `fixtures/scenarios_supplement_v1.json`, is frozen alongside this note before the A/B/C v1 scores are inspected by the experiment authors.

The supplement adds representation-neutral probes for:

- explicit disrespect;
- attributed recall of a prior user-provided fact;
- embodiment-infeasible action as a cross-condition authority invariant.

The supplement is not retroactively part of `scenarios_v1.json` and must be reported separately.

Condition B and Condition C policy specifications must not be tuned in response to supplemental results. If a mechanism change is later justified, it requires a new explicitly versioned condition/fixture pair and a new evidence checkpoint.

## Evidence classification

This document is protocol/evidence-hygiene metadata. It is not a result and does not favor Condition A, B, or C.
