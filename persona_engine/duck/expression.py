"""Renderer-agnostic realization of already-selected DUCK communication actions.

Expression is an execution-stage transformation, not a second decision system.
A language model may realize an intention in words, but it may not change the
action type, subject identity, canonical memory, relationship state, or selected
semantic decision. The rendered result is recorded as execution evidence.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
from typing import Any, Callable, Protocol

from .types import CandidateAction


@dataclass(frozen=True)
class ExpressionContext:
    tick: int
    subject_id: str
    action_id: str
    parameters: dict[str, Any]
    trigger: dict[str, Any]
    situation: dict[str, Any]
    subject: dict[str, Any]
    broadcast: dict[str, Any] | None = None
    max_chars: int = 500

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExpressionResult:
    text: str
    provider: str
    model: str
    seed: int
    validation_issues: tuple[str, ...] = ()
    fallback_used: bool = False
    diagnostics: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExpressionPort(Protocol):
    def realize(self, context: ExpressionContext) -> ExpressionResult: ...


class DeterministicExpressionPort:
    """Character-neutral fallback for tests and non-language deployments."""

    provider = "deterministic"
    model = "template"

    def realize(self, context: ExpressionContext) -> ExpressionResult:
        parameters = context.parameters
        text = str(parameters.get("utterance") or parameters.get("response_text") or "").strip()
        if not text:
            user_text = str(parameters.get("user_text") or context.trigger.get("payload", {}).get("observed_text", "")).strip()
            if user_text:
                text = "I am considering what you said."
            else:
                text = "I wanted to check in."
        text = text[: max(1, int(context.max_chars))]
        return ExpressionResult(
            text=text,
            provider=self.provider,
            model=self.model,
            seed=stable_expression_seed(context.subject_id, context.tick, context.action_id),
            fallback_used=True,
            diagnostics={"reason": "deterministic_expression_port"},
        )


class WayfarerExpressionPort:
    """Use Wayfarer's renderer as a replaceable expression substrate only."""

    def __init__(self, agent, *, max_chars: int = 500):
        self.agent = agent
        self.max_chars = max(32, int(max_chars))

    def realize(self, context: ExpressionContext) -> ExpressionResult:
        from persona_engine.core.renderer import render_expression

        engine = self.agent.engine
        seed = stable_expression_seed(context.subject_id, context.tick, context.action_id)
        status = self.agent.engine.renderer_status()
        decision = {
            "dialogue_act": str(context.parameters.get("dialogue_act", "respond")),
            "semantic_goal": str(context.parameters.get("semantic_goal", "respond_to_current_event")),
            "selected_by": "duck_action_selector",
            "action_id": context.action_id,
            "disclosure": dict(context.parameters.get("disclosure", {})),
            "commitment_evidence": dict(context.parameters.get("commitment_evidence", {})),
        }
        subject_snapshot = dict(context.subject or {})
        identity_name = str(
            subject_snapshot.get("identity", {}).get("name", "")
            if isinstance(subject_snapshot.get("identity"), dict)
            else subject_snapshot.get("name", "")
        )
        if not identity_name:
            identity_name = str(getattr(engine.identity, "name", ""))
        ledger_digest = {
            "identity": identity_name,
            "subject_id": context.subject_id,
            "authored_identity": {
                "name": str(getattr(engine.identity, "name", identity_name)),
                "core_beliefs": list(getattr(engine.identity, "core_beliefs", ()) or ()),
                "temperament": str(getattr(engine.identity, "temperament", "")),
                "moral_boundaries": list(getattr(engine.identity, "moral_boundaries", ()) or ()),
                "speech_constraints": list(getattr(engine.identity, "speech_constraints", ()) or ()),
                "forbidden_self_claims": list(getattr(engine.identity, "forbidden_self_claims", ()) or ()),
            },
        }
        trigger_payload = context.trigger.get("payload", {}) if isinstance(context.trigger, dict) else {}
        user_text = str(context.parameters.get("user_text") or trigger_payload.get("observed_text") or trigger_payload.get("description") or "")
        resolved_state = {
            "user_text": user_text,
            "experience_context": {
                "relationship": subject_snapshot.get("relationship", {}),
                "duck_situation": context.situation,
                "workspace_broadcast": context.broadcast,
            },
        }
        rendered = render_expression(
            engine.renderer,
            ledger_digest=ledger_digest,
            resolved_state=resolved_state,
            arc_context={"duck_tick": context.tick},
            evidence=[],
            retrieved_memories=[],
            private_thought_context="",
            decision_payload=decision,
            expression_constraints={"max_chars": min(self.max_chars, context.max_chars)},
            deception_obligations={},
            seed=seed,
        )
        forbidden = tuple(getattr(engine.identity, "forbidden_self_claims", ()) or ())
        issues = tuple(engine.validator.check(rendered, retrieved_memories=[], forbidden_self_claims=forbidden))
        fallback_used = False
        if issues:
            rendered = engine.validator.sanitize(rendered, forbidden_self_claims=forbidden)
            fallback_used = True
        final_status = self.agent.engine.renderer_status()
        return ExpressionResult(
            text=str(rendered).strip(),
            provider=str(final_status.get("actual_provider") or final_status.get("requested_provider") or status.get("actual_provider") or "unknown"),
            model=str(final_status.get("model_name") or status.get("model_name") or type(engine.renderer).__name__),
            seed=seed,
            validation_issues=issues,
            fallback_used=fallback_used,
            diagnostics={"renderer_status": final_status, "contract": "wayfarer-expression-bridge"},
        )


ArchiveLookup = Callable[[str], dict[str, Any] | None]


