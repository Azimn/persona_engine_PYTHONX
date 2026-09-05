"""Local FastAPI surface for the production-candidate DUCK host."""

from typing import Any

from .host import FutureDuckHost


def create_app(host: FutureDuckHost, *, debug: bool | None = None):
    try:
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel, Field
    except Exception as exc:  # pragma: no cover - dependency installation boundary
        raise RuntimeError("Install DUCK API dependencies with: pip install -e '.[ui]'") from exc

    debug_enabled = host.config.debug if debug is None else bool(debug)
    app = FastAPI(title="DUCK Runtime API", version="1.0")

    class MessageRequest(BaseModel):
        text: str = Field(min_length=1, max_length=100_000)
        utc_epoch: float | None = None

    class ObservationRequest(BaseModel):
        payload: dict[str, Any]
        kind: str = "observation"
        source: str = "api"
        utc_epoch: float | None = None
        process: bool = True

    class RendererRequest(BaseModel):
        provider: str = "offline"
        model_name: str = "offline-template"
        thinking_mode: str = "off"
        timeout_seconds: float = 60.0
        token_budget: int = 256

    @app.get("/health")
    def health():
        return {"ready": True, "subject_id": host.subject.subject_id, "tick": host.runtime.tick}

    @app.get("/v1/status")
    def status():
        return host.public_status()

    @app.post("/v1/messages")
    def message(request: MessageRequest):
        try:
            return host.send(request.text, utc_epoch=request.utc_epoch)
        except (ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/v1/observe")
    def observe(request: ObservationRequest):
        try:
            return host.observe(
                request.payload,
                kind=request.kind,
                source=request.source,
                utc_epoch=request.utc_epoch,
                process=request.process,
            )
        except (ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/v1/step")
    def step():
        return {"trace": host.step(), "tick": host.runtime.tick}

    @app.post("/v1/save")
    def save():
        return host.save()

    @app.get("/v1/renderers")
    def renderers():
        return host.discover_renderers()

    @app.put("/v1/renderer")
    def renderer(request: RendererRequest):
        try:
            return host.set_renderer(request.model_dump())
        except (ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/v1/trace/latest")
    def latest_trace():
        if not debug_enabled:
            raise HTTPException(status_code=403, detail="debug trace endpoint is disabled")
        if not host.runtime.organism.traces:
            return {"trace": None}
        return {"trace": host.runtime.organism.traces[-1].to_dict()}

    @app.get("/v1/debug/status")
    def debug_status():
        if not debug_enabled:
            raise HTTPException(status_code=403, detail="debug status endpoint is disabled")
        return host.debug_status()

    return app
