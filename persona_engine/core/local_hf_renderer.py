"""Local Hugging Face renderer implementing the cognition renderer contract.

This module is intentionally lazy-imported and optional. The normal test suite
must not require transformers, peft, GPU, network, or a downloaded model.
"""

from __future__ import annotations

import json
from typing import Any

from .cognition_schemas import Impulse, PrivateCognitionProposal
from .model_registry import ModelRegistryEntry, resolve_model
from .renderer import LocalLLMRenderer
from .renderer_contract import ExpressionRequest, PrivateCognitionRequest, PrivateCognitionResult


def _zero_proposal() -> PrivateCognitionProposal:
    return PrivateCognitionProposal(
        prose="",
        attention_targets=[],
        pressure_deltas={},
        impulse_candidates=[],
        memory_activation_requests=[],
        cognitive_theme_ids=[],
    )


class LocalHFRenderer:
    """HF/PEFT-backed renderer seam.

    This proves loading and task separation only. It does not train adapters.
    Any malformed cognition output fails closed to a zero-effect proposal.
    """

    def __init__(
        self,
        model_name: str,
        *,
        registry_entry: ModelRegistryEntry | None = None,
        device_map: str | dict | None = "auto",
        torch_dtype: Any = None,
        max_new_tokens: int = 256,
    ):
        self.model_name = model_name
        self.entry = registry_entry or resolve_model(model_name)
        if self.entry.backend != "hf":
            raise ValueError(f"LocalHFRenderer requires an hf registry entry, got {self.entry.backend!r}")
        self.device_map = device_map
        self.torch_dtype = torch_dtype
        self.max_new_tokens = max_new_tokens
        self._tokenizer = None
        self._model = None
        self._fallback = LocalLLMRenderer(model_name="missing-model-for-mock")

    def load(self):
        if self._model is not None and self._tokenizer is not None:
            return self
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError("LocalHFRenderer requires optional transformers install") from exc

        tokenizer_id = self.entry.tokenizer_id or self.entry.base_model_id
        self._tokenizer = AutoTokenizer.from_pretrained(
            tokenizer_id,
            revision=self.entry.revision,
            local_files_only=self.entry.local_files_only,
        )
        model = AutoModelForCausalLM.from_pretrained(
            self.entry.base_model_id,
            revision=self.entry.revision,
            local_files_only=self.entry.local_files_only,
            device_map=self.device_map,
            torch_dtype=self.torch_dtype,
        )
        if self.entry.adapter_path:
            try:
                from peft import PeftModel
            except ImportError as exc:
                raise RuntimeError("LocalHFRenderer adapter loading requires optional peft install") from exc
            model = PeftModel.from_pretrained(model, self.entry.adapter_path, local_files_only=self.entry.local_files_only)
        self._model = model
        return self

    def _generate_text(self, prompt: str, *, seed: int | None, max_new_tokens: int | None = None) -> str:
        self.load()
        inputs = self._tokenizer(prompt, return_tensors="pt")
        if hasattr(inputs, "to") and hasattr(self._model, "device"):
            inputs = inputs.to(self._model.device)
        kwargs = {
            "max_new_tokens": int(max_new_tokens or self.max_new_tokens),
            "do_sample": False,
        }
        output = self._model.generate(**inputs, **kwargs)
        return self._tokenizer.decode(output[0], skip_special_tokens=True)

    def _private_cognition_prompt(self, request: PrivateCognitionRequest) -> str:
        payload = {
            "task": "private_cognition",
            "ledger_digest": request.ledger_digest,
            "active_state": request.active_state,
            "arc_context": request.arc_context,
            "evidence": request.evidence,
            "retrieved_memories": request.retrieved_memories,
            "allowed_output_schema": {
                "prose": "string",
                "attention_targets": ["string"],
                "pressure_deltas": {"pressure_name": "float"},
                "impulse_candidates": [{"type": "string", "strength": "float", "target": "string"}],
                "memory_activation_requests": ["theme_id"],
                "cognitive_theme_ids": ["theme_id"],
            },
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)

    def _expression_prompt(self, request: ExpressionRequest) -> str:
        return json.dumps({
            "task": "expression",
            "ledger_digest": request.ledger_digest,
            "resolved_state": request.resolved_state,
            "arc_context": request.arc_context,
            "evidence": request.evidence,
            "retrieved_memories": request.retrieved_memories,
            "private_thought_context": request.private_thought_context,
            "decision_payload": request.decision_payload,
            "expression_constraints": request.expression_constraints,
            "deception_obligations": request.deception_obligations,
        }, ensure_ascii=False, sort_keys=True)

    def _parse_private_cognition_json(self, text: str) -> PrivateCognitionProposal:
        try:
            def _reject_constant(value: str):
                raise ValueError(f"non-json constant: {value}")

            data = json.loads(text.strip(), parse_constant=_reject_constant)
            if not isinstance(data, dict):
                return _zero_proposal()
            impulses = []
            for item in data.get("impulse_candidates", []) or []:
                if not isinstance(item, dict):
                    return _zero_proposal()
                impulses.append(Impulse(
                    type=str(item["type"]),
                    strength=float(item["strength"]),
                    target=str(item["target"]),
                ))
            return PrivateCognitionProposal(
                prose=str(data.get("prose", "")),
                attention_targets=[str(x) for x in data.get("attention_targets", []) or []],
                pressure_deltas={str(k): float(v) for k, v in (data.get("pressure_deltas", {}) or {}).items()},
                impulse_candidates=impulses,
                memory_activation_requests=[str(x) for x in data.get("memory_activation_requests", []) or []],
                cognitive_theme_ids=[str(x) for x in data.get("cognitive_theme_ids", []) or []],
            )
        except Exception:
            return _zero_proposal()

    def generate_private_cognition(self, request: PrivateCognitionRequest) -> PrivateCognitionResult:
        try:
            text = self._generate_text(self._private_cognition_prompt(request), seed=request.seed)
            proposal = self._parse_private_cognition_json(text)
            return PrivateCognitionResult(proposal=proposal, diagnostics={"backend": "hf", "model_name": self.model_name})
        except Exception as exc:
            return PrivateCognitionResult(
                proposal=_zero_proposal(),
                diagnostics={"backend": "hf", "model_name": self.model_name, "failed_closed": True, "error": type(exc).__name__},
            )

    def generate_expression(self, request: ExpressionRequest) -> str:
        try:
            if isinstance(request.expression_constraints, dict):
                max_chars = int(request.expression_constraints.get("max_chars", 200))
            else:
                max_chars = int(getattr(request.expression_constraints, "max_chars", 200))
            text = self._generate_text(self._expression_prompt(request), seed=request.seed, max_new_tokens=max(16, max_chars // 3))
            return self._fallback._clean_truncate(text, max_chars)
        except Exception:
            return self._fallback.generate_expression(request)
