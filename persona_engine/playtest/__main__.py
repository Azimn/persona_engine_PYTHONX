"""CLI for deterministic and optional Ollama developmental playtests."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from .actors import ActorMove, OllamaActorConfig
from .host import DevelopmentalPlaytestHost
from .minimizer import ScenarioMinimizer
from .report import write_reports
from .scenario import load_scenario
from persona_engine.core.c99_fixtures import developmental_fixture_bytes


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--actor-mode", choices=("scripted", "character", "ollama"), default="scripted")
    parser.add_argument("--output-dir", default="playtest_output")
    parser.add_argument("--judge", choices=("none", "deterministic", "ollama"), default="deterministic")
    parser.add_argument("--minimize-failures", action="store_true")
    parser.add_argument("--replay-moves")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--ollama-model", default="qwen3:1.7b")
    parser.add_argument("--ollama-endpoint", default="http://127.0.0.1:11434")
    parser.add_argument("--ollama-seed", type=int, default=17)
    args = parser.parse_args(argv)
    scenario = load_scenario(args.scenario)
    if args.seed is not None:
        scenario = scenario.__class__(**{**scenario.__dict__, "stable_seed": args.seed})
    replay_moves = None
    if args.replay_moves:
        replay_moves = [ActorMove(
            actor_id=str(item["actor_id"]), move_kind=str(item["move_kind"]), text=str(item.get("text", "")),
            visible_context=dict(item.get("visible_context") or {}), host_event=item.get("host_event"),
            rationale_code=str(item.get("rationale_code", "replay")),
        ) for item in json.loads(Path(args.replay_moves).read_text(encoding="utf-8"))]
    repo = Path(__file__).resolve().parents[2]
    db_dir = Path(tempfile.mkdtemp(prefix="persona_playtest_"))
    host = DevelopmentalPlaytestHost(
        scenario=scenario, cartridges_dir=repo / "persona_engine" / "cartridges", db_dir=db_dir,
        actor_mode=args.actor_mode, replay_moves=replay_moves,
        ollama_config=OllamaActorConfig(endpoint=args.ollama_endpoint, model=args.ollama_model, seed=args.ollama_seed),
    )
    result = host.run(judge=args.judge)
    write_reports(args.output_dir, result)
    if host.agents:
        first_agent = host.agents[sorted(host.agents)[0]]
        (Path(args.output_dir) / "c99_development_fixture.json").write_bytes(
            developmental_fixture_bytes(first_agent.engine)
        )
    if args.minimize_failures and result.failures:
        minimizer = ScenarioMinimizer()
        failure = result.failures[0]
        def rerun(candidate):
            return DevelopmentalPlaytestHost(
                scenario=candidate, cartridges_dir=repo / "persona_engine" / "cartridges",
                db_dir=Path(tempfile.mkdtemp(prefix="persona_minimize_")), actor_mode="scripted",
                replay_moves=None,
            ).run(judge="none")
        minimized, runs = minimizer.minimize(scenario=scenario, failure_code=failure.code, run_callable=rerun)
        generated = minimizer.export(
            minimized, failure.code,
            repo / "persona_engine" / "simulator_scripts" / "generated_regressions",
        )
        print(f"minimized failure in {runs} runs: {generated}")
    print(f"{scenario.total_days}-day Developmental Life playtest: {scenario.scenario_id}")
    print(json.dumps(dict(result.metrics), sort_keys=True))
    print(f"failures: {len(result.failures)}")
    return 1 if any(item.severity >= 0.9 for item in result.failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
