"""Host-supplied external/frontier expression renderer adapter.

The adapter deliberately knows nothing about OpenAI, Anthropic, xAI, or any
other provider SDK. A host supplies a callback that accepts standard chat
messages. The same Wayfarer expression brief is therefore usable with a
frontier service, a local gateway, or a manual integration without granting the
provider authority over character state.
"""

from __future__ import annotations

from typing import Any, Callable

from .expression_bridge import build_expression_messages
from .offline_template_renderer import OfflineTemplateRenderer


class ExternalChatRenderer:
    def __init__(
        self,
        chat: Callable[[list[dict[str, str]]], Any],
        *,
        provider_name: str = "external",
        model_name: str = "external-chat",
    ):
        self.chat = chat
        self.provider_name = str(provider_name or "external")
        self.model_name = str(model_name or "external-chat")
        self._actual_provider = self.provider_name
        self._fallback_reason: str | None = None
        self._offline = OfflineTemplateRenderer()

    def runtime_status(self) -> dict:
        return {
            "requested_provider": self.provider_name,
            "actual_provider": self._actual_provider,
            "model_name": self.model_name,
            "fallback_reason": self._fallback_reason,
        }

    @staticmethod
    def _extract_text(raw: Any) -> str:
        if isinstance(raw, str):
            return raw.strip()
        if isinstance(raw, dict):
            if isinstance(raw.get("content"), str):
                return raw["content"].strip()
            if isinstance(raw.get("text"), str):
                return raw["text"].strip()
            message = raw.get("message")
            if isinstance(message, dict) and isinstance(message.get("content"), str):
                return message["content"].strip()
        return ""

    @staticmethod
    def _clean_truncate(raw: str, max_chars: int) -> str:
        raw = " ".join(str(raw).split())
        if len(raw) <= max_chars:
            return raw
        cut = raw[:max_chars]
        sentence_end = max(cut.rfind("."), cut.rfind("!"), cut.rfind("?"))
        if sentence_end > max_chars * 0.45:
            return cut[: sentence_end + 1]
        last_space = cut.rfind(" ")
        if last_space > max_chars * 0.50:
            return cut[:last_space].rstrip(",;:") + "..."
        return cut.rstrip(",;:") + "..."

    def generate_expression(self, request) -> str:
        constraints = request.expression_constraints if isinstance(request.expression_constraints, dict) else {}
        max_chars = int(constraints.get("max_chars", 200))
        try:
            raw = self.chat(build_expression_messages(request))
            text = self._extract_text(raw)
            if text:
                self._actual_provider = self.provider_name
                self._fallback_reason = None
                return self._clean_truncate(text, max_chars)
            self._fallback_reason = "external renderer returned no response text"
        except Exception as exc:
            self._fallback_reason = f"external renderer failed ({type(exc).__name__})"
        self._actual_provider = "offline"
        return self._offline.render_expression_request(request, max_chars=max_chars)
