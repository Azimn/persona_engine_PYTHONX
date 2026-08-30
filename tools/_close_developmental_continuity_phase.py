#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"expected block not found in {path}: {old[:180]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# Remove one unreachable duplicate legacy authority branch exposed during direct
# post-integration review. This does not change behavior.
continuity = ROOT / "persona_engine/core/continuity.py"
replace_once(
    continuity,
    '''    if event_type in {"sensorium", "sensor_observation", "world_fact", "manual_authorized_fact", "world_action_resolution"}:
        return ContinuityAuthority(explicit_actor or "host", "host_world", "world_authority")
    if event_type == "dream_consolidation":
        return ContinuityAuthority(explicit_actor or "character_core", "internal_core", "consolidation_authority", "private")
    if event_type == "state_transition":
''',
    '''    if event_type in {"sensorium", "sensor_observation", "world_fact", "manual_authorized_fact", "world_action_resolution"}:
        return ContinuityAuthority(explicit_actor or "host", "host_world", "world_authority")
    if event_type == "state_transition":
''',
)

progress = ROOT / "persona_engine/docs/WAYFARER_PROGRESS.md"
replace_once(
    progress,
    '''```text
71790eb
Persist minimum-sufficient causal continuity roots
```

The production integration gate completed with:

```text
Focused root/continuity/replay/persistence tests: 36 passed
Full Python 3.11 deterministic suite: 326 passed, 1 skipped, 1 warning
1,000-turn SQLite file: 2,486,272 B
5,000-turn SQLite file: 8,581,120 B
5,000-turn active serialized state: 12,758 B
```
''',
    '''```text
268739c
Preserve slow belief development in canonical continuity
```

The developmental-continuity production gate completed with:

```text
Focused developmental/continuity/replay tests: 18 passed
Full Python 3.11 deterministic suite: 330 passed, 1 skipped, 1 warning
Changed slow belief: live -0.4, restart -0.4, canonical replay -0.4
Separated no-change repair boundaries: live 0.0, canonical replay 0.0
```

The prior root-only storage evidence remains the current persistence-size baseline:

```text
1,000-turn SQLite file: 2,486,272 B
5,000-turn SQLite file: 8,581,120 B
5,000-turn active serialized state: 12,758 B
```
''',
)
replace_once(
    progress,
    '''Outstanding continuity issue: slow `BeliefLedger` consolidation is persistent but its causal replay semantics are not yet established as a first-class root. Do not call M3 semantically complete for developmental history until an explicit consolidation/replay experiment closes that gap.
''',
    '''The slow-belief developmental continuity gap is now closed for the demonstrated `BeliefLedger` rule contract. Pre-fix evidence showed two separately consolidated identity violations reached `trust_user=-0.4`, survived restart, but replayed from input roots alone as `0.0`; consolidating once only at replay end reached merely `-0.2`. It also showed that two one-repair threshold misses separated by consolidation stayed at `0.0`, while grouping the same two repairs before one pass reached `+0.15`. Consolidation boundaries are therefore causal even when no belief value changes.

Production now records a compact `belief_consolidation` root whenever an executed pass consumes evidence relevant to the active belief rules, including threshold misses. Empty passes with no rule-relevant evidence remain housekeeping. Replay regenerates evidence from prior roots, checks the cartridge rule digest and pre-belief digest, executes the pass at the recorded boundary, and checks changed-belief IDs plus the post-belief digest. The belief snapshot, canonical boundary, and evidence-window pruning are committed atomically. Evidence: `evidence/mvi/DEVELOPMENTAL_CONTINUITY.md` and `evidence/mvi/DEVELOPMENTAL_CONTINUITY_FIXED.md`.
''',
)
replace_once(
    progress,
    '''**Next semantic gap:** explicitly test and define slow belief-consolidation continuity/replay. A replay that reconstructs conversational and sensory roots but loses consolidated developmental change is not sufficient for the project goal.
''',
    '''**Developmental replay refinement:** slow belief consolidation is now a demonstrated causal root. A `belief_consolidation` root records rule-relevant pass boundaries, including no-change threshold misses, without restoring verbose state-transition history. Legacy `dream_consolidation` rows remain readable as derived v1 compatibility records.

**Next evidence target:** re-measure persistence with developmental roots active, then choose the next semantic gap from actual longitudinal failure rather than adding another subsystem speculatively. Cross-host single-writer handoff and broader authorized world/action replay remain major roadmap gaps.
''',
)
replace_once(
    progress,
    '''Supported roots include user input, bounded audio/vision observations, M4 `time_advance`, and explicit self-adopted `commitment_adopted` events. Unsupported host-level roots are reported rather than silently claimed as complete.
''',
    '''Supported roots include user input, bounded audio/vision observations, M4 `time_advance`, explicit self-adopted `commitment_adopted` events, and evidence-gated `belief_consolidation` boundaries. Unsupported host-level roots are reported rather than silently claimed as complete.
''',
)

