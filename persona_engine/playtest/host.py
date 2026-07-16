"""Observable host for accelerated scripted and cross-character playtests."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from persona_engine.agent import CharacterAgent

from .actors import (
    ActorContext, ActorMove, CharacterActor, HUMAN_POLICIES, ObservableTurn,
    OllamaActorConfig, OllamaHumanActor, ScriptedBeat, ScriptedHumanActor,
)
from .judges import deterministic_judge, ollama_judge
from .metrics import FailureFinding, evaluate_transcript
from .scenario import DevelopmentalPlaytestScenario


@dataclass(frozen=True)
class DevelopmentalPlaytestResult:
    scenario_id: str
    transcript: tuple[ObservableTurn, ...]
    actor_moves: tuple[ActorMove, ...]
    diagnostics: tuple[Mapping[str, Any], ...]
    timeline: tuple[Mapping[str, Any], ...]
    metrics: Mapping[str, Any]
    failures: tuple[FailureFinding, ...]
    judge_results: Mapping[str, Any]
    state_growth: tuple[Mapping[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id, "transcript": [item.to_dict() for item in self.transcript],
            "actor_moves": [item.to_dict() for item in self.actor_moves],
            "diagnostics": list(self.diagnostics), "timeline": list(self.timeline),
            "metrics": dict(self.metrics), "failures": [item.to_dict() for item in self.failures],
            "judge_results": dict(self.judge_results), "state_growth": list(self.state_growth),
        }


class DevelopmentalPlaytestHost:
    def __init__(self, *, scenario: DevelopmentalPlaytestScenario, cartridges_dir, db_dir,
                 actor_mode: str = "scripted", replay_moves: Sequence[ActorMove] | None = None,
                 ollama_config: OllamaActorConfig | None = None):
        self.scenario = scenario
        self.cartridges_dir, self.db_dir = Path(cartridges_dir), Path(db_dir)
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.actor_mode, self.replay_moves = actor_mode, tuple(replay_moves or ())
        self.ollama_config = ollama_config or OllamaActorConfig()
        self.agents: dict[str, CharacterAgent] = {}
        for item in scenario.participants:
            if item.get("kind") == "character":
                pid = str(item["id"])
                self.agents[pid] = CharacterAgent(
                    cartridge_path=str(self.cartridges_dir / str(item["cartridge"])),
                    user_id=str(item.get("user_id", "playtest_user")),
                    db_path=str(self.db_dir / f"{pid}.db"),
                )

    def run(self, judge: str = "deterministic") -> DevelopmentalPlaytestResult:
        transcript: list[ObservableTurn] = []
        moves: list[ActorMove] = []
        diagnostics: list[dict[str, Any]] = []
        timeline: list[dict[str, Any]] = []
        growth: list[dict[str, Any]] = []
        visible_world: dict[str, Any] = {}
        event_aliases: dict[tuple[str, str], str] = {}
        actors = self._actors()
        turn_number = 0
        event_time = 1_700_000_000.0
        replay_index = 0
        for day in range(1, self.scenario.total_days + 1):
            event_time += 86400.0
            for event in [item for item in self.scenario.scheduled_events if item.day == day]:
                for target in event.targets:
                    if target in self.agents:
                        payload = dict(event.payload)
                        perception = payload.pop("character_perception", None)
                        scheduled_parent = payload.pop("corrects_scheduled_event_id", None)
                        if scheduled_parent:
                            payload["corrects_world_event_id"] = event_aliases.get(
                                (target, str(scheduled_parent)), str(scheduled_parent),
                            )
                        recorded = self.agents[target].record_world_event(
                            event_type=event.event_type, actors=event.actors, targets=event.targets,
                            action=event.action, outcome=event.outcome, source="playtest_director",
                            payload=payload, timestamp=event_time,
                        )
                        event_aliases[(target, event.event_id)] = recorded["event_id"]
                        if event.visible:
                            self.agents[target].perceive_world_event(
                                recorded["event_id"], **dict(perception or {
                                    "attention": .8, "confidence": .8, "salience": .55,
                                    "emotional_residue": "neutral", "interpretation": "ordinary",
                                }),
                            )
                        if event.visible:
                            visible_world[event.event_id] = {"outcome": event.outcome, "event_id": recorded["event_id"]}
                        timeline.append({"day": day, "type": "world_event", "event_id": recorded["event_id"]})
            for local_turn in range(1, self.scenario.max_turns_per_day + 1):
                turn_number += 1
                actor_id, target_id = self._pair_for_turn(turn_number)
                if replay_index < len(self.replay_moves):
                    move = self.replay_moves[replay_index]
                    replay_index += 1
                else:
                    context = ActorContext(
                        self.scenario.scenario_id, actor_id, target_id, turn_number, day,
                        dict(visible_world), tuple(transcript[-12:]), self._goal_for_day(day),
                        self._phase_for_day(day), tuple(sorted({"speak", "interrupt", "wait", "leave", "return"})),
                        self.scenario.stable_seed,
                    )
                    move = actors[actor_id].next_move(context)
                moves.append(move)
                if move.host_event and target_id in self.agents:
                    event = self.agents[target_id].record_world_event(
                        event_type=str(move.host_event.get("event_type", "actor_event")), actors=(actor_id,),
                        targets=(target_id,), action=str(move.host_event.get("action", move.move_kind)),
                        outcome=str(move.host_event.get("outcome", move.text)), source="playtest_actor",
                        payload=dict(move.host_event.get("payload") or {}), timestamp=event_time + local_turn,
                    )
                    visible_world[f"move:{turn_number}"] = {"event_id": event["event_id"], "outcome": event["outcome"]}
                result = self._deliver(target_id, move, event_time + local_turn)
                observable = self._observable_from_result(turn_number, day, actor_id, target_id, move, result)
                transcript.append(observable)
                if result is not None:
                    character_turn = ObservableTurn(
                        turn_number, day, target_id, actor_id, str(result.get("response", "")), "character",
                        self._performance_summary(result), str(result.get("life_context", {}).get("current_activity", "")),
                        (str(result.get("world_event_id", "")),), dict(result.get("public_status") or {}),
                    )
                    transcript.append(character_turn)
                    diagnostics.append(self._diagnostic(day, target_id, result, self.agents[target_id].engine.renderer))
            for pid, agent in self.agents.items():
                state_bytes = len(json.dumps(agent.engine._serialize_state(), sort_keys=True, default=str).encode())
                growth.append({"day": day, "participant_id": pid, "serialized_state_bytes": state_bytes})
        metrics, failures = evaluate_transcript(transcript, diagnostics)
        return DevelopmentalPlaytestResult(
            self.scenario.scenario_id, tuple(transcript), tuple(moves), tuple(diagnostics), tuple(timeline),
            metrics, failures,
            deterministic_judge(transcript) if judge == "deterministic"
            else ollama_judge(transcript, self.ollama_config) if judge == "ollama" else {},
            tuple(growth),
        )

    def _actors(self):
        result = {}
        for item in self.scenario.participants:
            pid = str(item["id"])
            if item.get("kind") == "character" and item.get("acts_as_actor"):
                result[pid] = CharacterActor(actor_id=pid, agent=self.agents[pid])
            elif item.get("kind") != "character":
                profile = str(item.get("policy", "steady_collaborator"))
                actor_profile = dict(self.scenario.actor_profiles.get(pid, {}))
                beats = tuple(ScriptedBeat(
                    beat_id=str(value["beat_id"]), trigger_kind=str(value["trigger_kind"]),
                    trigger_value=str(value.get("trigger_value", "")), move_kind=str(value.get("move_kind", "speak")),
                    text_template=str(value.get("text_template", "")), visible_context=dict(value.get("visible_context") or {}),
                    host_event=value.get("host_event"), priority=int(value.get("priority", 0)), once=bool(value.get("once", True)),
                ) for value in actor_profile.get("beats", ()))
                scripted = ScriptedHumanActor(actor_id=pid, policy=HUMAN_POLICIES[profile], beats=beats)
                result[pid] = (
                    OllamaHumanActor(actor_id=pid, config=self.ollama_config, fallback=scripted)
                    if self.actor_mode == "ollama" else scripted
                )
        return result

    def _pair_for_turn(self, turn: int) -> tuple[str, str]:
        actors = [str(item["id"]) for item in self.scenario.participants if item.get("kind") != "character" or item.get("acts_as_actor")]
        targets = [str(item["id"]) for item in self.scenario.participants if item.get("kind") == "character"]
        actor = actors[(turn - 1) % len(actors)]
        candidates = [item for item in targets if item != actor]
        return actor, candidates[(turn - 1) % len(candidates)]

    def _deliver(self, target_id: str, move: ActorMove, event_time: float):
        if target_id not in self.agents or move.move_kind in {"wait", "leave", "remain_silent"}:
            return None
        return self.agents[target_id].say(move.text or "The other person acts without speaking.",
                                          visible_context=dict(move.visible_context), event_time=event_time)

    @staticmethod
    def _observable_from_result(turn, day, actor_id, target_id, move, result):
        return ObservableTurn(turn, day, actor_id, target_id, move.text, "actor", move.move_kind,
                              None, (), dict(result.get("public_status") or {}) if result else {})

    @staticmethod
    def _performance_summary(result):
        return ";".join(f"{item.get('channel')}:{item.get('function')}" for item in result.get("observable_action", {}).get("acts", ()))

    @staticmethod
    def _diagnostic(day, participant_id, result, renderer):
        action = result.get("action_decision") or {}
        development = result.get("development") or {}
        conversation = result.get("conversation_candidate") or {}
        performance = result.get("performance_plan") or {}
        return {
            "day": day, "participant_id": participant_id, "action_kind": action.get("action_kind"),
            "communicative_function": action.get("communicative_function"),
            "selected_regulation": action.get("selected_regulation_id"),
            "selected_skill": action.get("selected_skill_id"),
            "conversation_move": conversation.get("move"),
            "behavioral_tendency_id": conversation.get("tendency_id"),
            "activity_transition": performance.get("activity_transition"),
            "activity_label": performance.get("activity_label"),
            "performance_channels": tuple(
                item.get("channel") for item in performance.get("acts", ())
            ),
            "self_monitor": dict(result.get("self_monitor") or {}),
            "model_calls": dict(result.get("model_calls") or {}),
            "external_model_calls": (
                int((result.get("model_calls") or {}).get("total_model_calls", 0))
                if str(getattr(renderer, "provider", "offline")) != "offline" else 0
            ),
            "reinterpretation_count": int(development.get("reinterpretation_count", 0)),
            "deferred_reinterpretation_count": int(development.get("deferred_reinterpretation_count", 0)),
            "memory_connection_count": int(development.get("memory_connection_count", 0)),
            "skills": list(development.get("skills", ())),
            "relationship_expectations": list(development.get("relationship_expectations", ())),
            "dyadic_rituals": list(development.get("dyadic_rituals", ())),
            "development_signal_count": int(development.get("development_signal_count", 0)),
            "earned_traits": list(development.get("earned_traits", ())),
        }

    def _phase_for_day(self, day):
        for phase in self.scenario.phases:
            if int(phase.get("start_day", 1)) <= day <= int(phase.get("end_day", self.scenario.total_days)):
                return str(phase.get("id", "ongoing"))
        return "ongoing"

    def _goal_for_day(self, day):
        for phase in self.scenario.phases:
            if int(phase.get("start_day", 1)) <= day <= int(phase.get("end_day", self.scenario.total_days)):
                return str(phase.get("goal", "continue interaction"))
        return "continue interaction"
