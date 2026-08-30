#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "persona_engine" / "docs"


def replace_section(path: Path, start: str, end: str, replacement: str) -> None:
    text = path.read_text(encoding="utf-8")
    a = text.index(start)
    b = text.index(end, a)
    path.write_text(text[:a] + replacement.rstrip() + "\n\n" + text[b:], encoding="utf-8")


def insert_after_once(path: Path, anchor: str, addition: str, marker: str) -> None:
    text = path.read_text(encoding="utf-8")
    if marker in text:
        return
    if anchor not in text:
        raise SystemExit(f"anchor not found in {path}: {anchor!r}")
    text = text.replace(anchor, anchor + "\n\n" + addition.strip(), 1)
    path.write_text(text + ("" if text.endswith("\n") else "\n"), encoding="utf-8")


progress = DOCS / "WAYFARER_PROGRESS.md"
text = progress.read_text(encoding="utf-8").replace("Last updated: 2026-08-29", "Last updated: 2026-08-30", 1)
progress.write_text(text, encoding="utf-8")
replace_section(
    progress,
    "## Latest implemented checkpoint",
    "## Baseline history",
    '''## Latest implemented checkpoint

Current production/evidence head before this documentation update:

```text
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

The canonical-root projection first demonstrated that a mixed 21-event history could be reduced to 9 causal roots while preserving the exact semantic replay digest, cold biography, submitted host context, commitment continuity, subject time, and bounded sensory replay. Serialized event bytes fell 73.27% and payload bytes fell 82.73% in that experiment.

Production now follows the same causal contract. New v1 runtime histories retain minimum-sufficient roots rather than routine regenerated `state_transition` and `sensorium` records. Historical v1 histories containing those derived rows remain valid, importable, and replayable; replay skips the derived records rather than double-applying them. Rich derived packets remain available in the bounded diagnostic journal.

The 1,000-turn production storage probe reduced durable continuity from approximately 3.01 rows per exercised turn to 1.004. Canonical input payloads averaged 75.75 B and exact canonical/diagnostic payload duplication was zero. The complete database fell from the previous approximately 6.78 MB measurement to 2.49 MB.

The 5,000-turn production plateau remained behaviorally green. Resident memory remained seven objects, the same subject survived restart, unresolved history continued to qualify trust, cold lighthouse recall worked, the non-disclosure commitment still declined disclosure, identity rewrite still produced `protect_boundary`, and genuine repair returned relationship conflict to zero. Active state changed only +205 B between turn 250 and turn 5,000. Database growth over that interval was 7,438,336 B instead of the pre-persistence-cleanup 62,939,136 B.

Outstanding continuity issue: slow `BeliefLedger` consolidation is persistent but its causal replay semantics are not yet established as a first-class root. Do not call M3 semantically complete for developmental history until an explicit consolidation/replay experiment closes that gap.
''',
)
insert_after_once(
    progress,
    "## M3 canonical continuity ledger and replay",
    '''### 2026-08-30 root-only production contract

**VALIDATED AND IN PRODUCTION.** New runtime writes distinguish causal biography from regenerated verification evidence. `canonical_continuity_root_eligible()` governs new durable writes; the broader historical validator remains for v1 compatibility. Production `input` roots store user text plus only context actually submitted by the host. Classifier output, canonicality flags, memory-type metadata, derived body/world context, routine `state_transition`, and routine `sensorium` remain diagnostic rather than permanent biography.

Evidence:

- `evidence/mvi/CANONICAL_ROOT_PROJECTION.md`
- `evidence/mvi/ROOT_ONLY_CONTINUITY_STORAGE.md`
- `evidence/mvi/ROOT_ONLY_PRODUCTION_PLATEAU.md`

The representation change kept `CONTINUITY_SCHEMA_VERSION = 1.0` because old and new streams remain mutually readable at the interchange level. This is a narrower write policy and payload schema refinement, not an incompatible bundle format change.

**Next semantic gap:** explicitly test and define slow belief-consolidation continuity/replay. A replay that reconstructs conversational and sensory roots but loses consolidated developmental change is not sufficient for the project goal.''',
    "### 2026-08-30 root-only production contract",
)

