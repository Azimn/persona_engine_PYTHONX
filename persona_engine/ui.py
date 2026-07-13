"""Optional FastAPI/SSE human-testing interface.

The UI layer is a pure consumer of organism state. It may submit user text
through the normal engine input channel, and it may submit bounded sensory
observations through standard sensor endpoints. It never directly mutates body,
world, relationship, memory, pressure, symbol, belief, or identity state.
"""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any

from .agent import CharacterAgent
from .core.public_state import debug_snapshot_from_engine
from .core.renderer_control import RendererConfig, RendererControlService


class InterfaceDependencyError(RuntimeError):
    """Raised when optional UI dependencies are unavailable."""


def _package_root() -> Path:
    return Path(__file__).resolve().parent


def _default_cartridges_dir() -> Path:
    return _package_root() / "cartridges"


def _safe_cartridge_path(cartridges_dir: Path, cartridge_name: str) -> Path:
    """Resolve a cartridge name without allowing path traversal."""

    cartridges_dir = cartridges_dir.resolve()
    name = Path(cartridge_name).name
    if not name.endswith(".snp"):
        name = f"{name}.snp"
    candidate = (cartridges_dir / name).resolve()
    if cartridges_dir not in candidate.parents and candidate != cartridges_dir:
        raise ValueError("cartridge must live inside the configured cartridges directory")
    if not candidate.exists():
        raise FileNotFoundError(f"cartridge not found: {name}")
    return candidate


def stream_payload_chunks(text: str, delay_seconds: float = 0.015):
    """Yield SSE-ready text chunks without authoring any state."""

    for index, word in enumerate(text.split(" ")):
        piece = word if index == 0 else " " + word
        yield f"data: {json.dumps({'type': 'token', 'token': piece})}\n\n"
        time.sleep(delay_seconds)


def _public_status_payload(session: "HumanTestingSession") -> dict[str, Any]:
    """Return only categorical public/session status for normal UI consumers."""

    return {
        "session": {
            "cartridge": session.cartridge_path.name,
            "user_id": session.user_id,
        },
        "status": session.agent.public_status(),
        "avatar_state": session.agent.avatar_projection(),
    }


def _debug_payload(session: "HumanTestingSession", enabled: bool) -> dict[str, Any]:
    """Return an opt-in read-only debug summary.

    Normal UI status never includes private values. This debug view can expose
    developer inspection details, but it still does not provide mutation hooks.
    """

    if not enabled:
        return {"enabled": False, "message": "debug mode is disabled"}

    engine = session.agent.engine
    rows = engine.persistence.load_events_since(engine.identity.name, engine.user_id, since=0)[-12:]
    validator_actions = [
        {
            "event_id": row["id"],
            "timestep": row["timestep"],
            "violations": row["payload"].get("violations", []),
        }
        for row in rows
        if row["event_type"] == "validation"
    ]
    workspace_rows = [row for row in rows if row["event_type"] in {"turn", "input", "sensorium"}]
    latest_workspace = workspace_rows[-1] if workspace_rows else None
    debug_refs = [
        {
            "event_id": row["id"],
            "timestep": row["timestep"],
            "event_type": row["event_type"],
        }
        for row in rows
    ]
    return {
        "enabled": True,
        "event_ids": [row["id"] for row in rows],
        "workspace_summary": {
            "latest_event_type": latest_workspace["event_type"] if latest_workspace else None,
            "latest_timestep": latest_workspace["timestep"] if latest_workspace else None,
            "visible_context_keys": sorted((latest_workspace or {}).get("payload", {}).get("visible_context", {}).keys()),
            "memory_types": (latest_workspace or {}).get("payload", {}).get("memory_types", []),
        },
        "validator_actions": validator_actions,
        "replay_debug_refs": debug_refs,
        "private_snapshot": debug_snapshot_from_engine(engine),
    }


