"""Blind behavioral evaluation with a separate structured causal replay.

This is a diagnostic host, not a cognitive subsystem. It passes only observable
events between isolated character engines and never mutates their private state.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import tempfile
from typing import Any, Callable

import yaml

from .agent import CharacterAgent


@dataclass(frozen=True)
class BlindTranscriptItem:
    turn: int
    speaker_id: str
    listener_id: str
    text: str
    source: str = "observed_speech"


@dataclass(frozen=True)
class CausalTurnRecord:
    turn: int
    speaker_id: str
    listener_id: str
    intrinsic_action: dict[str, Any] | None
    synthesis: dict[str, Any]
    interpretive_beliefs: tuple[dict[str, Any], ...]
    decision_payload: dict[str, Any]
    retrieved_memories: tuple[dict[str, Any], ...]
    life_context: dict[str, Any]
    model_calls: dict[str, Any]
    self_monitor: dict[str, Any]
    selected_regulation_id: str | None
    conversation_candidate: dict[str, Any]
    conversation_choreography: dict[str, Any]
    action_decision: dict[str, Any]
    performance_plan: dict[str, Any]
    speech_world_event_ids: tuple[str, ...]


@dataclass(frozen=True)
class BehavioralEvaluationResult:
    scenario_id: str
    participants: tuple[str, ...]
    blind_transcript: tuple[BlindTranscriptItem, ...]
    causal_prelude: tuple[dict[str, Any], ...]
    causal_turns: tuple[CausalTurnRecord, ...]
    metrics: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BehavioralEvaluationHarness:
    """Run a paired scene while preserving per-character private boundaries."""

    def __init__(
        self,
        *,
        cartridges_dir: str | Path,
        db_dir: str | Path | None = None,
        renderer_factory: Callable[[str], Any] | None = None,
    ):
        self.cartridges_dir = Path(cartridges_dir)
        self.db_dir = Path(db_dir) if db_dir else Path(tempfile.mkdtemp(prefix="persona_behavior_"))
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.renderer_factory = renderer_factory
        self.agents: dict[str, CharacterAgent] = {}
        self.db_paths: dict[str, Path] = {}

    def _create_agents(self, participants: list[dict[str, Any]]) -> tuple[str, ...]:
        if len(participants) != 2:
            raise ValueError("paired evaluation requires exactly two participants")
        ids = tuple(str(item["id"]) for item in participants)
        if len(set(ids)) != 2:
            raise ValueError("paired participant IDs must be unique")
        for index, item in enumerate(participants):
            participant_id = ids[index]
            other_id = ids[1 - index]
            cartridge = self.cartridges_dir / Path(str(item["cartridge"])).name
            if not cartridge.is_file():
                raise ValueError(f"missing cartridge: {cartridge.name}")
            db_path = self.db_dir / f"{participant_id}.db"
            agent = CharacterAgent(
                cartridge_path=str(cartridge),
                user_id=f"participant:{other_id}",
                db_path=str(db_path),
            )
            if self.renderer_factory:
                agent.engine.set_renderer(self.renderer_factory(participant_id))
            self.agents[participant_id] = agent
            self.db_paths[participant_id] = db_path
        return ids

    def _record_shared_event(
        self,
        *,
        event_type: str,
        actors: tuple[str, ...],
        targets: tuple[str, ...],
        action: str,
        outcome: str,
        payload: dict[str, Any] | None = None,
    ) -> tuple[str, ...]:
        event_ids = []
        for participant_id in sorted(self.agents):
            event = self.agents[participant_id].record_world_event(
                event_type=event_type,
                actors=actors,
                location="shared_interaction",
                action=action,
                targets=targets,
                outcome=outcome,
                source="behavioral_evaluation_host",
                payload=payload or {},
            )
            event_ids.append(event["event_id"])
        return tuple(event_ids)

    def run_paired(self, scenario: dict[str, Any]) -> BehavioralEvaluationResult:
        participant_ids = self._create_agents(list(scenario.get("participants", [])))
        first_responder = str(scenario.get("first_responder", participant_ids[0]))
        if first_responder not in self.agents:
            raise ValueError("first_responder is not a participant")
        turns = max(1, min(100, int(scenario.get("turns", 8))))
        current_input = str(scenario.get("starter", "Another participant is present."))

        prelude: list[dict[str, Any]] = []
        for participant_id in participant_ids:
            other_id = next(item for item in participant_ids if item != participant_id)
            decision = self.agents[participant_id].select_intrinsic_action()
            prelude.append({
                "participant_id": participant_id,
                "other_id": other_id,
                "intrinsic_action": decision,
            })
        self._record_shared_event(
            event_type="participant_arrival",
            actors=tuple(participant_ids),
            targets=tuple(participant_ids),
            action="became mutually present",
            outcome="both participants were present in the shared interaction",
            payload={"visibility": "mutual", "canonicality": "objective"},
        )

        blind: list[BlindTranscriptItem] = []
        causal: list[CausalTurnRecord] = []
        speaker_id = first_responder
        prior_observable_performance: dict[str, Any] | None = None
        for turn in range(1, turns + 1):
            listener_id = next(item for item in participant_ids if item != speaker_id)
            agent = self.agents[speaker_id]
            visible_context = {
                "speaker_id": listener_id,
                "speaker_name": listener_id,
                "observed_utterance": "" if prior_observable_performance else current_input,
                "interaction_type": "character_to_character",
            }
            if prior_observable_performance is not None:
                visible_context.update({
                    "source_modality": "nonverbal_performance",
                    "observable_performance": prior_observable_performance,
                })
            result = agent.say(
                "..." if prior_observable_performance else current_input,
                visible_context=visible_context,
            )
            reply = str(result["response"])
            performance = dict(result.get("performance_plan") or {})
            source = "observed_speech"
            next_input = reply
            next_performance = None
            if not reply:
                reply = f"*{_observable_performance_text(performance)}*"
                source = "observed_performance"
                next_input = "..."
                next_performance = performance
            blind.append(BlindTranscriptItem(turn, speaker_id, listener_id, reply, source=source))
            speech_ids = self._record_shared_event(
                event_type=source,
                actors=(speaker_id,),
                targets=(listener_id,),
                action="spoke" if source == "observed_speech" else "performed nonverbally",
                outcome=reply,
                payload={
                    "canonicality": "speech_evidence" if source == "observed_speech" else "performance_evidence",
                    "turn": turn,
                },
            )
            causal.append(CausalTurnRecord(
                turn=turn,
                speaker_id=speaker_id,
                listener_id=listener_id,
                intrinsic_action=(
                    agent.engine._last_action_decision.to_dict()
                    if agent.engine._last_action_decision else None
                ),
                synthesis=dict(result.get("synthesis") or {}),
                interpretive_beliefs=tuple(result.get("interpretive_belief_trace") or ()),
                decision_payload=dict(result.get("decision_payload") or {}),
                retrieved_memories=tuple(result.get("retrieved_memory_trace") or ()),
                life_context=dict(result.get("life_context") or {}),
                model_calls=dict(result.get("model_calls") or {}),
                self_monitor=dict(result.get("self_monitor") or {}),
                selected_regulation_id=(result.get("action_decision") or {}).get("selected_regulation_id"),
                conversation_candidate=dict(result.get("conversation_candidate") or {}),
                conversation_choreography=dict(result.get("conversation_choreography") or {}),
                action_decision=dict(result.get("action_decision") or {}),
                performance_plan=dict(result.get("performance_plan") or {}),
                speech_world_event_ids=speech_ids,
            ))
            current_input = next_input
            prior_observable_performance = next_performance
            speaker_id = listener_id

        return BehavioralEvaluationResult(
            scenario_id=str(scenario.get("scenario_id", "paired_evaluation")),
            participants=participant_ids,
            blind_transcript=tuple(blind),
            causal_prelude=tuple(prelude),
            causal_turns=tuple(causal),
            metrics={
                **_score_transcript(blind, participant_ids),
                "private_cognition_renderer_calls": sum(
                    int(item.model_calls.get("private_cognition_renderer_called", False)) for item in causal
                ),
                "expression_renderer_calls": sum(
                    int(item.model_calls.get("expression_renderer_called", False)) for item in causal
                ),
                "total_model_calls": sum(int(item.model_calls.get("total_model_calls", 0)) for item in causal),
                "self_monitor_detected_conflict_count": sum(
                    len(item.self_monitor.get("noticed_conflict_ids", ())) for item in causal
                ),
                "self_monitor_missed_conflict_count": sum(
                    len(item.self_monitor.get("missed_conflict_ids", ())) for item in causal
                ),
                "clarification_count": sum(
                    item.selected_regulation_id is not None
                    and any(candidate.get("candidate_id") == item.selected_regulation_id and candidate.get("kind") == "ask_clarification"
                            for candidate in item.self_monitor.get("regulation_candidates", ()))
                    for item in causal
                ),
                "self_correction_count": _regulation_count(causal, "self_correct"),
                "delay_count": _regulation_count(causal, "delay") + _regulation_count(causal, "pause"),
                "double_down_count": _regulation_count(causal, "double_down"),
                "concealed_uncertainty_count": _regulation_count(causal, "conceal_uncertainty"),
                "externalized_cause_count": sum(
                    item.self_monitor.get("attributed_cause") in {"interlocutor", "circumstances"}
                    for item in causal
                ),
                "conversation_move_diversity": len({
                    item.conversation_candidate.get("move") for item in causal
                    if item.conversation_candidate.get("move") not in {None, "basic_reply"}
                }),
                "conversation_extension_diversity": len({
                    item.conversation_candidate.get("extension_move") for item in causal
                    if item.conversation_candidate.get("extension_move")
                }),
                "obligation_honored_count": sum(
                    (
                        item.action_decision.get("communicative_function")
                        in {
                            "answer": {"answer", "respond", "reminisce"},
                            "clarify": {"ask_clarification"},
                            "acknowledge": {"acknowledge", "respond"},
                            "repair": {"repair", "acknowledge"},
                            "follow_up": {"return_to_topic", "defer_and_note", "reminisce_and_note"},
                        }.get(item.conversation_candidate.get("obligation"), set())
                    )
                    for item in causal if item.conversation_candidate.get("obligation")
                ),
                "behavioral_tendency_use_count": sum(
                    bool(item.conversation_candidate.get("tendency_id")) for item in causal
                ),
                "activity_callback_count": sum(
                    item.performance_plan.get("activity_transition") in {
                        "continued", "paused", "resumed", "completed", "failed", "abandoned", "changed",
                    }
                    for item in causal
                ),
                "activity_update_count": sum(
                    item.conversation_candidate.get("move") == "activity_update" for item in causal
                ),
                "optional_extension_count": sum(
                    bool(item.conversation_candidate.get("extension_move")) for item in causal
                ),
                "no_extension_count": sum(
                    bool(item.conversation_candidate.get("obligation"))
                    and not item.conversation_candidate.get("extension_move")
                    for item in causal
                ),
                "semantic_move_repeat_count": sum(
                    (
                        prior.conversation_candidate.get("obligation"),
                        prior.conversation_candidate.get("extension_move"),
                        prior.action_decision.get("action_kind"),
                    ) == (
                        current.conversation_candidate.get("obligation"),
                        current.conversation_candidate.get("extension_move"),
                        current.action_decision.get("action_kind"),
                    )
                    for participant in {item.speaker_id for item in causal}
                    for prior, current in zip(
                        [item for item in causal if item.speaker_id == participant],
                        [item for item in causal if item.speaker_id == participant][1:],
                    )
                ),
                "trajectory_repeat_count": sum(
                    prior.conversation_choreography.get("trajectory_signature")
                    == current.conversation_choreography.get("trajectory_signature")
                    for participant in {item.speaker_id for item in causal}
                    for prior, current in zip(
                        [item for item in causal if item.speaker_id == participant],
                        [item for item in causal if item.speaker_id == participant][1:],
                    )
                    if prior.conversation_choreography.get("trajectory_signature")
                ),
                "rhetorical_strategy_diversity": len({
                    item.conversation_choreography.get("rhetorical_strategy")
                    for item in causal
                    if item.conversation_choreography.get("rhetorical_strategy")
                }),
            },
        )


def _observable_performance_text(performance: dict[str, Any]) -> str:
    """Render bounded public acts for a human transcript, never as dialogue."""

    acts = list(performance.get("acts") or ())
    phrases: list[str] = []
    for channel in ("gesture", "activity", "gaze", "posture", "face"):
        act = next((item for item in acts if item.get("channel") == channel), None)
        if not act:
            continue
        function = str(act.get("function", "")).replace("_", " ").strip()
        target = str(act.get("target", "")).replace("_", " ").strip()
        if channel == "gesture" and function not in {"", "none"}:
            article = "an" if function[:1].lower() in "aeiou" else "a"
            phrases.append(f"offers {article} {function} acknowledgement")
        elif channel == "activity" and function not in {"", "none"}:
            if target == "responding to interruption":
                phrases.append(f"{function} while responding to the interruption")
            else:
                activity = target if target and target != "current interlocutor" else "the current activity"
                phrases.append(f"{function} {activity}")
        elif channel == "gaze" and function not in {"", "none", "target"}:
            phrases.append(f"holds an {function} gaze")
        elif channel == "posture" and function not in {"", "none"}:
            phrases.append(f"remains {function}")
        elif channel == "face" and function not in {"", "none", "neutral"}:
            phrases.append(f"keeps a {function} expression")
        if len(phrases) >= 2:
            break
    return "; ".join(phrases) if phrases else "remains present without speaking"


def _regulation_count(records: list[CausalTurnRecord], kind: str) -> int:
    return sum(
        record.selected_regulation_id is not None
        and any(
            candidate.get("candidate_id") == record.selected_regulation_id
            and candidate.get("kind") == kind
            for candidate in record.self_monitor.get("regulation_candidates", ())
        )
        for record in records
    )


def _score_transcript(
    transcript: list[BlindTranscriptItem], participants: tuple[str, ...]
) -> dict[str, Any]:
    texts = [" ".join(item.text.lower().split()) for item in transcript]
    openers = [" ".join(text.split()[:5]) for text in texts]
    combined = " ".join(texts)
    assistant_patterns = re.findall(
        r"\b(?:as an ai|language model|how can i help|happy to help|let me know if)\b",
        combined,
    )
    bleed: list[dict[str, Any]] = []
    repeats_by_speaker = {}
    for participant in participants:
        participant_texts = [
            text for text, item in zip(texts, transcript) if item.speaker_id == participant
        ]
        repeats_by_speaker[participant] = len(participant_texts) - len(set(participant_texts))
    for item in transcript:
        for other in participants:
            if other == item.speaker_id:
                continue
            if re.search(rf"\b(?:i am|i'm|call me)\s+{re.escape(other)}\b", item.text, re.IGNORECASE):
                bleed.append({"turn": item.turn, "speaker_id": item.speaker_id, "suspected_identity": other})
    return {
        "turns": len(transcript),
        "exact_repeats": len(texts) - len(set(texts)),
        "exact_repeats_by_speaker": repeats_by_speaker,
        "opener_repeats": len(openers) - len(set(openers)),
        "question_rate": round(sum("?" in item.text for item in transcript) / max(1, len(transcript)), 4),
        "assistant_drift_hits": len(assistant_patterns),
        "identity_bleed_suspicions": bleed,
    }


def load_scenario(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    if not isinstance(raw, dict):
        raise ValueError("behavioral scenario must be a mapping")
    return raw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a blind paired-character behavioral evaluation.")
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--output")
    parser.add_argument("--db-dir")
    args = parser.parse_args(argv)
    scenario = load_scenario(args.scenario)
    root = Path(__file__).resolve().parent
    harness = BehavioralEvaluationHarness(cartridges_dir=root / "cartridges", db_dir=args.db_dir)
    result = harness.run_paired(scenario)
    payload = result.to_dict()
    for item in result.blind_transcript:
        print(f"{item.turn:02d} {item.speaker_id} -> {item.listener_id}: {item.text}")
    print("metrics:", json.dumps(result.metrics, ensure_ascii=False, sort_keys=True))
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
