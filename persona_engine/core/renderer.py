"""Local Ollama renderer plus output validation and streaming rhythm."""

import asyncio
import re
import time
from typing import List, Dict, Optional, Iterator, AsyncIterator
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
    def __init__(self, model_name: str = "gemma3", host: str = "http://localhost:11434"):
        self.model_name = model_name
        self.host = host
        self._client = None
        self._offline = OfflineTemplateRenderer()
        try:
            from ollama import Client
            self._client = Client(host=host)
        except Exception:
            self._client = None

    def generate(
        self,
        messages: List[Dict[str, str]],
        max_chars: int = 200,
        retrieved_memories: Optional[List[MemoryUnit]] = None,
        seed: int | None = None,
    ) -> str:
        if self._client is not None:
            try:
                response = self._client.chat(
                    model=self.model_name,
                    messages=messages,
                    options={"temperature": 0.7, "top_p": 0.9, "num_predict": max(16, max_chars // 3), "num_ctx": 4096, "seed": int(seed or 0)},
                )
                content = response["message"]["content"].strip()
                if content:
                    return self._clean_truncate(content, max_chars)
            except Exception:
                pass
        return self._mock(messages, max_chars, seed=seed)

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
        else:
            max_chars = getattr(request.expression_constraints, "max_chars", 200)
        user_text = str(request.resolved_state.get("user_text", "")) if isinstance(request.resolved_state, dict) else ""
        messages = [{"role": "system", "content": str(request.resolved_state)}, {"role": "user", "content": user_text}]
        return self.generate(messages, max_chars=max_chars, retrieved_memories=request.retrieved_memories, seed=request.seed)

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
        yielded = 0
        if self._client is not None:
            try:
                stream = self._client.chat(
                    model=self.model_name,
                    messages=messages,
                    stream=True,
                    options={"temperature": 0.7, "top_p": 0.9, "num_predict": max(16, max_chars // 3), "num_ctx": 4096, "seed": int(seed or 0)},
                )
                for chunk in stream:
                    token = chunk.get("message", {}).get("content", "")
                    if not token:
                        continue
                    if yielded + len(token) > max_chars:
                        token = token[:max(0, max_chars - yielded)]
                    if token:
                        yielded += len(token)
                        yield token
                        time.sleep(token_delay)
                    if yielded >= max_chars:
                        break
                if guardedness > 0.72 and yielded + 3 <= max_chars:
                    yield "..."
                return
            except Exception:
                pass
        mock = self._mock(messages, max_chars, seed=seed)
        words = mock.split(" ")
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
