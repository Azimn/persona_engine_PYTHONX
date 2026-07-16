# v0.2 Simulated Life Extension

This pass extends the existing organism with a compact game-oriented life layer. It does not replace World Authority, MemoryStore, InterpretationEngine, Tide, DreamEngine, or the renderer contract.

## Architecture Decisions

- `WorldEventLedger` is append-only and stores objective, externally resolvable events only.
- `ExperienceStore` keeps per-character perception, interpretation, emotional residue, confidence, distortion, and lifecycle separately from objective events.
- Experiences begin as traces. Salient traces may consolidate through `MemoryStore`; weak traces decay or are pruned.
- `MemoryStore.retrieve_explained` adds selection reasons while preserving the existing `retrieve` API.
- `EmbeddingProvider` is narrow and optional. The default is `NoEmbeddingProvider`; `HashEmbeddingProvider` proves local vectors and caching without a dependency or neural model.
- `VitalityEventEngine` is separate from Tide. It uses persisted counter-based randomness, bounded rates, and explicit `whim`, `limitation`, and `chaos` provenance.
- `LifeState` stores current activity, intention, attention, interruption state, entropy, and a bounded recent event list.
- `CapabilityArtifactStore` validates durable tier-produced knowledge. Artifacts belong to the organism and remain available to lower tiers.
- `ImperfectActionEngine` separates decision quality, execution result, objective cause, and learned subjective inference.
- `SelfMonitor` reads actual diagnostics but produces fallible perceived state and bounded regulation candidates; it never executes them directly.
- `SubjectiveExperience` preserves encoding-time perception; append-only autobiographical interpretations own later evidence-backed meaning.
- The debug UI remains read-only and projects world/experience discrepancies, recall reasons, life events, and learning artifacts.

## Migration Notes

No cartridge migration is required. Existing cartridges receive neutral vitality defaults. Authors may later add a `[vitality]` table with generic `whim_weights`; this pass does not require or modify cartridge files.

Existing SQLite databases load with empty ledgers and default life state when the new JSON state keys are absent. New keys are:

- `world_events`
- `subjective_experiences`
- `capability_artifacts`
- `life_state`
- `imperfect_action`
- `last_self_monitor`
- `autobiographical_interpretations`
- `deferred_reinterpretations`
- `interpretation_use_outcomes`

No SQL schema migration is needed because these use the existing `(character_id, user_id, key)` state table.

## Performance Measurements

Measured on July 14, 2026 using the bundled Codex Python runtime on the development machine:

| Probe | Result |
|---|---:|
| Baseline tests before v0.2 | 177 passed, 1 skipped in 6.48 s |
| Allocated memory for 1,000 world events | 435,434 bytes |
| Compact JSON for 1,000 world events | 240,671 bytes |
| Allocated memory for 1,000 subjective experiences | 642,642 bytes |
| Compact JSON for 1,000 subjective experiences | 520,781 bytes |
| Retrieval over 1,000 memories, no embeddings | 13.9349 ms/query |
| Retrieval over 1,000 memories, hash adapter | 20.1937 ms/query |
| Vitality tick | 0.002868 ms |
| Summarized one-day catch-up, maximum 12 steps | 0.036164 ms |
| SQLite size with 1,000 events and 1,000 experiences | 856,064 bytes |

Run the same probe locally:

```powershell
python -m persona_engine.benchmarks.life_v02 --cartridge persona_engine/cartridges/neutral.snp
```

These are reference measurements, not cross-machine performance guarantees.

## Simulator

```powershell
python persona_engine/simulator.py --script persona_engine/simulator_scripts/lived_experience_v02.yaml --cartridge persona_engine/cartridges/neutral.snp
```

The scenario covers pre-existing activity, interruption, objective and subjective event records, failed action, incorrect learning, recall, whim, limitation, forced chaos, contradictory evidence, and continued idle life.

## Known Limitations

- Subjective perception uses deterministic bounded rules; model enrichment is not yet connected.
- Hash vectors are a local adapter demonstration, not a neural semantic model.
- Activity selection uses generic defaults until cartridges opt into vitality weights.
- Learning artifacts are inspectable and challengeable but do not yet feed DreamEngine belief consolidation.
- Catch-up summarizes vitality events but retains the older bounded Tide catch-up loop for compatibility.
- The life inspector is a developer debug view, not a player-facing presentation.
