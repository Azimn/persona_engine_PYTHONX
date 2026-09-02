"""Experimental host receipt for what speech was actually delivered.

Wayfarer already separates semantic speech choice from renderer wording.  This
module tests the next host boundary: generated wording is an intention to speak,
not proof that the other party actually received every generated character.

The initial contract is deliberately narrow and dependency-free.  It supports
exact text delivery, prefix delivery interrupted partway through, and complete
failure.  More complex host transforms (translation, paraphrase, lossy speech
recognition) require a separately versioned contract rather than being guessed
into this one.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any
import hashlib
import time
import uuid


class DeliveryStatus(str, Enum):
    DELIVERED = "delivered"
    PARTIAL = "partial"
    NOT_DELIVERED = "not_delivered"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SpeechDeliveryReceipt:
    """Host-owned evidence of the text that actually reached the channel.

    ``intended_text`` is intentionally not stored.  The receipt keeps its hash
    and length, plus only the text that the host reports was actually delivered.
    This prevents a failed/partial delivery record from becoming a second copy of
    concealed or never-spoken generated content.
    """

    receipt_id: str
    speech_id: str
    status: str
    channel: str
    intended_sha256: str
    intended_chars: int
    delivered_text: str
    delivered_chars: int
    delivered_at: float
    host_ref: str
    reason: str = ""
    schema_version: str = "speech-delivery-receipt-v1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SpeechDeliveryReceipt":
        receipt = cls(**{key: data[key] for key in cls.__dataclass_fields__ if key in data})
        validate_delivery_receipt(receipt)
        return receipt


def validate_delivery_receipt(receipt: SpeechDeliveryReceipt) -> None:
    if receipt.schema_version != "speech-delivery-receipt-v1":
        raise ValueError(f"unsupported speech delivery schema: {receipt.schema_version}")
    if not str(receipt.receipt_id or "").strip():
        raise ValueError("receipt_id must not be empty")
    if not str(receipt.speech_id or "").strip():
        raise ValueError("speech_id must not be empty")
    if not str(receipt.channel or "").strip():
        raise ValueError("channel must not be empty")
    if not str(receipt.host_ref or "").strip():
        raise ValueError("host_ref must not be empty")
    try:
        status = DeliveryStatus(str(receipt.status))
    except ValueError as exc:
        raise ValueError(f"unsupported delivery status: {receipt.status}") from exc
    if int(receipt.intended_chars) < 0 or int(receipt.delivered_chars) < 0:
        raise ValueError("delivery character counts must be non-negative")
    if int(receipt.delivered_chars) != len(receipt.delivered_text):
        raise ValueError("delivered_chars must match delivered_text length")
    if int(receipt.delivered_chars) > int(receipt.intended_chars):
        raise ValueError("delivered content cannot exceed intended length")
    if status is DeliveryStatus.NOT_DELIVERED:
        if receipt.delivered_text or receipt.delivered_chars != 0:
            raise ValueError("not_delivered receipt must not contain delivered text")
    elif status is DeliveryStatus.PARTIAL:
        if receipt.delivered_chars <= 0 or receipt.delivered_chars >= receipt.intended_chars:
            raise ValueError("partial receipt must contain a non-empty strict prefix")
    elif receipt.delivered_chars != receipt.intended_chars:
        raise ValueError("delivered receipt must match intended length")
    if len(str(receipt.intended_sha256)) != 64:
        raise ValueError("intended_sha256 must be a SHA-256 hex digest")


def make_text_delivery_receipt(
    *,
    speech_id: str,
    intended_text: str,
    delivered_text: str,
    channel: str,
    host_ref: str,
    delivered_at: float | None = None,
    reason: str = "",
    receipt_id: str | None = None,
) -> SpeechDeliveryReceipt:
    """Create a receipt for exact, interrupted-prefix, or failed text delivery.

    The v1 contract rejects non-prefix transformed output.  A host that changes
    wording must use a future transform-aware receipt rather than pretending the
    altered text was the original utterance.
    """

    intended = str(intended_text or "")
    delivered = str(delivered_text or "")
    if delivered and not intended.startswith(delivered):
        raise ValueError("v1 delivered_text must be an exact prefix of intended_text")
    if not delivered:
        status = DeliveryStatus.NOT_DELIVERED
    elif delivered == intended:
        status = DeliveryStatus.DELIVERED
    else:
        status = DeliveryStatus.PARTIAL
    receipt = SpeechDeliveryReceipt(
        receipt_id=str(receipt_id or f"delivery_{uuid.uuid4().hex}"),
        speech_id=str(speech_id or "").strip(),
        status=status.value,
        channel=str(channel or "").strip(),
        intended_sha256=_sha256_text(intended),
        intended_chars=len(intended),
        delivered_text=delivered,
        delivered_chars=len(delivered),
        delivered_at=float(time.time() if delivered_at is None else delivered_at),
        host_ref=str(host_ref or "").strip(),
        reason=" ".join(str(reason or "").strip().split()),
    )
    validate_delivery_receipt(receipt)
    return receipt


def first_person_delivery_experience(receipt: SpeechDeliveryReceipt) -> str:
    """Project actual delivery as first-person experience, not world truth."""

    validate_delivery_receipt(receipt)
    if receipt.status == DeliveryStatus.DELIVERED.value:
        return f"I said: {receipt.delivered_text}"
    if receipt.status == DeliveryStatus.PARTIAL.value:
        return f"I began to say: {receipt.delivered_text} I was interrupted before I finished."
    return "I tried to speak, but nothing was delivered."
