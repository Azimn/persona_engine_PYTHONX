# Wayfarer M3 Canonical Continuity Ledger

M3 introduces a canonical continuity ledger beside the existing broad diagnostic `event_log`.

The two logs have different purposes. The diagnostic log may record renderer output, private cognition reports, validation traces, voice plans, avatar state, rejected action proposals, and other useful debugging evidence. The canonical continuity ledger is narrower: it records events admitted by Wayfarer's fail-closed canonicality/authority policy as part of the individual's lived causal history.

## Threat model

The default M3 profile assumes a local-first, single-owner runtime and ordinary corruption/failure concerns. It does not assume an adversarial database administrator or mutually untrusted synchronization peers.

For that reason, M3 uses append-only ordering, uniqueness constraints, sequence validation, UUIDs, deterministic checkpoint digests, SQLite integrity checking, and import/export validation. It does **not** require a cryptographic previous-event hash chain.

A stronger tamper-evident integrity profile may be added later if Wayfarer gains untrusted multi-party synchronization, hostile remote custody, or a requirement to prove history integrity across administrative boundaries.

## Event contract

A canonical continuity event contains:

- permanent `subject_uuid`,
- display/runtime `character_id`,
- `user_id` for the current relationship/session partition,
- monotonically increasing canonical `sequence`,
- `continuity_epoch`, currently zero until M5 handoff/branching semantics,
- event UUID,
- subject time,
- wall time,
- source actor,
- source class,
- authority class,
- event type,
- visibility,
- canonicality marker,
- causal-parent references where supplied,
- payload schema version,
- losslessly preserved payload,
- optional legacy diagnostic event ID for migration/backfill.

M3 v1 subject time is the existing engine timestep. M4 will replace/extend this with an explicit ContinuityClock rather than pretending timestep is full human-like temporal experience.

## Admission policy

Ledger admission reuses the existing fail-closed `can_promote_to_canonical_memory()` contract.

Examples:

- a user input is canonical evidence that the user **said the text**; it is not World Authority proof that the proposition inside the text is true,
- a state transition is canonical character-state history,
- authorized sensor/world events are canonical observations,
- accepted World Authority action resolutions are canonical consequences,
- rejected action proposals remain diagnostic,
- renderer speech is noncanonical,
- private cognition is noncanonical,
- interpretive beliefs are noncanonical,
- UI/avatar/voice output is noncanonical.

This distinction is essential for future multi-agent interaction. `Agent B told me X` may enter biography as an observed social event without silently becoming `X is objectively true`.

## Subject binding

`InteriorEngine` binds persistence to the cartridge's permanent `entity_uuid` when one is available. Direct legacy callers without a UUID receive a deterministic compatibility UUID, but portable Wayfarer subjects should always use the `.snp` entity UUID.

## Checkpoints

State snapshots remain useful caches. M3 records a deterministic SHA-256 digest of canonical JSON state at the latest canonical sequence. The digest detects accidental mismatch and supports cross-runtime conformance testing.

This digest is a checkpoint fingerprint. It is not a blockchain and is not used to chain events together.

## Import/export

`export_continuity_tail()` emits a schema-versioned canonical tail with subject UUID, epoch, ordered events, and latest checkpoint metadata.

`import_continuity_tail()` validates subject identity, epoch, canonicality, event eligibility, payload shape, and contiguous sequence before inserting. It does not automatically execute imported events against runtime state. Replay/application remains a later M3 step after the event contract is stable.

Unknown payload fields are preserved.

## Legacy migration

The old diagnostic `event_log` remains in place during M3.

`backfill_legacy_events()` is explicit and idempotent. It scans historical diagnostic rows, admits only events that satisfy current canonicality rules, and assigns deterministic UUIDv5 identifiers derived from permanent subject identity and legacy event ID. Noncanonical renderer/UI/private-cognition rows are ignored.

## Integrity checks

M3 provides:

- database `PRAGMA integrity_check`,
- canonical sequence-gap detection,
- subject mismatch detection,
- malformed canonical-event detection,
- database uniqueness constraints on event UUID and per-subject/epoch sequence,
- validated tail import.

These mechanisms solve the current local reliability problem without pretending to solve an adversarial distributed-ledger problem that Wayfarer does not yet have.