class HumanTestingSession:
    """Small holder for a selected cartridge and its current agent instance."""

    def __init__(
        self,
        cartridges_dir: Path,
        db_dir: Path,
        default_cartridge: str,
        user_id: str,
        renderer_control: RendererControlService,
    ):
        self.cartridges_dir = cartridges_dir
        self.db_dir = db_dir
        self.user_id = user_id
        self.renderer_control = renderer_control
        self._renderer_configs: dict[str, RendererConfig] = {}
        self.cartridge_path = _safe_cartridge_path(cartridges_dir, default_cartridge)
        self.agent = self._make_agent(reset=False)

    def _renderer_config(self) -> RendererConfig:
        return self._renderer_configs.setdefault(self.cartridge_path.name, RendererConfig())

    def _db_path_for(self, cartridge_path: Path) -> Path:
        stem = cartridge_path.stem.replace(" ", "_")
        safe_user = self.user_id.replace("/", "_").replace("\\", "_")
        return self.db_dir / f"ui_{safe_user}_{stem}.db"

    def _make_agent(self, reset: bool = False) -> CharacterAgent:
        self.db_dir.mkdir(parents=True, exist_ok=True)
        db_path = self._db_path_for(self.cartridge_path)
        if reset and db_path.exists():
            db_path.unlink()
        agent = CharacterAgent(cartridge_path=str(self.cartridge_path), user_id=self.user_id, db_path=str(db_path))
        agent.engine.set_renderer(self.renderer_control.build_renderer(self._renderer_config()))
        return agent

    def select(self, cartridge_name: str, reset: bool = False) -> dict:
        self.cartridge_path = _safe_cartridge_path(self.cartridges_dir, cartridge_name)
        self.agent = self._make_agent(reset=reset)
        return self.info()

    def reset(self) -> dict:
        self.agent = self._make_agent(reset=True)
        return self.info()

    def configure_renderer(self, raw: dict[str, Any]) -> dict[str, Any]:
        config = self.renderer_control.config_from_mapping(raw)
        renderer = self.renderer_control.build_renderer(config)
        self._renderer_configs[self.cartridge_path.name] = config
        self.agent.engine.set_renderer(renderer)
        return self.renderer_status()

    def renderer_status(self) -> dict[str, Any]:
        return {
            "config": self._renderer_config().to_dict(),
            "runtime": self.agent.engine.renderer_status(),
        }

    def info(self) -> dict:
        return {
            "cartridge": self.cartridge_path.name,
            "user_id": self.user_id,
            "db_path": str(self._db_path_for(self.cartridge_path)),
            "renderer": self.renderer_status(),
        }


