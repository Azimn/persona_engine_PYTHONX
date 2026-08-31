# Disconnected Authority-Store Transfer V1

## Falsification target

A move between separate authority stores must not leave both supported runtime stores writable. The package must represent the whole subject rather than one interlocutor stream, the target must remain read-only until source retirement, and the old source database must not become writable again merely because it is reopened with the target host id.

## Pre-fix gap

The pre-fix probe showed:

- same permanent subject UUID in two independently created stores: `True`
- source independently writable: `True`
- target independently writable: `True`
- source writer generation: `1`
- target writer generation: `1`
- established per-interlocutor export carried subject-wide ordinal: `False`
- Alice export included Bob canonical events: `False`

This demonstrated that `export_continuity_tail()` was an interchange seam, not a whole-subject migration protocol.

## Post-fix result

Permanent probe passed: `True`.

- source quiesced after preparation: `True`
- staged target blocked before source finalization: `True`
- finalized source store retired: `True`
- old source stayed retired when reopened using target host id: `True`
- target became writable only after activation: `True`
- writer generation: `1` -> `2`
- whole-subject canonical anchor: `4`
- canonical event count source/target: `4` / `4`
- pending consolidation evidence preserved: `True`
- Alice relationship preserved: `True`
- Bob relationship preserved: `True`
- subject-owned earned trait preserved: `True`
- self-adopted commitment preserved: `True`
- transfer administration inserted into lived history: `False`

Targeted verification: `38 passed in 2.78s`.

Full deterministic Python 3.11 suite: `346 passed, 1 skipped, 1 warning in 31.81s`.

## Transfer protocol

1. Source persists a clean primary-stream state boundary and packages the whole subject across bound interlocutors.
2. Preparation records a target-specific transfer UUID and quiesces normal writes across the source subject.
3. Target validates bundle/content digests, complete subject and per-stream ordering, bindings, and canonical eligibility, then stages the subject with source generation custody so the target remains read-only.
4. Source validates the exact staging receipt and unchanged whole-subject content, advances custody to the target generation, and permanently retires that source authority store.
5. Target verifies its local state/content against the final receipt, activates the target host, and installs the new generation claim.
6. Cancellation is allowed only before source finalization.

Diagnostic event-log rows are not required for migration. Pending slow-consolidation evidence is transferred separately and receives negative target-local legacy ids so future positive diagnostic ids cannot collide.

## Scope and limitations

This is a cooperative host-id and supported-API contract. It does not provide remote consensus, cryptographic uniqueness, hostile direct-database protection, or a way for two disconnected stores to detect that both are maliciously impersonating the same target host. An intentional copy still requires explicit branch semantics. Divergent copies remain descendants/branches and are not silently mergeable.