master = ROOT / "persona_engine/docs/WAYFARER_MASTER_PLAN.md"
replace_once(
    master,
    '''This does not close all M3 semantics. Slow belief consolidation remains the important uncovered causal family. Before further persistence compression, establish whether consolidation should be an explicit internal root or be deterministically regenerated from another durable evidence contract.
''',
    '''A follow-up developmental-continuity experiment closed the slow-belief gap for the current rule system. Inputs alone were insufficient: two identity violations consolidated at separate boundaries produced `trust_user=-0.4`, while replay without boundaries produced `0.0` and one consolidation at the end produced only `-0.2`. A threshold-miss control also proved that a no-change pass can be causal because it partitions the evidence window.

Production therefore adds one compact internal root, `belief_consolidation`, only for executed passes that consumed evidence relevant to the active belief rules. The root records rule/belief digests, relevant evidence counts, changed belief IDs, and changed before/after values. It does not restore verbose per-turn state snapshots. Replay regenerates evidence from preceding roots, executes the pass at the recorded boundary, and verifies rule plus belief digests. Empty irrelevant passes remain noncanonical housekeeping. The belief snapshot, canonical root, and evidence pruning commit atomically. Legacy `dream_consolidation` remains a readable derived compatibility family.

Evidence: `evidence/mvi/DEVELOPMENTAL_CONTINUITY.md` (pre-fix failure) and `evidence/mvi/DEVELOPMENTAL_CONTINUITY_FIXED.md` (production verification).
''',
)
replace_once(
    master,
    '''- [x] Expand replay beyond user `input` to demonstrated time, commitment, and bounded sensor roots.
- [ ] Replay time, world, sensor, social, action, consolidation, migration, and authorized state transitions.
''',
    '''- [x] Expand replay beyond user `input` to demonstrated time, commitment, bounded sensor, and slow-belief consolidation roots.
- [x] Preserve demonstrated slow-belief developmental history with typed `belief_consolidation` boundaries and digest-verified replay.
- [ ] Replay the remaining world, social, action, migration, and authorized state-transition families as their contracts are demonstrated.
''',
)

