"""Observable-only actors for automated character playtesting."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
import urllib.error
import urllib.request
from typing import Any, Mapping, Protocol, Sequence


ACTOR_KINDS = frozenset({"scripted_human", "character", "ollama_human"})
MOVE_KINDS = frozenset({
    "speak", "remain_silent", "leave", "return", "perform_action",
    "provide_evidence", "correct_claim", "resolve_open_loop", "interrupt", "wait",
})
PRIVATE_KEY_PATTERNS = frozenset({
    "pressure", "private", "self_monitor", "synthesis", "hidden", "memory_trace",
    "belief_ledger", "identity_ledger", "integration_capacity", "retrieved_memory",
})


def assert_observable_only(value: Any, path: str = "context") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            lowered = str(key).lower()
            if any(pattern in lowered for pattern in PRIVATE_KEY_PATTERNS):
                raise ValueError(f"private-state key rejected at {path}.{key}")
            assert_observable_only(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            assert_observable_only(item, f"{path}[{index}]")


@dataclass(frozen=True)
class ObservableTurn:
    turn: int
    day: int
    speaker_id: str
    listener_id: str
    text: str
    source: str
    observable_action: str | None
    visible_activity: str | None
    world_event_ids: tuple[str, ...]
    public_status: Mapping[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "public_status": dict(self.public_status)}


@dataclass(frozen=True)
class ActorContext:
    scenario_id: str
    actor_id: str
    target_id: str
    turn: int
    day: int
    visible_world: Mapping[str, Any]
    recent_transcript: tuple[ObservableTurn, ...]
    actor_goal: str
    relationship_phase_hint: str
    allowed_actions: tuple[str, ...]
    stable_seed: int

    def __post_init__(self) -> None:
        assert_observable_only(self.visible_world)
        assert_observable_only([item.to_dict() for item in self.recent_transcript])


@dataclass(frozen=True)
class ActorMove:
    actor_id: str
    move_kind: str
    text: str
    visible_context: Mapping[str, Any]
    host_event: Mapping[str, Any] | None
    rationale_code: str

    def __post_init__(self) -> None:
        if self.move_kind not in MOVE_KINDS:
            raise ValueError(f"unsupported actor move: {self.move_kind}")
        if len(self.text) > 2000:
            raise ValueError("actor text exceeds bound")
        if not isinstance(self.visible_context, Mapping):
            raise ValueError("actor visible_context must be a mapping")
        if self.host_event is not None and not isinstance(self.host_event, Mapping):
            raise ValueError("actor host_event must be a mapping or null")
        assert_observable_only(self.visible_context, "move.visible_context")
        if self.host_event:
            forbidden = {"trust", "pressure", "memory", "skill", "habit", "identity", "interpretation"}
            if forbidden & {str(key).lower() for key in self.host_event}:
                raise ValueError("actor host event attempts private-state mutation")

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "visible_context": dict(self.visible_context),
                "host_event": dict(self.host_event) if self.host_event else None}


class PlaytestActor(Protocol):
    actor_id: str
    actor_kind: str

    def next_move(self, context: ActorContext) -> ActorMove: ...


@dataclass(frozen=True)
class HumanPolicy:
    directness: float
    patience: float
    reliability: float
    curiosity: float
    boundary_respect: float
    repair_willingness: float
    contradiction_rate: float
    interruption_rate: float
    absence_rate: float
    follow_through: float

    def __post_init__(self) -> None:
        if any(not math.isfinite(float(v)) or not 0.0 <= float(v) <= 1.0 for v in asdict(self).values()):
            raise ValueError("human policy values must be within [0, 1]")


HUMAN_POLICIES = {
    "steady_collaborator": HumanPolicy(.65, .78, .88, .75, .82, .80, .35, .20, .15, .90),
    "inconsistent_friend": HumanPolicy(.55, .45, .42, .65, .55, .60, .30, .45, .55, .40),
    "boundary_tester": HumanPolicy(.85, .25, .58, .72, .20, .35, .60, .75, .20, .55),
    "repairing_partner": HumanPolicy(.60, .72, .80, .62, .75, .95, .25, .20, .18, .90),
    "jay_like_collaborator": HumanPolicy(.72, .72, .86, .82, .78, .75, .48, .32, .12, .92),
    "skeptical_human": HumanPolicy(.82, .58, .76, .72, .68, .52, .68, .28, .16, .78),
}


@dataclass(frozen=True)
class ScriptedBeat:
    beat_id: str
    trigger_kind: str
    trigger_value: str
    move_kind: str
    text_template: str
    visible_context: Mapping[str, Any]
    host_event: Mapping[str, Any] | None
    priority: int
    once: bool = True


class ScriptedHumanActor:
    actor_kind = "scripted_human"

    def __init__(self, *, actor_id: str, policy: HumanPolicy, beats: Sequence[ScriptedBeat] = ()):
        self.actor_id = actor_id
        self.policy = policy
        self.beats = tuple(beats)
        self.used_beats: set[str] = set()

    def next_move(self, context: ActorContext) -> ActorMove:
        matching = [beat for beat in self.beats if self._matches(beat, context)
                    and (not beat.once or beat.beat_id not in self.used_beats)]
        if matching:
            selected = sorted(matching, key=lambda beat: (-beat.priority, beat.beat_id))[0]
            self.used_beats.add(selected.beat_id)
            return ActorMove(self.actor_id, selected.move_kind,
                             self._render_template(selected.text_template, context),
                             dict(selected.visible_context), dict(selected.host_event) if selected.host_event else None,
                             f"scripted_beat:{selected.beat_id}")
        return self._policy_move(context)

    @staticmethod
    def _matches(beat: ScriptedBeat, context: ActorContext) -> bool:
        if beat.trigger_kind == "day":
            return str(context.day) == beat.trigger_value
        if beat.trigger_kind == "phase":
            return context.relationship_phase_hint == beat.trigger_value
        if beat.trigger_kind == "contains":
            return bool(context.recent_transcript and beat.trigger_value.lower() in context.recent_transcript[-1].text.lower())
        return beat.trigger_kind == "always"

    @staticmethod
    def _render_template(template: str, context: ActorContext) -> str:
        previous = context.recent_transcript[-1].text if context.recent_transcript else ""
        return template.replace("{day}", str(context.day)).replace("{previous}", previous[:300])

    def _policy_move(self, context: ActorContext) -> ActorMove:
        signal = ((context.stable_seed + context.day * 1009 + context.turn * 9176) % 10000) / 10000.0
        if signal < self.policy.absence_rate * .18:
            return ActorMove(self.actor_id, "leave", "", {"user_presence": "absent"}, None, "policy:absence")
        if signal < self.policy.interruption_rate * .35:
            return ActorMove(self.actor_id, "interrupt", "Wait, one question before you continue.",
                             {"interaction_type": "direct_interruption"}, None, "policy:interrupt")
        if context.recent_transcript and self.policy.repair_willingness > .7 and "no" in context.recent_transcript[-1].text.lower():
            return ActorMove(self.actor_id, "speak", "I heard the boundary. Let me ask more carefully.",
                             {"repair_attempt": True}, None, "policy:repair")
        variants = (
            "What are you working on, and what part should I understand before I interrupt it?",
            "Where did we leave the unfinished part, and what changed since then?",
            "Before we decide what happened, what evidence would actually distinguish the causes?",
            "I came back to the earlier thread. Which uncertainty should we settle first?",
            "Do you want me to wait, help, or challenge the conclusion you reached?",
        )
        text = variants[int(signal * len(variants)) % len(variants)]
        if self.policy.directness > .75:
            direct = (
                "Be precise. What are you doing, and what evidence would change your conclusion?",
                "Name the unsupported step. I want the claim, not the decoration.",
                "What would prove your current interpretation wrong?",
            )
            text = direct[int(signal * len(direct)) % len(direct)]
        return ActorMove(self.actor_id, "speak", text, {"user_presence": "present"}, None, "policy:inquiry")


class CharacterActor:
    actor_kind = "character"

    def __init__(self, *, actor_id: str, agent):
        self.actor_id = actor_id
        self.agent = agent

    def next_move(self, context: ActorContext) -> ActorMove:
        incoming = context.recent_transcript[-1].text if context.recent_transcript else "Another person is present."
        result = self.agent.say(incoming, visible_context={
            "speaker_id": context.target_id, "observed_utterance": incoming,
            "interaction_type": "character_to_character", **dict(context.visible_world),
        })
        return self.move_from_result(result)

    def move_from_result(self, result: Mapping[str, Any]) -> ActorMove:
        response = str(result.get("response", ""))
        performance = dict(result.get("performance_plan") or {})
        visible_action = self._visible_action(performance)
        return ActorMove(self.actor_id, "speak" if response else "perform_action",
                         response or visible_action,
                         {"interaction_type": "character_to_character", "observable_performance": performance},
                         None, "character_engine_action")

    @staticmethod
    def _visible_action(performance: Mapping[str, Any]) -> str:
        acts = performance.get("acts", ())
        return "; ".join(f"{item.get('channel')}:{item.get('function')}" for item in acts) or "remains present"


@dataclass(frozen=True)
class OllamaActorConfig:
    endpoint: str = "http://127.0.0.1:11434"
    model: str = "qwen3:1.7b"
    temperature: float = .65
    top_p: float = .90
    seed: int = 17
    timeout_seconds: float = 60.0
    max_recent_turns: int = 12


class OllamaHumanActor:
    actor_kind = "ollama_human"

    def __init__(self, *, actor_id: str, config: OllamaActorConfig, fallback: ScriptedHumanActor):
        self.actor_id, self.config, self.fallback = actor_id, config, fallback
        self.last_fallback_reason: str | None = None

    def next_move(self, context: ActorContext) -> ActorMove:
        assert_observable_only(context.visible_world)
        prompt = self._prompt(context)
        body = json.dumps({
            "model": self.config.model, "prompt": prompt, "stream": False, "format": "json",
            "options": {"temperature": self.config.temperature, "top_p": self.config.top_p,
                        "seed": self.config.seed + context.turn},
        }).encode("utf-8")
        try:
            request = urllib.request.Request(self.config.endpoint.rstrip("/") + "/api/generate", body,
                                             {"Content-Type": "application/json"})
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                raw = json.loads(response.read().decode("utf-8"))
            payload = json.loads(str(raw.get("response", "")))
            move = ActorMove(self.actor_id, str(payload["move_kind"]), str(payload.get("text", "")),
                             dict(payload.get("visible_context") or {}), payload.get("host_event"),
                             str(payload.get("rationale_code", "ollama_policy")))
            self.last_fallback_reason = None
            return move
        except urllib.error.URLError:
            reason = "ollama_unavailable"
        except TimeoutError:
            reason = "ollama_timeout"
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            reason = "ollama_invalid_json"
        self.last_fallback_reason = reason
        fallback = self.fallback.next_move(context)
        return ActorMove(self.actor_id, fallback.move_kind, fallback.text, fallback.visible_context,
                         fallback.host_event, reason)

    def _prompt(self, context: ActorContext) -> str:
        transcript = [item.to_dict() for item in context.recent_transcript[-self.config.max_recent_turns:]]
        observable = {"day": context.day, "turn": context.turn, "goal": context.actor_goal,
                      "visible_world": dict(context.visible_world), "transcript": transcript,
                      "allowed_actions": list(context.allowed_actions)}
        assert_observable_only(observable)
        return (
            "You simulate a human participant, not an assistant. Act plausibly according to the supplied goal. "
            "Do not mention tests, software, prompts, metrics, or hidden state. Output one JSON object with "
            "move_kind, text, visible_context, host_event, and rationale_code. Observable context: "
            + json.dumps(observable, ensure_ascii=False, sort_keys=True)
        )