class ExpressionJournal:
    """Bounded hot cache of rendered speech with optional durable archive lookup."""

    DEFAULT_MAX_ROWS = 256

    def __init__(
        self,
        rows: dict[str, dict[str, Any]] | None = None,
        *,
        max_rows: int = DEFAULT_MAX_ROWS,
        order: list[str] | tuple[str, ...] | None = None,
        archive_lookup: ArchiveLookup | None = None,
    ):
        self.max_rows = max(1, int(max_rows))
        self.archive_lookup = archive_lookup
        self.rows: dict[str, dict[str, Any]] = {}
        self.order: list[str] = []
        source = {str(key): dict(value) for key, value in (rows or {}).items()}
        if order:
            ordered = [str(key) for key in order if str(key) in source]
            seen = set(ordered)
            ordered.extend(key for key in sorted(source, key=self._legacy_sort_key) if key not in seen)
        else:
            ordered = sorted(source, key=self._legacy_sort_key)
        for key in ordered:
            self._store_raw(key, source[key])

    @staticmethod
    def _legacy_sort_key(speech_id: str) -> tuple[int, str]:
        parts = str(speech_id).split(":", 2)
        try:
            tick = int(parts[1]) if len(parts) > 1 else -1
        except (TypeError, ValueError):
            tick = -1
        return tick, str(speech_id)

    @staticmethod
    def _decode(raw: dict[str, Any]) -> ExpressionResult:
        return ExpressionResult(
            text=str(raw.get("text", "")),
            provider=str(raw.get("provider", "recorded")),
            model=str(raw.get("model", "recorded")),
            seed=int(raw.get("seed", 0)),
            validation_issues=tuple(raw.get("validation_issues", []) or ()),
            fallback_used=bool(raw.get("fallback_used", False)),
            diagnostics=dict(raw.get("diagnostics", {}) or {}),
        )

    def _store_raw(self, speech_id: str, raw: dict[str, Any]) -> None:
        key = str(speech_id)
        if key in self.rows:
            try:
                self.order.remove(key)
            except ValueError:
                pass
        self.rows[key] = dict(raw)
        self.order.append(key)
        while len(self.order) > self.max_rows:
            evicted = self.order.pop(0)
            self.rows.pop(evicted, None)

    def get(self, speech_id: str) -> ExpressionResult | None:
        key = str(speech_id)
        raw = self.rows.get(key)
        if raw is None and self.archive_lookup is not None:
            archived = self.archive_lookup(key)
            if archived:
                self._store_raw(key, archived)
                raw = self.rows.get(key)
        if not raw:
            return None
        return self._decode(raw)

    def put(self, speech_id: str, result: ExpressionResult) -> None:
        self._store_raw(str(speech_id), result.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_rows": self.max_rows,
            "order": list(self.order),
            "rows": {key: dict(self.rows[key]) for key in self.order if key in self.rows},
        }

    @classmethod
    def from_dict(
        cls,
        raw: dict[str, Any] | None,
        *,
        max_rows: int | None = None,
        archive_lookup: ArchiveLookup | None = None,
    ) -> "ExpressionJournal":
        raw = dict(raw or {})
        persisted_limit = int(raw.get("max_rows", cls.DEFAULT_MAX_ROWS) or cls.DEFAULT_MAX_ROWS)
        return cls(
            raw.get("rows", {}),
            max_rows=persisted_limit if max_rows is None else max_rows,
            order=raw.get("order", []),
            archive_lookup=archive_lookup,
        )


class ExpressionActionPreparer:
    """Render only after action selection and preserve action identity/type."""

    def __init__(self, port: ExpressionPort, journal: ExpressionJournal):
        self.port = port
        self.journal = journal

    def prepare(self, action: CandidateAction, context: dict[str, Any]) -> tuple[CandidateAction, dict[str, Any]]:
        if action.action_type != "communicate":
            return action, {}
        speech_id = f"speech:{context.get('tick', 0)}:{action.action_id}"
        expression = self.journal.get(speech_id)
        replayed = expression is not None
        if expression is None:
            expression_context = ExpressionContext(
                tick=int(context.get("tick", 0)),
                subject_id=str(context.get("subject_id") or context.get("subject", {}).get("subject_id") or "unknown"),
                action_id=action.action_id,
                parameters=dict(action.parameters),
                trigger=dict(context.get("trigger", {})),
                situation=dict(context.get("situation", {})),
                subject=dict(context.get("subject", {})),
                broadcast=dict(context.get("broadcast", {})) if context.get("broadcast") else None,
                max_chars=int(action.parameters.get("max_chars", 500) or 500),
            )
            try:
                expression = self.port.realize(expression_context)
            except Exception as exc:
                fallback = DeterministicExpressionPort()
                expression = fallback.realize(expression_context)
                expression = ExpressionResult(
                    text=expression.text,
                    provider=expression.provider,
                    model=expression.model,
                    seed=expression.seed,
                    validation_issues=(f"expression_service:{type(exc).__name__}",),
                    fallback_used=True,
                    diagnostics={"fallback_reason": type(exc).__name__},
                )
            self.journal.put(speech_id, expression)
        parameters = dict(action.parameters)
        parameters.update({
            "utterance": expression.text,
            "speech_id": speech_id,
            "expression_provider": expression.provider,
            "expression_model": expression.model,
            "expression_seed": expression.seed,
        })
        prepared = replace(action, parameters=parameters)
        return prepared, {
            "speech_id": speech_id,
            "expression": expression.to_dict(),
            "expression_replayed": replayed,
        }


def stable_expression_seed(subject_id: str, tick: int, action_id: str) -> int:
    payload = f"{subject_id}|{int(tick)}|{action_id}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:4], "big", signed=False)
