# Speech Delivery Receipt Experiment

Status: **EXPERIMENTAL BRANCH ONLY**

Branch: `wayfarer-adjacent-research-phase`

## Problem

Wayfarer already distinguishes semantic decision from renderer wording, and its world-action architecture distinguishes intended action from `WorldResolution`. Speech still has an asymmetry: a renderer can generate a complete response, but a host may fail to deliver it or may be interrupted partway through.

Without a host receipt, later biography can accidentally assume that generated speech was fully experienced by the other party.

Examples include:

- the user interrupts TTS halfway through a sentence;
- streaming stops after a network failure;
- a game host cuts dialogue when a scene changes;
- an audio device fails before playback;
- a robot begins an utterance but is interrupted;
- a UI suppresses a message before display.

## Candidate causal path

```text
semantic SpeechPlan
      -> Renderer
      -> intended text
      -> Host Delivery
      -> SpeechDeliveryReceipt
      -> experienced consequence
```

The receipt is host evidence about what actually reached the channel. It does not make the semantic claims inside the utterance objective world truth.

## Experimental v1 contract

`core/delivery.py` supports only three outcomes:

- `delivered`: the exact intended text was delivered;
- `partial`: a non-empty strict prefix was delivered;
- `not_delivered`: none of the intended text was delivered.

V1 deliberately rejects a host report whose delivered text is not an exact prefix of the intended text. Translation, paraphrase, speech-recognition uncertainty, censorship transforms, or other host rewriting require a later transform-aware receipt rather than being silently represented as exact delivery.

## Least-privilege detail

The receipt does **not** store the full intended text separately.

It stores:

- the SHA-256 digest of intended text;
- intended character count;
- only the text that was actually delivered;
- delivery status, channel, host reference, time, and reason.

This matters when delivery fails. A message containing a protected value that never reached the channel should not be copied into a canonical delivery record merely because the renderer generated it.

## First-person experience

The experiment deterministically projects delivery outcome into first-person lived framing:

- full: `I said: ...`
- partial: `I began to say: ... I was interrupted before I finished.`
- failed: `I tried to speak, but nothing was delivered.`

As with the epistemic experiment, this language is derived from typed state and has no authority over the event that produced it.

## What this does not yet do

The prototype is not wired into `receive_input()` or host APIs.

It does not yet:

- create canonical continuity roots;
- change relationship state when interruption occurs;
- infer whether the user actually understood the delivered words;
- model translation or semantic transformation;
- model simultaneous multi-recipient speech;
- model audio recognition confidence;
- make renderer claims true merely because they were spoken.

## Production acceptance gate

A later integration should prove at minimum:

1. a fully delivered utterance becomes an experienced speech action;
2. an interrupted utterance records only the delivered prefix;
3. a failed utterance stores no never-delivered secret/plaintext content;
4. restart/replay reconstructs the same delivery history;
5. relationship or commitment effects consume the actual delivery result where causally relevant;
6. renderer output that was never delivered cannot be used as evidence that the interlocutor heard it;
7. low-resource storage does not duplicate renderer transcripts unnecessarily.

This mechanism is attractive because it adds little psychological complexity. It is primarily an authority and embodiment correction at the host boundary.