status = ROOT / "persona_engine/docs/CURRENT_STATUS.md"
replace_once(
    status,
    '''```text
71790eb
Persist minimum-sufficient causal continuity roots
```

Latest documentation checkpoint before this status refresh:

```text
84bb1ba
Document root-only continuity production contract
```

The phase-sized Python 3.11 integration gate completed with:

```text
Focused root/continuity/replay/persistence tests: 36 passed
Full deterministic suite: 326 passed, 1 skipped, 1 warning
```
''',
    '''```text
268739c
Preserve slow belief development in canonical continuity
```

The phase-sized Python 3.11 developmental integration gate completed with:

```text
Focused developmental/continuity/replay tests: 18 passed
Full deterministic suite: 330 passed, 1 skipped, 1 warning
```
''',
)
replace_once(
    status,
    '''`canonical_continuity_root_eligible()` governs new durable writes. Current root families include user input/user statement, authoritative time advance, explicit self-adopted commitments, bounded sensor observations, authorized world facts/manual facts, and accepted world-action resolutions.
''',
    '''`canonical_continuity_root_eligible()` governs new durable writes. Current root families include user input/user statement, authoritative time advance, explicit self-adopted commitments, rule-relevant slow-belief consolidation boundaries, bounded sensor observations, authorized world facts/manual facts, and accepted world-action resolutions.
''',
)
replace_once(
    status,
    '''## Important open continuity gap

Slow `BeliefLedger` consolidation is persistent, but its causal replay semantics are not yet established as a first-class continuity root.

Do not declare developmental continuity complete merely because conversational, sensory, commitment, and temporal roots replay correctly. A replay that loses consolidated long-term belief change would fail the project definition even if ordinary dialogue state reconstructs correctly.

The next evidence-driven continuity experiment should force an actual slow-belief change, restart it, export it, replay it from canonical history, and determine the smallest valid causal contract. The likely alternatives are an explicit typed internal consolidation root or deterministic regeneration from another durable evidence contract. The experiment should decide between them rather than assuming either design.

Only after that semantic contract is established should Wayfarer consider further reducing or restructuring the `consolidation_evidence` stream.
''',
    '''## Developmental continuity contract

The pre-fix developmental probe forced a real slow `BeliefLedger` trajectory. Two identity violations consolidated separately moved `trust_user` from `0.0` to `-0.2` to `-0.4`, and ordinary restart preserved `-0.4`. The root-only canonical export contained only the two input events, so current replay reconstructed `0.0`. Replaying both inputs and consolidating only once at the end reconstructed only `-0.2`.

The threshold control was more decisive: one repair followed by a consolidation pass, repeated twice, stayed at `0.0` because each pass consumed a sub-threshold evidence window. The same two repairs grouped before one consolidation reached `+0.15`. A no-change consolidation boundary can therefore alter later development and is genuine causal history.

Production commit `268739c` adds the minimum mechanism supported by that result. An executed pass becomes a compact `belief_consolidation` root only when it consumed evidence relevant to the active belief rules. Threshold misses are recorded; empty irrelevant passes are not. The payload records a rule digest, before/after belief digests, relevant evidence counts, changed IDs, and before/after values for changed beliefs. It is verification/causal metadata, not a full state dump.

Replay regenerates the preceding evidence, verifies the active rule digest and pre-belief digest, executes consolidation at the recorded boundary without writing a duplicate root, then verifies changed IDs and the post-belief digest. Rule mismatch requires explicit migration rather than silently replaying development under different rules. Persistence atomically commits the belief snapshot, canonical consolidation root, and pruning of the consumed evidence window.

Post-fix evidence reproduces `trust_user=-0.4` across live state, restart, and canonical replay. Two separate no-change repair boundaries also reproduce `0.0` in canonical replay. Legacy `dream_consolidation` remains a derived compatibility family.

Evidence:

- `evidence/mvi/DEVELOPMENTAL_CONTINUITY.md`
- `evidence/mvi/developmental_continuity.json`
- `evidence/mvi/DEVELOPMENTAL_CONTINUITY_FIXED.md`
- `evidence/mvi/developmental_continuity_fixed.json`
''',
)
replace_once(
    status,
    '''## Immediate next work

1. Verify the normal Python 3.11/3.12 CI matrix on this final branch state.
2. Run a controlled slow-belief developmental continuity experiment that forces a real `BeliefLedger` change and tests restart/export/replay.
3. Promote only the minimum causal consolidation mechanism supported by that experiment.
4. Re-measure persistence after the developmental replay contract is fixed before optimizing the compact evidence stream further.
''',
    '''## Immediate next work

1. Verify the normal Python 3.11/3.12 CI matrix on the final developmental-continuity branch state.
2. Re-measure persistence with `belief_consolidation` roots active before changing the compact evidence stream further.
3. Use the next controlled longitudinal failure to choose between broader world/action replay, cross-host single-writer handoff, or another minimum-individual requirement; do not add all three speculatively.
4. Keep M7 plasticity calibration separate from this continuity result: replay correctness does not validate the psychological values of belief deltas or thresholds.
''',
)

print("closed developmental continuity phase documentation")
