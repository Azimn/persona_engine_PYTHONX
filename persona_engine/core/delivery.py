"""Host-authoritative speech delivery receipts.

Generated or selected language is not automatically an event in the world. A
host may deliver it fully, interrupt it, suppress it, or eventually transform
it. This module records what actually reached the environment so downstream
memory and relationship systems can distinguish intended expression from lived
consequence.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib


DELIVERY_RECEIPT_SCHEMA = "ensemble-speech-delivery-v1"


class DeliveryStatus(str, Enum):
    DELIVERED = "delivered"
    PARTIAL = "partial"
    NOT_DELIVERED = "not_delivered"


@dataclass(frozen=True)
class SpeechDeliveryReceipt:
    receipt_id: str
    speech_id: str
    status: DeliveryStatus
    channel: str
    intended_sha256: str
    intended_character_count: int
    delivered_text: str
    delivered_character_count: int
    created_at: float
    host_ref: str = ""
    reason: str = ""
    schema: str = DELIVERY_RECEIPT_SCHEMA

    def __post_init__(self):
        if not self.receipt_id or not self.speech_id:
            raise ValueError("receipt_id and speech_id are required")
        if self.intended_character_count < 0 or self.delivered_character_count < 0:
            raise ValueError("character counts must be non-negative")
        if self.delivered_character_count != len(self.delivered_text):
            raise ValueError("delivered_character_count must match delivered_text")
        if self.status == DeliveryStatus.NOT_DELIVERED and self.delivered_text:
            raise ValueError("not-delivered receipt cannot contain delivered text")
        if self.status == DeliveryStatus.DELIVERED and self.delivered_character_count != self.intended_character_count:
            raise ValueError("delivered receipt must have full intended character count")
        if self.status == DeliveryStatus.PARTIAL and not self.delivered_text:
            raise ValueError("partial receipt requires delivered text")

    def to_dict(self) -> dict:
        return {
            "schema": self.schema,
            "receipt_id": self.receipt_id,
            "speech_id": self.speech_id,
            "status": self.status.value,
            "channel": self.channel,
            "intended_sha256": self.intended_sha256,
            "intended_character_count": self.intended_character_count,
            "delivered_text": self.delivered_text,
            "delivered_character_count": self.delivered_character_count,
            "created_at": self.created_at,
            "host_ref": self.host_ref,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SpeechDeliveryReceipt":
        return cls(
            receipt_id=str(data["receipt_id"]),
            speech_id=str(data["speech_id"]),
            status=DeliveryStatus(data["status"]),
            channel=str(data.get("channel", "text")),
            intended_sha256=str(data["intended_sha256"]),
            intended_character_count=int(data["intended_character_count"]),
            delivered_text=str(data.get("delivered_text", "")),
            delivered_character_count=int(data.get("delivered_character_count", 0)),
            created_at=float(data["created_at"]),
            host_ref=str(data.get("host_ref", "")),
            reason=str(data.get("reason", "")),
            schema=str(data.get("schema", DELIVERY_RECEIPT_SCHEMA)),
        )


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_text_delivery_receipt(
    *,
    receipt_id: str,
    speech_id: str,
    intended_text: str,
    delivered_text: str,
    created_at: float,
    channel: str = "text",
    host_ref: str = "",
    reason: str = "",
) -> SpeechDeliveryReceipt:
    """Create a receipt for exact or prefix delivery.

    V1 intentionally refuses to guess whether a non-prefix transformation is a
    translation, paraphrase, censorship event, speech-recognition correction, or
    something else. Hosts must model those transformations explicitly later.
    """

    intended = str(intended_text or "")
    delivered = str(delivered_text or "")
    if delivered == intended:
        status = DeliveryStatus.DELIVERED
    elif not delivered:
        status = DeliveryStatus.NOT_DELIVERED
    elif intended.startswith(delivered):
        status = DeliveryStatus.PARTIAL
    else:
        raise ValueError("v1 delivered text must be the intended text or an exact prefix")

    return SpeechDeliveryReceipt(
        receipt_id=str(receipt_id),
        speech_id=str(speech_id),
        status=status,
        channel=str(channel or "text"),
        intended_sha256=_digest(intended),
        intended_character_count=len(intended),
        delivered_text=delivered,
        delivered_character_count=len(delivered),
        created_at=float(created_at),
        host_ref=str(host_ref or ""),
        reason=str(reason or ""),
    )


def first_person_delivery_experience(receipt: SpeechDeliveryReceipt) -> str:
    if receipt.status == DeliveryStatus.DELIVERED:
        return f"I said: {receipt.delivered_text}"
    if receipt.status == DeliveryStatus.PARTIAL:
        return f"I began to say: {receipt.delivered_text} I was interrupted before I finished."
    return "I tried to speak, but nothing was delivered."
