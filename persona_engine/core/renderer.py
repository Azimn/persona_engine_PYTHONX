"""Local Ollama renderer plus output validation and streaming rhythm."""

import asyncio
import json
import re
import time
from typing import AsyncIterator, Dict, Iterator, List, Optional
from urllib.request import Request, urlopen

from .cognition_schemas import DeceptionAuthorization, PrivateCognitionProposal
from .deception_ledger import DeceptionLedger
from .memory import MemoryUnit
from .offline_template_renderer import OfflineTemplateRenderer
from .renderer_contract import ExpressionRequest, PrivateCognitionRequest, PrivateCognitionResult


class OutputValidator:
    def check(
        self,
        text: str,
        retrieved_memories: Optional[List[MemoryUnit]] = None,
        authorization: DeceptionAuthorization | None = None,
        deception_ledger: DeceptionLedger | None = None,
        decision_payload: dict | None = None,
        forbidden_self_claims: tuple[str, ...] = (),
    ) -> List[str]:
        lowered = text.lower()
        violations = []
        for claim in forbidden_self_claims:
            normalized = claim.strip().lower()
            if normalized and normalized in lowered:
                violations.append(f"self_model_conflict:{claim}")
        retrieved_memories = retrieved_memories or []
        memory_text = " ".join(memory.content.lower() for memory in retrieved_memories)
        claims = re.findall(r"\bi remember\s+([^.!?]+)", lowered)
        for claim in claims:
            claim_words = {word for word in re.findall(r"[a-z0-9']+", claim) if len(word) > 3}
            if claim_words and not any(word in memory_text for word in claim_words):
                if authorization is not None and authorization.may_fabricate_memory:
                    scope_text = " ".join(authorization.permitted_claim_scope).lower()
                    topic_text = authorization.topic.lower()
                    if any(word in scope_text or word in topic_text for word in claim_words):
                        continue
                    violations.append(f"unauthorized_fabrication:{claim[:40]}")
                elif authorization is not None:
                    violations.append(f"unauthorized_fabrication:{claim[:40]}")
                else:
                    violations.append(f"false_memory_claim:{claim[:40]}")
        for phrase in ["you always", "you never"]:
            if phrase in lowered and phrase not in memory_text:
                violations.append(f"unsupported_absolute:{phrase}")
        if re.search(r"\bi know (exactly )?what you (think|feel|want)\b", lowered):
            violations.append("unsupported_private_user_state")
        if deception_ledger is not None:
            reveal_allowed = (decision_payload or {}).get("dialogue_act") in {"reveal", "confess"}
            for active in deception_ledger.claims:
                if active.status != "active":
                    continue
                obligation = active.consistency_obligation.lower()
                spoken = active.spoken_claim.lower()
                if reveal_allowed and any(word in lowered for word in ["truth", "lied", "confess", "reveal"]):
                    continue
                if obligation and obligation not in lowered and spoken and spoken not in lowered:
                    if active.topic.lower() in lowered or active.audience.lower() in lowered:
                        violations.append(f"deception_contradiction:{active.claim_id}")
        return violations

    def sanitize(self, text: str, forbidden_self_claims: tuple[str, ...] = ()) -> str:
        for claim in forbidden_self_claims:
            normalized = claim.strip()
            if normalized:
                text = re.sub(re.escape(normalized), "...", text, flags=re.IGNORECASE)
        text = re.sub(
            r"\bI remember\s+[^.!?]+[.!?]?",
            "Something about that remains with me.",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(r"\byou always\b", "you seem to", text, flags=re.IGNORECASE)
        text = re.sub(r"\byou never\b", "you rarely", text, flags=re.IGNORECASE)
        text = re.sub(
            r"\bI know exactly what you (think|feel|want)\b",
            "I can only infer so much",
            text,
            flags=re.IGNORECASE,
        )
        return text.strip()


class LocalLLMRenderer:
    def __init__(
        self,
        model_name: str = "gemma3",
        host: str = "http://localhost:11434",
        provider: str | None = None,
        thinking_mode: str = "auto",
        timeout_seconds: float = 60.0,
        token_budget: int = 256,
        opener=urlopen,
    ):
        self.model_name = model_name
        self.host = host.rstrip("/")
        self.provider = provider or ("offline" if model_name.startswith("missing-model-for-mock") else "ollama")
        self.thinking_mode = thinking_mode
        self.timeout_seconds = float(timeout_seconds)
        self.token_budget = int(token_budget)
        self._opener = opener
        self._offline = OfflineTemplateRenderer()
        self._actual_backend = "offline" if self.provider == "offline" else "pending"
        self._fallback_reason = None

    def runtime_status(self) -> dict:
        return {
            "requested_provider": self.provider,
            "actual_provider": self._actual_backend,
            "model_name": self.model_name,
            "thinking_mode": self.thinking_mode,
            "timeout_seconds": self.timeout_seconds,
            "token_budget": self.token_budget,
            "fallback_reason": self._fallback_reason,
        }

    def _ollama_chat(self, messages: List[Dict[str, str]], seed: int | None) -> str:
        options = {
            "temperature": 0.7,
            "top_p": 0.9,
            "num_predict": self.token_budget,
            "num_ctx": 4096,
            "seed": int(seed or 0),
        }
        payload = {"model": self.model_name, "messages": messages, "stream": False, "options": options}
        if self.thinking_mode != "auto":
            payload["think"] = self.thinking_mode == "on"
        request = Request(
            f"{self.host}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        with self._opener(request, timeout=self.timeout_seconds) as response:
            result = json.loads(response.read().decode("utf-8"))
        return str(result.get("message", {}).get("content", "")).strip()

    def generate(
        self,
        messages: List[Dict[str, str]],
        max_chars: int = 200,
        retrieved_memories: Optional[List[MemoryUnit]] = None,
        seed: int | None = None,
    ) -> str:
        if self.provider == "ollama":
            try:
                content = self._ollama_chat(messages, seed)
                if content:
                    self._actual_backend = "ollama"
                    self._fallback_reason = None
                    return self._clean_truncate(content, max_chars)
                self._fallback_reason = "Ollama returned no final response text."
            except Exception as exc:
                self._fallback_reason = f"Ollama request failed ({type(exc).__name__})."
        else:
            self._fallback_reason = None
        self._actual_backend = "offline"
        return self._offline.render(messages, max_chars=max_chars, seed=seed)

    def generate_private_cognition(self, request: PrivateCognitionRequest) -> PrivateCognitionResult:
        proposal = PrivateCognitionProposal(
            prose="",
            attention_targets=[],
            pressure_deltas={},
            impulse_candidates=[],
            memory_activation_requests=[],
            cognitive_theme_ids=[],
        )
        return PrivateCognitionResult(proposal=proposal, diagnostics={"backend": "mock_noop"})

    def generate_expression(self, request: ExpressionRequest) -> str:
        if isinstance(request.expression_constraints, dict):
            max_chars = int(request.expression_constraints.get("max_chars", 200))
        else:
            max_chars = int(getattr(request.expression_constraints, "max_chars", 200))

        resolved = request.resolved_state if isinstance(request.resolved_state, dict) else {}
        user_text = str(resolved.get("user_text", ""))
        system_prompt = str(resolved.get("system_prompt", ""))
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_text}]

        if self.provider == "ollama":
            try:
                content = self._ollama_chat(messages, request.seed)
                if content:
                    self._actual_backend = "ollama"
                    self._fallback_reason = None
                    return self._clean_truncate(content, max_chars)
                self._fallback_reason = "Ollama returned no final response text."
            except Exception as exc:
                self._fallback_reason = f"Ollama request failed ({type(exc).__name__})."
        else:
            self._fallback_reason = None

        self._actual_backend = "offline"
        return self._offline.render_expression_request(request, max_chars=max_chars)

    def generate_stream(
        self,
        messages: List[Dict[str, str]],
        envelope=None,
        max_chars: int = 200,
        seed: int | None = None,
    ) -> Iterator[str]:
        guardedness = getattr(envelope, "guardedness", 0.5) if envelope else 0.5
        warmth = getattr(envelope, "warmth", 0.5) if envelope else 0.5
        initial_delay = min(1.2, 0.05 + guardedness * 0.25)
        token_delay = min(0.12, 0.005 + (1.0 - warmth) * 0.025)
        time.sleep(initial_delay)
        rendered = self.generate(messages, max_chars=max_chars, seed=seed)
        for index, word in enumerate(rendered.split(" ")):
            yield word if index == 0 else " " + word
            time.sleep(token_delay)

    async def generate_stream_async(
        self,
        messages: List[Dict[str, str]],
        envelope=None,
        max_chars: int = 200,
        seed: int | None = None,
    ) -> AsyncIterator[str]:
        guardedness = getattr(envelope, "guardedness", 0.5) if envelope else 0.5
        warmth = getattr(envelope, "warmth", 0.5) if envelope else 0.5
        await asyncio.sleep(min(1.2, 0.05 + guardedness * 0.25))
        token_delay = min(0.12, 0.005 + (1.0 - warmth) * 0.025)
        for token in self.generate_stream(messages, envelope=envelope, max_chars=max_chars, seed=seed):
            yield token
            await asyncio.sleep(token_delay)

    def _clean_truncate(self, raw: str, max_chars: int) -> str:
        raw = " ".join(raw.split())
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

    def _mock(self, messages, max_chars, error: Optional[str] = None, seed: int | None = None) -> str:
        return self._offline.render(messages, max_chars=max_chars, seed=seed)


