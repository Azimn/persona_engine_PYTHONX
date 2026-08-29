#!/usr/bin/env python3
"""Test a semantics-preserving bounded representation for WorldAuthority facts.

The candidate compactor removes only facts that can never again become the
winning value for either server truth or character-visible truth. Expiring
facts are retained when they can become future fallbacks. Hidden and visible
projections are evaluated independently and their required facts are unioned.
No production code is changed by this probe.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from persona_engine.core.world_authority import WorldAuthority, WorldFact

BASE_NOW = 1_000.0


def _views_at(authority: WorldAuthority, now: float) -> tuple[dict, dict]:
    clone = WorldAuthority.from_list(authority.to_list())
    clone.expire_old(now=now)
    server = {fact.key: fact.value for fact in clone.facts.values()}
    visible = {fact.key: fact.value for fact in clone.facts.values() if fact.visible_to_character}
    return server, visible


def _potential_winners(facts: list[WorldFact], now: float) -> set[str]:
    """Return facts that can become latest-surviving within one projection."""

    live = [fact for fact in facts if fact.expires_at is None or fact.expires_at > now]
    keep: set[str] = set()
    max_newer_expiry = now
    for fact in reversed(live):
        if fact.expires_at is None:
            keep.add(fact.id)
            break
        if fact.expires_at > max_newer_expiry:
            keep.add(fact.id)
            max_newer_expiry = fact.expires_at
    return keep


def compact_candidate(authority: WorldAuthority, now: float) -> int:
    authority.expire_old(now=now)
    by_key: dict[str, list[WorldFact]] = {}
    for fact in authority.facts.values():
        by_key.setdefault(fact.key, []).append(fact)

    keep: set[str] = set()
    for facts in by_key.values():
        keep.update(_potential_winners(facts, now))
        keep.update(_potential_winners([fact for fact in facts if fact.visible_to_character], now))

    before = len(authority.facts)
    authority.facts = {fact_id: fact for fact_id, fact in authority.facts.items() if fact_id in keep}
    return before - len(authority.facts)


def _add(authority, key, value, created_at, *, visible=True, expires_at=None):
    return authority.add_fact(
        key,
        value,
        source="probe",
        visible_to_character=visible,
        created_at=created_at,
        expires_at=expires_at,
    )


def _scenario_cases() -> list[tuple[str, WorldAuthority, list[float]]]:
    cases = []

    a = WorldAuthority()
    _add(a, "zone", "A", 100)
    _add(a, "zone", "B", 200)
    _add(a, "zone", "C", 300)
    cases.append(("permanent_churn", a, [BASE_NOW, 2_000]))

    a = WorldAuthority()
    _add(a, "weather", "clear", 100)
    _add(a, "weather", "storm", 200, expires_at=1_200)
    cases.append(("temporary_override_fallback", a, [BASE_NOW, 1_100, 1_300]))

    a = WorldAuthority()
    _add(a, "mode", "base", 100)
    _add(a, "mode", "middle", 200, expires_at=1_400)
    _add(a, "mode", "top", 300, expires_at=1_200)
    cases.append(("nested_expiry", a, [BASE_NOW, 1_100, 1_300, 1_500]))

    a = WorldAuthority()
    _add(a, "signal", "base", 100)
    _add(a, "signal", "dominated", 200, expires_at=1_200)
    _add(a, "signal", "newer", 300, expires_at=1_400)
    cases.append(("dominated_expiry", a, [BASE_NOW, 1_100, 1_300, 1_500]))

    a = WorldAuthority()
    _add(a, "note", "visible_base", 100, visible=True)
    _add(a, "note", "hidden_override", 200, visible=False)
    cases.append(("hidden_permanent_override", a, [BASE_NOW, 2_000]))

    a = WorldAuthority()
    _add(a, "note", "visible_base", 100, visible=True)
    _add(a, "note", "hidden_temp", 200, visible=False, expires_at=1_200)
    cases.append(("hidden_temporary_override", a, [BASE_NOW, 1_100, 1_300]))

    return cases


def _random_fixture() -> WorldAuthority:
    rng = random.Random(260829)
    authority = WorldAuthority()
    for index in range(2_000):
        key = f"key_{rng.randrange(20):02d}"
        created = 100.0 + index * 0.2
        expiry_kind = rng.randrange(5)
        if expiry_kind == 0:
            expires = None
        else:
            expires = BASE_NOW + rng.choice([50, 100, 250, 500, 1000, 2500])
        _add(
            authority,
            key,
            f"value_{index}",
            created,
            visible=(rng.randrange(4) != 0),
            expires_at=expires,
        )
    return authority


def run() -> dict:
    scenario_results = []
    all_preserved = True
    for name, original, times in _scenario_cases():
        compacted = WorldAuthority.from_list(original.to_list())
        before = len(compacted.facts)
        removed = compact_candidate(compacted, BASE_NOW)
        checks = []
        for t in times:
            before_views = _views_at(original, t)
            after_views = _views_at(compacted, t)
            preserved = before_views == after_views
            all_preserved = all_preserved and preserved
            checks.append({
                "time": t,
                "preserved": preserved,
                "server_truth": before_views[0],
                "visible_truth": before_views[1],
            })
        scenario_results.append({
            "name": name,
            "facts_before": before,
            "facts_after": len(compacted.facts),
            "facts_removed": removed,
            "checks": checks,
        })

    random_original = _random_fixture()
    random_compacted = WorldAuthority.from_list(random_original.to_list())
    random_before = len(random_compacted.facts)
    random_removed = compact_candidate(random_compacted, BASE_NOW)
    random_times = [BASE_NOW, 1_050, 1_100, 1_250, 1_500, 2_000, 3_500, 5_000]
    random_checks = []
    for t in random_times:
        preserved = _views_at(random_original, t) == _views_at(random_compacted, t)
        all_preserved = all_preserved and preserved
        random_checks.append({"time": t, "preserved": preserved})

    return {
        "probe": "world-authority-semantic-compaction-v1",
        "production_policy_changed": False,
        "all_truth_and_visibility_views_preserved": all_preserved,
        "scenario_results": scenario_results,
        "random_fixture": {
            "facts_before": random_before,
            "facts_after": len(random_compacted.facts),
            "facts_removed": random_removed,
            "reduction_fraction": random_removed / random_before if random_before else 0.0,
            "checks": random_checks,
        },
        "candidate_rule": "Per semantic key, retain the union of facts that can still become latest-surviving server truth and latest-surviving visible truth. A later non-expiring fact permanently dominates older facts in that projection; an older expiring fact is retained only if it outlives every newer candidate and can therefore re-emerge.",
        "recent_facts_note": "The probe preserves authoritative server and visible truth, including future expiry fallback. It does not claim historical recent_facts output is preserved; canonical continuity is the intended history authority and this compatibility seam must be reviewed before production integration.",
    }


def markdown(result: dict) -> str:
    lines = [
        "# WorldAuthority Semantic Compaction Probe",
        "",
        f"All server/visible truth views preserved: `{result['all_truth_and_visibility_views_preserved']}`.  ",
        f"Production policy changed: `{result['production_policy_changed']}`.",
        "",
        "| Scenario | Facts before | Facts after | Removed |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in result["scenario_results"]:
        lines.append(f"| {row['name']} | {row['facts_before']} | {row['facts_after']} | {row['facts_removed']} |")
    random_row = result["random_fixture"]
    lines.extend([
        "",
        f"Deterministic 2,000-fact mixed fixture: `{random_row['facts_before']}` -> `{random_row['facts_after']}` active facts, removing `{random_row['facts_removed']}` ({random_row['reduction_fraction']:.1%}).",
        "",
        result["recent_facts_note"],
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json")
    parser.add_argument("--markdown")
    args = parser.parse_args()
    result = run()
    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.json:
        path = Path(args.json)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered + "\n", encoding="utf-8")
    if args.markdown:
        path = Path(args.markdown)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown(result), encoding="utf-8")
    if not result["all_truth_and_visibility_views_preserved"]:
        raise SystemExit("candidate WorldAuthority compaction changed authoritative truth semantics")


if __name__ == "__main__":
    main()
