from __future__ import annotations

import pytest

from persona_engine.core.delivery import (
    DeliveryStatus,
    SpeechDeliveryReceipt,
    first_person_delivery_experience,
    make_text_delivery_receipt,
)


def test_full_delivery_records_actual_utterance():
    receipt = make_text_delivery_receipt(
        speech_id="turn-7-speech",
        intended_text="I will meet you at dusk.",
        delivered_text="I will meet you at dusk.",
        channel="text",
        host_ref="chat:message:77",
        delivered_at=10.0,
        receipt_id="receipt_full",
    )

    assert receipt.status == DeliveryStatus.DELIVERED.value
    assert receipt.delivered_chars == receipt.intended_chars
    assert first_person_delivery_experience(receipt) == "I said: I will meet you at dusk."


def test_interrupted_prefix_records_only_what_was_actually_delivered():
    intended = "I need to tell you something important about yesterday."
    delivered = "I need to tell you something"
    receipt = make_text_delivery_receipt(
        speech_id="turn-8-speech",
        intended_text=intended,
        delivered_text=delivered,
        channel="voice",
        host_ref="tts:utterance:88",
        delivered_at=20.0,
        reason="user interrupted playback",
        receipt_id="receipt_partial",
    )

    assert receipt.status == DeliveryStatus.PARTIAL.value
    assert receipt.delivered_text == delivered
    assert "important about yesterday" not in first_person_delivery_experience(receipt)
    assert first_person_delivery_experience(receipt) == (
        "I began to say: I need to tell you something I was interrupted before I finished."
    )


def test_failed_delivery_does_not_store_never_delivered_secret_text():
    secret = "Project Orchid access phrase is cerulean-lantern-9."
    receipt = make_text_delivery_receipt(
        speech_id="turn-9-speech",
        intended_text=secret,
        delivered_text="",
        channel="voice",
        host_ref="tts:utterance:89",
        delivered_at=30.0,
        reason="audio device unavailable",
        receipt_id="receipt_failed",
    )

    serialized = receipt.to_dict()
    assert receipt.status == DeliveryStatus.NOT_DELIVERED.value
    assert secret not in str(serialized)
    assert "cerulean-lantern-9" not in str(serialized)
    assert receipt.intended_chars == len(secret)
    assert len(receipt.intended_sha256) == 64
    assert first_person_delivery_experience(receipt) == "I tried to speak, but nothing was delivered."


def test_v1_rejects_host_text_that_is_not_an_exact_prefix():
    with pytest.raises(ValueError, match="exact prefix"):
        make_text_delivery_receipt(
            speech_id="turn-10-speech",
            intended_text="I cannot agree to that.",
            delivered_text="Sure, I agree.",
            channel="text",
            host_ref="chat:message:90",
        )


def test_delivery_receipt_round_trip_preserves_host_evidence():
    receipt = make_text_delivery_receipt(
        speech_id="turn-11-speech",
        intended_text="No. I won't do that.",
        delivered_text="No. I won't",
        channel="voice",
        host_ref="tts:utterance:91",
        delivered_at=40.0,
        reason="connection dropped",
        receipt_id="receipt_roundtrip",
    )

    restored = SpeechDeliveryReceipt.from_dict(receipt.to_dict())
    assert restored == receipt


def test_not_delivered_receipt_fails_closed_if_it_claims_delivered_text():
    data = make_text_delivery_receipt(
        speech_id="turn-12-speech",
        intended_text="hello",
        delivered_text="",
        channel="text",
        host_ref="chat:message:92",
        receipt_id="receipt_invalid_base",
    ).to_dict()
    data["delivered_text"] = "h"
    data["delivered_chars"] = 1

    with pytest.raises(ValueError, match="must not contain"):
        SpeechDeliveryReceipt.from_dict(data)
