"""Local Ollama renderer plus output validation and streaming rhythm."""

import asyncio
import json
import re
import time
from typing import List, Dict, Optional, Iterator, AsyncIterator
from urllib.request import Request, urlopen
from .cognition_schemas import DeceptionAuthorization, PrivateCognitionProposal
from .deception_ledger import DeceptionLedger
from .memory import MemoryUnit
from .offline_template_renderer import OfflineTemplateRenderer
from .renderer_contract import ExpressionRequest, PrivateCognitionRequest, PrivateCognitionResult


class OutputValidator:
    FORBIDDEN_PHRASES = [
        r"as an ai", r"i am an ai", r"language model",
        r"i don't have (feelings|emotions)", r"i cannot experience",
    ]

    def check(
        self,
        text: str,
        retrieved_memories: Optional[List[MemoryUnit]] = None,
        authorization: DeceptionAuthorization | None = None,
        deception_ledger: DeceptionLedger | None = None,
        decision_payload: dict | None = None,
    ) -> List[str]:
        lowered = text.lower()
        violations = []
        for p in self.FORBIDDEN_PHRASES:
            if re.search(p, lowered):
                violations.append(f"meta_break:{p}")
        retrieved_memories = retrieved_memories or []
        memory_text = " ".join(m.content.lower() for m in retrieved_memories)
        claims = re.findall(r"\bi remember\s+([^.!?]+)", lowered)
        for claim in claims:
            claim_words = {w for w in re.findall(r"[a-z0-9']+", claim) if len(w) > 3}
            if claim_words and not any(w in memory_text for w in claim_words):
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
        unsupported_absolutes = ["you always", "you never"]
        for phrase in unsupported_absolutes:
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

    def sanitize(self, text: str) -> str:
        for pattern in self.FORBIDDEN_PHRASES:
            text = re.sub(pattern, "...", text, flags=re.IGNORECASE)
        text = re.sub(r"\bI remember\s+[^.!?]+[.!?]?", "Something about that remains with me.", text, flags=re.IGNORECASE)
        text = re.sub(r"\byou always\b", "you seem to", text, flags=re.IGNORECASE)
        text = re.sub(r"\byou never\b", "you rarely", text, flags=re.IGNORECASE)
        text = re.sub(r"\bI know exactly what you (think|feel|want)\b", "I can only infer so much", text, flags=re.IGNORECASE)
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
        offline_realization: dict | None = None,
        offline_context: dict | None = None,
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
        return self._mock(
            messages, max_chars, seed=seed, offline_realization=offline_realization,
            offline_context=offline_context,
        )

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
            max_chars = request.expression_constraints.get("max_chars", 200)
            offline_realization = request.expression_constraints.get("offline_realization")
            offline_context = {
                "conversation_move": (
                    request.expression_constraints.get("conversation_candidate") or {}
                ).get("move"),
                "obligation": (
                    request.expression_constraints.get("conversation_candidate") or {}
                ).get("obligation"),
                "extension_move": (
                    request.expression_constraints.get("conversation_candidate") or {}
                ).get("extension_move"),
                "actor_id": request.expression_constraints.get("active_actor_id"),
                "choreography": request.expression_constraints.get("conversation_choreography"),
                "topic_plan": request.expression_constraints.get("offline_topic_plan"),
            }
        else:
            max_chars = getattr(request.expression_constraints, "max_chars", 200)
            offline_realization = getattr(request.expression_constraints, "offline_realization", None)
            offline_context = {}
        if isinstance(request.resolved_state, dict):
            user_text = str(request.resolved_state.get("user_text", ""))
            system_content = str(request.resolved_state.get("system_prompt") or request.resolved_state)
        else:
            user_text = ""
            system_content = str(request.resolved_state)
        messages = [{"role": "system", "content": system_content}, {"role": "user", "content": user_text}]
        grounding_mode = (
            request.expression_constraints.get("memory_grounding_mode", "optional")
            if isinstance(request.expression_constraints, dict) else "optional"
        )
        if grounding_mode == "unavailable":
            self._actual_backend = "offline"
            self._fallback_reason = "No directly relevant memory was available for a memory-grounded answer."
            return self._offline.render(
                messages, max_chars=max_chars, seed=request.seed, realization=offline_realization,
                **offline_context,
            )
        rendered = self.generate(
            messages,
            max_chars=max_chars,
            retrieved_memories=request.retrieved_memories,
            seed=request.seed,
            offline_realization=offline_realization,
            offline_context=offline_context,
        )
        rendered = self._strip_generic_assistant_tail(rendered)
        if self._actual_backend != "offline" and self._echoes_input(rendered, user_text):
            self._actual_backend = "offline"
            self._fallback_reason = "Model output repeated the interlocutor input."
            return self._offline.render(
                messages, max_chars=max_chars, seed=request.seed, realization=offline_realization,
                **offline_context,
            )
        if grounding_mode == "required" and self._actual_backend != "offline" and not self._memory_grounded(
            rendered, user_text, request.retrieved_memories,
        ):
            self._actual_backend = "offline"
            self._fallback_reason = "Model output failed the explicit autobiographical grounding check."
            return self._offline.render(
                messages, max_chars=max_chars, seed=request.seed, realization=offline_realization,
                **offline_context,
            )
        return rendered

    @staticmethod
    def _echoes_input(text: str, user_text: str) -> bool:
        normalize = lambda value: " ".join(re.findall(r"[a-z0-9']+", str(value).casefold()))
        rendered = normalize(text)
        incoming = normalize(user_text)
        return len(incoming) >= 40 and rendered == incoming

    @staticmethod
    def _strip_generic_assistant_tail(text: str) -> str:
        patterns = (
            r"\s+Let me know if\b[^.!?]*[.!?]?\s*$",
            r"\s+How can I help\b[^.!?]*[.!?]?\s*$",
            r"\s+Is there anything else\b[^.!?]*[.!?]?\s*$",
            r"\s+What(?:'|’)s on your mind\?\s*$",
        )
        cleaned = str(text).strip()
        for pattern in patterns:
            candidate = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
            if len(candidate) >= 40:
                cleaned = candidate
        return cleaned

    @staticmethod
    def _memory_grounded(text: str, user_text: str, memories) -> bool:
        stop = {
            "about", "after", "being", "does", "from", "happened", "memory", "memories",
            "remember", "that", "their", "there", "these", "they", "this", "what", "when",
            "where", "which", "with", "would", "your",
        }

        def tokens(value: str) -> set[str]:
            return {item for item in re.findall(r"[a-z0-9']+", value.lower()) if len(item) >= 4 and item not in stop}

        user_tokens = tokens(user_text)
        response_tokens = tokens(text) - user_tokens
        memory_tokens = set()
        for memory in list(memories or ())[:1]:
            content = memory.content if hasattr(memory, "content") else str(memory)
            memory_tokens.update(tokens(content))
        overlap = response_tokens & memory_tokens
        if len(overlap) >= 2:
            return True
        return sum(
            1 for left in response_tokens for right in memory_tokens
            if len(left) >= 6 and len(right) >= 6 and left[:6] == right[:6]
        ) >= 2

    def generate_stream(self, messages: List[Dict[str, str]], envelope=None, max_chars: int = 200, seed: int | None = None) -> Iterator[str]:
        """Synchronous token stream. UIs can render these chunks directly.

        If Ollama is unavailable, this streams the mock response in word chunks so
        timing code can still be tested.
        """
        guardedness = getattr(envelope, "guardedness", 0.5) if envelope else 0.5
        warmth = getattr(envelope, "warmth", 0.5) if envelope else 0.5
        initial_delay = min(1.2, 0.05 + guardedness * 0.25)
        token_delay = min(0.12, 0.005 + (1.0 - warmth) * 0.025)
        time.sleep(initial_delay)
        rendered = self.generate(messages, max_chars=max_chars, seed=seed)
        words = rendered.split(" ")
        for i, word in enumerate(words):
            piece = word if i == 0 else " " + word
            yield piece
            time.sleep(token_delay)

    async def generate_stream_async(self, messages: List[Dict[str, str]], envelope=None, max_chars: int = 200, seed: int | None = None) -> AsyncIterator[str]:
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
            return cut[:sentence_end + 1]
        last_space = cut.rfind(" ")
        if last_space > max_chars * 0.50:
            return cut[:last_space].rstrip(",;:") + "..."
        return cut.rstrip(",;:") + "..."

    def _mock(
        self,
        messages,
        max_chars,
        error: Optional[str] = None,
        seed: int | None = None,
        offline_realization: dict | None = None,
        offline_context: dict | None = None,
    ) -> str:
        return self._offline.render(
            messages,
            max_chars=max_chars,
            seed=seed,
            realization=offline_realization,
            **dict(offline_context or {}),
        )


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
    """Render expression from an already-resolved decision payload."""

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
    user_text = ""
    if isinstance(resolved_state, dict):
        user_text = str(resolved_state.get("user_text", ""))
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
