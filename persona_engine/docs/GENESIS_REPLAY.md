# Autobiographical Genesis Replay

Genesis replay gives a new organism an authored past without importing a
biography directly into `MemoryStore`.

Cartridge `[genesis]` episodes pass through the existing ownership chain:

```text
cartridge-authored historical input
-> objective continuity-scoped WorldEvent
-> bounded perception or missed event
-> SubjectiveExperience
-> optional ordinary consolidation
-> elapsed-time decay and compression
-> AutobiographicalInterpretation
-> later retrieval and synthesis
```

An episode declares one authority category: `lived`, `documentary`, `hearsay`,
`expanded_continuity`, `ontologically_disputed`, or `current_system_fact`.
Conflicting continuities are retained. The category describes why the record
exists; it does not force the character to resolve the contradiction.

Genesis is bounded to 64 episodes. Replays have a stable source digest and are
idempotent per persisted organism. The replayer never constructs a
`MemoryUnit` directly.

Pretorius's first authored history deliberately includes reconstructed early
life, lived creation experiences, one important missed event, moral failures,
incompatible death and survival memories, expanded-media claims, documentary
evidence that he was performed as fiction, digital embodiment, and modern
scientific correction.

Run an offline fresh-versus-genesis comparison:

```bash
python -m persona_engine.genesis \
  --cartridge persona_engine/cartridges/pretorius.snp \
  --db genesis_eval.db \
  --compare-fresh \
  --output genesis_comparison.json
```

Use `--provider ollama --model qwen3:8b --thinking off` for an optional local
model comparison. Model output on explicit autobiographical questions must use
details from the selected memory. Ungrounded output falls back to deterministic
expression and records the fallback reason.

Current limitation: historical actors do not yet receive independent
relationship ledgers. Replaying Henry's dialogue through the current-user turn
path would incorrectly transfer Henry's relationship history to the present
user, so genesis dialogue is presently stored as observed dialogue and lived
experience instead.
