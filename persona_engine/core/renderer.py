"""Local Ollama renderer plus output validation and streaming rhythm."""

import asyncio
import re
import time
from typing import List, Dict, Optional, Iterator, AsyncIterator
from .memory import MemoryUnit


class OutputValidator:
    FORBIDDEN_PHRASES = [
        r"as an ai", r"i am an ai", r"language model",
        r"i don't have (feelings|emotions)", r"i cannot experience",
    ]

    def check(self, text: str, retrieved_memories: Optional[List[MemoryUnit]] = None) -> List[str]:
        lowered = text.lower()
        violations = []
        for p in self.FORBIDDEN_PHRASES:
            if re.search(p, lowered):
                violations.append(f"meta_break:{p}")
        retrieved_memories = retrieved_memories or []
        memory_text = " ".join(m.content.lower() for m in retrieved_memories)
        claims = re.findall(r"i remember\s+([^.!?]+)", lowered)
        for claim in claims:
            claim_words = {w for w in re.findall(r"[a-z0-9']+", claim) if len(w) > 3}
            if claim_words and not any(w in memory_text for w in claim_words):
                violations.append(f"false_memory_claim:{claim[:40]}")
        unsupported_absolutes = ["you always", "you never"]
        for phrase in unsupported_absolutes:
            if phrase in lowered and phrase not in memory_text:
                violations.append(f"unsupported_absolute:{phrase}")
        if re.search(r"i know (exactly )?what you (think|feel|want)", lowered):
            violations.append("unsupported_private_user_state")
        return violations

    def sanitize(self, text: str) -> str:
        for pattern in self.FORBIDDEN_PHRASES:
            text = re.sub(pattern, "...", text, flags=re.IGNORECASE)
        text = re.sub(r"I remember\s+[^.!?]+[.!?]?", "Something about that remains with me.", text, flags=re.IGNORECASE)
        text = re.sub(r"you always", "you seem to", text, flags=re.IGNORECASE)
        text = re.sub(r"you never", "you rarely", text, flags=re.IGNORECASE)
        text = re.sub(r"I know exactly what you (think|feel|want)", "I can only infer so much", text, flags=re.IGNORECASE)
        return text.strip()


class LocalLLMRenderer:
    def __init__(self, model_name: str = "gemma3", host: str = "http://localhost:11434"):
        self.model_name = model_name
        self.host = host
        self._client = None
        try:
            from ollama import Client
            self._client = Client(host=host)
        except Exception:
            self._client = None

    def generate(self, messages: List[Dict[str, str]], max_chars: int = 200, retrieved_memories: Optional[List[MemoryUnit]] = None) -> str:
        if self._client is not None:
            try:
                response = self._client.chat(
                    model=self.model_name,
                    messages=messages,
                    options={"temperature": 0.7, "top_p": 0.9, "num_predict": max(16, max_chars // 3), "num_ctx": 4096, "seed": 42},
                )
                return self._clean_truncate(response["message"]["content"].strip(), max_chars)
            except Exception as e:
                return self._mock(messages, max_chars, error=str(e))
        return self._mock(messages, max_chars)

    def generate_stream(self, messages: List[Dict[str, str]], envelope=None, max_chars: int = 200) -> Iterator[str]:
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
                    options={"temperature": 0.7, "top_p": 0.9, "num_predict": max(16, max_chars // 3), "num_ctx": 4096, "seed": 42},
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
        mock = self._mock(messages, max_chars)
        words = mock.split(" ")
        for i, word in enumerate(words):
            piece = word if i == 0 else " " + word
            yield piece
            time.sleep(token_delay)

    async def generate_stream_async(self, messages: List[Dict[str, str]], envelope=None, max_chars: int = 200) -> AsyncIterator[str]:
        guardedness = getattr(envelope, "guardedness", 0.5) if envelope else 0.5
        warmth = getattr(envelope, "warmth", 0.5) if envelope else 0.5
        await asyncio.sleep(min(1.2, 0.05 + guardedness * 0.25))
        token_delay = min(0.12, 0.005 + (1.0 - warmth) * 0.025)
        for token in self.generate_stream(messages, envelope=envelope, max_chars=max_chars):
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

    def _mock(self, messages, max_chars, error: Optional[str] = None) -> str:
        tag = f"[mock renderer{' - ollama unreachable: ' + error if error else ' - ollama not installed'}] "
        user_msg = messages[-1]["content"] if messages else ""
        return self._clean_truncate(tag + f"(would respond in character to: {user_msg[:60]!r})", max_chars)
