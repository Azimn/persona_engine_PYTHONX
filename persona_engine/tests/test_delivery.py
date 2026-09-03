import pytest

from persona_engine.core.delivery import (
    DeliveryStatus,
    first_person_delivery_experience,
    make_text_delivery_receipt,
)


def test_full_delivery_records_only_delivered_text_and_digest():
    receipt = make_text_delivery_receipt(
        receipt_id="r1",
        speech_id="s1",
        intended_text="Hello there.",
        delivered_text="Hello there.",
        created_at=1.0,
    )
    assert receipt.status == DeliveryStatus.DELIVERED
    assert receipt.delivered_text == "Hello there."
    assert len(receipt.intended_sha256) == 64
    assert first_person_delivery_experience(receipt) == "I said: Hello there."


def test_partial_delivery_requires_exact_prefix():
    receipt = make_text_delivery_receipt(
        receipt_id="r1",
        speech_id="s1",
        intended_text="I need to tell you something important.",
        delivered_text="I need to tell you",
        created_at=1.0,
        reason="interrupted",
    )
    assert receipt.status == DeliveryStatus.PARTIAL
    assert "interrupted" in first_person_delivery_experience(receipt)


def test_failed_delivery_does_not_store_secret_plaintext():
    secret = "The secret is Project Orchid."
    receipt = make_text_delivery_receipt(
        receipt_id="r1",
        speech_id="s1",
        intended_text=secret,
        delivered_text="",
        created_at=1.0,
    )
    assert receipt.status == DeliveryStatus.NOT_DELIVERED
    assert secret not in str(receipt.to_dict())
    assert receipt.delivered_text == ""


def test_non_prefix_host_transform_fails_closed():
    with pytest.raises(ValueError):
        make_text_delivery_receipt(
            receipt_id="r1",
            speech_id="s1",
            intended_text="Original wording.",
            delivered_text="Paraphrased wording.",
            created_at=1.0,
        )


def test_receipt_roundtrip_preserves_status():
    receipt = make_text_delivery_receipt(
        receipt_id="r1",
        speech_id="s1",
        intended_text="abcdef",
        delivered_text="abc",
        created_at=2.0,
    )
    restored = type(receipt).from_dict(receipt.to_dict())
    assert restored == receipt