master = DOCS / "WAYFARER_MASTER_PLAN.md"
insert_after_once(
    master,
    "Goal: make biography replayable and inspectable without over-engineering the current threat model.",
    '''## Validated production refinement, 2026-08-30

The canonical-root projection and production integration established a minimum-sufficient write policy for ordinary continuity. New runtime histories persist causal roots while routine regenerated `state_transition` and `sensorium` packets remain bounded diagnostics. Historical v1 streams containing derived rows remain valid and replayable, so the interchange schema remains 1.0.

Measured production evidence:

- mixed-history projection: 21 canonical events -> 9 roots, 73.27% fewer serialized event bytes, 82.73% fewer payload bytes, identical semantic replay digest;
- 1,000-turn production: 1.004 canonical rows/turn, 2,486,272 B SQLite file, 75.75 B average canonical input payload;
- 5,000-turn production: 8,581,120 B SQLite file, approximately 12.8 KB active state, all restart/history/recall/commitment/identity/repair contracts green.

This does not close all M3 semantics. Slow belief consolidation remains the important uncovered causal family. Before further persistence compression, establish whether consolidation should be an explicit internal root or be deterministically regenerated from another durable evidence contract.''',
    "## Validated production refinement, 2026-08-30",
)
# Mark only tasks whose current implementation has actually earned completion.
text = master.read_text(encoding="utf-8")
for old, new in [
    ("- [ ] Define `ContinuityEvent`.", "- [x] Define `ContinuityEvent`."),
    ("- [ ] Store canonical events append-only.", "- [x] Store canonical causal-root events append-only."),
    ("- [ ] Make snapshots derived caches rather than the only truth source.", "- [x] Make snapshots explicit caches rather than the only continuity authority for demonstrated subject-owned families."),
    ("- [ ] Detect missing/reordered/duplicated sequence entries.", "- [x] Detect missing/reordered/duplicated sequence entries."),
    ("- [ ] Add deterministic state digest comparison.", "- [x] Add deterministic state digest comparison."),
    ("- [ ] Expand replay beyond user `input`.", "- [x] Expand replay beyond user `input` to demonstrated time, commitment, and bounded sensor roots."),
    ("- [ ] Add complete event-tail export/import.", "- [x] Add validated event-tail export/import for the current v1 stream contract."),
    ("- [ ] Add schema migration tests.", "- [x] Add v1 migration/backfill and old-derived-row compatibility tests."),
    ("- [ ] Add corruption/incomplete-log tests appropriate to ordinary local failure.", "- [x] Add ordinary local continuity integrity/gap validation tests."),
]:
    text = text.replace(old, new, 1)
master.write_text(text, encoding="utf-8")

readme = ROOT / "README.md"
replace_section(
    readme,
    "## Current Verified Test State",
    "## Important Baseline Regression That Wayfarer Already Fixed",
    '''## Current Verified Test State

Latest completed phase-sized production integration:

- Commit: `71790eb` (`Persist minimum-sufficient causal continuity roots`)
- Focused root/continuity contracts: `36 passed`
- Full Python 3.11 deterministic suite: `326 passed, 1 skipped, 1 warning`
- 1,000-turn production SQLite measurement: `2,486,272 B`
- 5,000-turn production SQLite measurement: `8,581,120 B`
- 5,000-turn active serialized state: approximately `12.8 KB`

The remaining warning is the existing Starlette/httpx TestClient deprecation. The normal Python 3.11/3.12 Wayfarer CI matrix should be checked after this documentation pass before quoting a newer branch-wide two-version result.

Run locally with:

```bash
python -m pytest persona_engine/tests -q
```

The historical `171 passed, 1 skipped` figure in the old documentation was stale. The true frozen baseline and its failures are preserved in `persona_engine/docs/WAYFARER_BASELINE.md`.
''',
)
text = readme.read_text(encoding="utf-8")
text = text.replace(
    "The next M1 task is to remove remaining universal AI/language-model ontology assumptions from generic engine/output code and move such conflicts into character-specific self-model policy.",
    "M1 ownership/ontology repair is complete. Current continuity work uses minimum-sufficient causal roots while preserving historical v1 compatibility. The next uncovered causal continuity family is slow belief consolidation/developmental replay.",
    1,
)
readme.write_text(text, encoding="utf-8")

print("documented root-only continuity production phase")
