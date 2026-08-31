# Cross-Host Writer Handoff V1

## Falsification target

Two distinct hosts sharing one canonical subject authority store must not both be able to author subject state. A deliberate handoff must advance a fencing generation, preserve established subject/state contracts, and make the former host fail closed.

## Before

The pre-fix probe demonstrated dual writers: `2` independent engine inputs entered the same canonical stream with no host custody boundary.

## After

- competing host blocked before handoff: `True`
- stale source blocked after handoff: `True`
- target writer generation: `2`
- subject sequence anchor: `3`
- same permanent subject across interlocutors: `True`
- commitment behavior after handoff: `decline`
- subject clock preserved: `60.080240844665525` seconds
- earned trait preserved: `True`
- administrative handoff excluded from lived biography: `True`

## Scope

V1 uses a shared canonical SQLite authority store and cooperative hosts with explicit, distinct `host_id` values. The lease is a durable exclusive custody claim with a monotonic writer generation. It has no timeout and no automatic steal path. That is intentional: uncertainty fails closed rather than risking split-brain canonical history.

This does not yet solve disconnected database copies, hostile direct database mutation, remote consensus, or reconciliation of already-divergent copies. Such copies remain branch candidates, not silently mergeable continuations.

## Verification

Targeted custody/continuity suite and permanent handoff probe passed after replacing the per-mutation writer-row heartbeat with a SQLite `BEGIN IMMEDIATE` fencing reservation. Full deterministic suite:

```text
........................................................................ [ 21%]
........................................................................ [ 42%]
.....s.................................................................. [ 63%]
........................................................................ [ 84%]
.....................................................                    [100%]
=============================== warnings summary ===============================
persona_engine/tests/test_human_ui.py::test_create_app_serves_root_and_cartridges
  /opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
============================= slowest 20 durations =============================
3.33s call     persona_engine/tests/test_bounded_diagnostic_persistence.py::test_normal_runtime_pruning_is_amortized_but_stays_inside_operational_slack
2.36s call     persona_engine/tests/test_role_bounded_user_memory.py::test_production_residency_stays_small_under_routine_user_history
2.08s call     persona_engine/tests/test_mvi_character_baseline.py::test_clean_ablation_seams_remove_the_mechanism_they_claim_to_remove
2.04s call     persona_engine/tests/test_mvi_character_baseline.py::test_early_mvi_study_has_fixed_renderer_and_all_declared_conditions
2.01s call     persona_engine/tests/test_mvi_character_baseline.py::test_mvi_report_does_not_reduce_results_to_a_single_lifelikeness_score
1.54s call     persona_engine/tests/test_cold_biography.py::test_nonexistent_explicit_recall_fails_closed_instead_of_using_nearest_memory
1.10s call     persona_engine/tests/test_cold_biography.py::test_contextual_cold_readthrough_fails_closed_for_never_happened_and_anchorless_topics
1.06s call     persona_engine/tests/test_cold_biography.py::test_contextual_cold_readthrough_changes_observable_answer_without_rehydrating_hot_memory
1.06s call     persona_engine/tests/test_cold_biography.py::test_anchorless_explicit_recall_fails_closed
1.04s call     persona_engine/tests/test_cold_biography.py::test_cold_recall_does_not_cross_interlocutor_boundary
1.04s call     persona_engine/tests/test_bounded_diagnostic_persistence.py::test_direct_persistence_keeps_legacy_unlimited_diagnostics_by_default
1.04s call     persona_engine/tests/test_cold_biography.py::test_contextual_cold_readthrough_does_not_cross_interlocutor_boundary
1.03s call     persona_engine/tests/test_cold_biography.py::test_explicit_recall_reads_cold_biography_without_rehydrating_resident_cache
0.38s call     persona_engine/tests/test_human_ui.py::test_create_app_serves_root_and_cartridges
0.32s call     persona_engine/tests/test_full_conversation.py::test_full_conversation_snapshot_round_trip
0.31s call     persona_engine/tests/test_interpretation_contract.py::test_anchored_misread_simulator_runs
0.29s call     persona_engine/tests/test_long_silence_contract.py::test_long_silence_resume_script_runs
0.27s call     persona_engine/tests/test_personaconsole_v6_compat.py::test_converted_personaconsole_v6_cartridges_run_one_turn
0.25s call     persona_engine/tests/test_role_bounded_user_memory.py::test_what_about_negative_still_fails_closed
0.25s call     persona_engine/tests/test_role_bounded_user_memory.py::test_old_evicted_topic_is_recovered_by_grounded_what_about_continuation
340 passed, 1 skipped, 1 warning in 31.68s
```