def render_expression(
    renderer,
    ledger_digest,
    resolved_state,
    arc_context,
    evidence,
    retrieved_memories,
    private_thought_context,
    decision_payload,
    expression_constraints,
    deception_obligations,
    seed: int | None = None,
) -> str:
    """Render expression from an already resolved decision payload."""

    request = ExpressionRequest(
        ledger_digest=ledger_digest,
        resolved_state=resolved_state,
        arc_context=arc_context,
        evidence=evidence,
        retrieved_memories=retrieved_memories,
        private_thought_context=private_thought_context,
        decision_payload=decision_payload,
        expression_constraints=expression_constraints,
        deception_obligations=deception_obligations,
        seed=seed,
    )
    if hasattr(renderer, "generate_expression"):
        return renderer.generate_expression(request)

    lines = [
        f"Resolved decision: {decision_payload}",
        f"Ledger digest: {ledger_digest}",
        f"Resolved state: {resolved_state}",
        f"Arc context: {arc_context}",
        f"Evidence: {evidence}",
        f"Private thought context: {private_thought_context}",
        f"Expression constraints: {expression_constraints}",
        f"Deception obligations: {deception_obligations}",
    ]
    user_text = str(resolved_state.get("user_text", "")) if isinstance(resolved_state, dict) else ""
    messages = [{"role": "system", "content": "\n".join(lines)}, {"role": "user", "content": user_text}]
    if isinstance(expression_constraints, dict):
        max_chars = expression_constraints.get("max_chars", 200)
    else:
        max_chars = getattr(expression_constraints, "max_chars", 200)
    return renderer.generate(
        messages,
        max_chars=max_chars,
        retrieved_memories=retrieved_memories,
        seed=seed,
    )