def create_app(
    cartridge_path: str | None = None,
    db_path: str = "persona_ui_state.db",
    user_id: str = "ui_user",
    debug: bool = False,
    cartridges_dir: str | None = None,
    renderer_control: RendererControlService | None = None,
):
    """Create a FastAPI app if FastAPI is installed.

    The resulting app serves a local human-testing UI plus JSON/SSE endpoints.
    The interface can only act through the same input and sensor channels used
    by the deterministic engine.
    """

    try:
        from fastapi import FastAPI, HTTPException, Body
        from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
        from fastapi.staticfiles import StaticFiles
    except Exception as exc:
        raise InterfaceDependencyError("Install fastapi and uvicorn to run the UI server") from exc

    package_root = _package_root()
    static_dir = package_root / "ui_static"
    selected_cartridges_dir = Path(cartridges_dir).resolve() if cartridges_dir else _default_cartridges_dir().resolve()
    db_target = Path(db_path)
    db_dir = db_target if db_target.suffix == "" else db_target.parent
    default_cartridge = Path(cartridge_path).name if cartridge_path else "pretorius.snp"
    control = renderer_control or RendererControlService()
    session = HumanTestingSession(selected_cartridges_dir, db_dir, default_cartridge, user_id, control)

    app = FastAPI(title="Persona Engine Human Testing UI", version="12.0")
    app.mount("/assets", StaticFiles(directory=str(static_dir)), name="assets")

    @app.get("/", response_class=HTMLResponse)
    def index():
        html = static_dir.joinpath("index.html").read_text(encoding="utf-8")
        return HTMLResponse(html)

    @app.get("/start", response_class=HTMLResponse)
    def start():
        html = static_dir.joinpath("start.html").read_text(encoding="utf-8")
        return HTMLResponse(html)

    @app.get("/launcher")
    def launcher():
        launcher_path = package_root.parent / "Start_PersonaConsole_Python.cmd"
        if not launcher_path.exists():
            raise HTTPException(status_code=404, detail="launcher file is not available in this install")
        return FileResponse(str(launcher_path), filename="Start_PersonaConsole_Python.cmd")

    @app.get("/health")
    def health():
        return {"ok": True, "session": session.info(), "renderer": session.renderer_status()}

    @app.get("/api/renderers")
    @app.get("/renderers")
    def renderers():
        return {**control.discover(), "current": session.renderer_status()}

    @app.post("/api/renderer/config")
    @app.post("/renderer/config")
    def configure_renderer(req: dict = Body(...)):
        try:
            return session.configure_renderer(req)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/cartridges")
    @app.get("/cartridges")
    def cartridges():
        items = []
        for path in sorted(selected_cartridges_dir.glob("*.snp")):
            items.append({"name": path.name, "stem": path.stem})
        return {"cartridges": items, "current": session.cartridge_path.name}

    @app.post("/api/session/select")
    @app.post("/session/select")
    def select_cartridge(req: dict = Body(...)):
        try:
            info = session.select(str(req.get("cartridge", "")), reset=bool(req.get("reset", False)))
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"session": {"cartridge": info["cartridge"], "user_id": info["user_id"]}, "status": session.agent.public_status(), "renderer": session.renderer_status()}

    @app.post("/api/session/reset")
    @app.post("/session/reset")
    def reset_session():
        info = session.reset()
        return {"session": {"cartridge": info["cartridge"], "user_id": info["user_id"]}, "status": session.agent.public_status(), "renderer": session.renderer_status()}

    @app.get("/api/status")
    @app.get("/status")
    def status():
        return _public_status_payload(session)

    @app.get("/api/proactive")
    @app.get("/proactive")
    def proactive():
        return {"events": session.agent.poll_proactive_events()}

    @app.get("/api/avatar")
    @app.get("/avatar")
    def avatar():
        return session.agent.avatar_projection()

    @app.post("/api/sensor/audio")
    @app.post("/sense/audio")
    def sense_audio(req: dict = Body(...)):
        return session.agent.observe_audio(req)

    @app.post("/api/sensor/vision")
    @app.post("/sense/vision")
    def sense_vision(req: dict = Body(...)):
        return session.agent.observe_vision(req)

    @app.get("/api/voice/plan")
    @app.get("/voice/plan")
    def voice_plan(text: str):
        return session.agent.plan_voice(text)

    @app.get("/api/debug")
    @app.get("/debug")
    def debug_view():
        return _debug_payload(session, debug)

    @app.post("/api/chat")
    @app.post("/chat")
    def chat(req: dict = Body(...)):
        result = session.agent.say(str(req.get("text", "")), server_truth=req.get("server_truth"), visible_context=req.get("visible_context"))
        return {
            "response": result["response"],
            "status": result["public_status"],
            "avatar_state": result["avatar_state"],
            "avatar_projection": result.get("avatar_projection"),
            "voice_plan": result.get("voice_plan"),
            "second_thoughts": result["second_thoughts"],
            "proactive_events": result["proactive_events"],
            "interpretive_beliefs": result.get("interpretive_beliefs", []),
            "bucket": result.get("bucket"),
            "renderer": session.renderer_status(),
        }

    @app.post("/api/chat/stream")
    @app.post("/chat/stream")
    def chat_stream(req: dict = Body(...)):
        result = session.agent.say(str(req.get("text", "")), server_truth=req.get("server_truth"), visible_context=req.get("visible_context"))

        def events():
            yield f"data: {json.dumps({'type': 'status', 'status': result['public_status']})}\n\n"
            yield f"data: {json.dumps({'type': 'avatar', 'avatar': result.get('avatar_projection')})}\n\n"
            for chunk in stream_payload_chunks(result["response"]):
                yield chunk
            for thought in result.get("second_thoughts", []):
                yield f"data: {json.dumps({'type': 'second_thought', 'text': thought})}\n\n"
            yield f"data: {json.dumps({'type': 'complete', 'response': result['response'], 'voice_plan': result.get('voice_plan'), 'beliefs': result.get('interpretive_beliefs', []), 'renderer': session.renderer_status()})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(events(), media_type="text/event-stream")

    return app
