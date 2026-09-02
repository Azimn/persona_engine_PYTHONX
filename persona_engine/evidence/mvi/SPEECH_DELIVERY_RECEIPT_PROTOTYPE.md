# Speech Delivery Receipt Prototype Verification

Date: 2026-09-02
Combined experimental code checkpoint: `4049ed75821acfbef49b71fd8fb31aa20b240565`
Workflow run: `33684229287`
Production `wayfarer` runtime remains unchanged by this experiment.

## Result

The isolated speech-delivery receipt contract is mechanically viable and coexists with the epistemic proposition prototype without regressing the existing deterministic suite.

Focused adjacent-prototype verification:

```text
Python 3.11: 12 passed
Python 3.12: 12 passed
```

Full experimental branch suite:

```text
Python 3.11: 391 passed, 1 skipped, 1 warning
Python 3.12: 391 passed, 1 skipped, 1 warning
```

The 12 focused tests comprise six epistemic-proposition regressions and six delivery-receipt regressions. Production `wayfarer` remains on its previously verified 379-test runtime inventory because these experimental modules are not wired into production.

## Demonstrated delivery invariants

### Full delivery

When the host reports that the exact intended text reached the channel, the receipt records `delivered` and the first-person projection records the actual utterance.

### Partial delivery

When only a strict prefix was delivered, the receipt records only that delivered prefix. The undelivered suffix is not represented as something the subject said.

The deterministic first-person projection states that the subject began speaking and was interrupted before finishing.

### Failed delivery preserves least privilege

When nothing was delivered, the receipt stores no plaintext copy of the intended utterance. It retains only the intended SHA-256 digest and character count plus host delivery metadata.

A regression uses a Project Orchid secret string and verifies that neither the secret nor its protected value appears in the serialized failed-delivery receipt.

### Host transformation fails closed in v1

The v1 contract accepts exact delivery or an exact delivered prefix only. A host report containing different wording is rejected rather than silently pretending translation, paraphrase, censorship, or another transform was exact delivery.

### Receipt round-trip

A valid receipt survives serialization and reconstruction with host evidence unchanged.

### Malformed status fails closed

A `not_delivered` receipt that also claims delivered text is rejected.

## Architectural significance

This prototype gives speech the same conceptual separation already present in Wayfarer world actions:

```text
intention -> attempted action -> host resolution -> experienced consequence
```

A renderer-generated utterance is therefore not automatically evidence that another person actually heard the whole utterance.

This is useful for voice, streaming text, games, robotics, network interruptions, scene transitions, muting, and other hosts where generation and delivery can diverge.

## What this verification does not establish

This checkpoint does not justify production integration yet.

It does not establish:

- canonical delivery-event/replay semantics;
- relationship consequences of interruption;
- recipient comprehension;
- translated or transformed delivery semantics;
- multiple-recipient delivery;
- speech-recognition uncertainty;
- integration with current `receive_input()` output handling;
- whether full renderer text should ever be retained outside diagnostic logs.

Those are separate host/runtime experiments.

## Next delivery experiment

If this mechanism is advanced after the frozen Phase D renderer evidence is collected, the next test should introduce an explicit host delivery acknowledgement seam without changing renderer authority. The character should only acquire first-person evidence of what was actually delivered, and replay should reconstruct that same experience from the receipt.
