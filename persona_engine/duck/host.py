"""Production-facing local host for one persistent DUCK individual.

The host is deliberately boring. It composes the existing Wayfarer subject,
DUCK cognitive organism, text embodiment, renderer control, persistence, and
backup boundaries without becoming another cognitive authority.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
from typing import Any

from persona_engine.agent import CharacterAgent
from persona_engine.core.renderer_control import RendererConfig, RendererControlService

from .future_runtime import FutureDuckRuntime
from .persistence import DuckPersistence
from .subject_adapter import WayfarerSubjectAdapter
from .text_body import TextChannelEmbodimentPort


HOST_SCHEMA_VERSION = 1


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    with temporary.open("w", encoding="utf-8") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


@dataclass(frozen=True)
class FutureHostConfig:
    root: str
    cartridge_path: str
    user_id: str = "default_user"
    host_id: str = "local"
    body_id: str = "text-channel"
    ollama_host: str = "http://127.0.0.1:11434"
    debug: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class FutureDuckHost:
    """Own process-level composition for one DUCK subject.

    All character-changing cognition still flows through Wayfarer/DUCK public
    authorities. This class owns process paths, adapter construction, renderer
    selection, and request/response convenience only.
    """

    def __init__(self, config: FutureHostConfig):
        self.config = config
        self.root = Path(config.root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.host_metadata_path = self.root / "host.json"
        self.wayfarer_db_path = self.root / "wayfarer.sqlite3"
        self.duck_root = self.root / "duck"
        self.config_root = self.root / "config"
        self.pinned_cartridge_path = self.config_root / "cartridge.snp"
        self.renderer_control = RendererControlService(ollama_host=config.ollama_host)

        self._prepare_pinned_cartridge(Path(config.cartridge_path).expanduser().resolve())
        self._validate_existing_host_metadata()

        self.agent = CharacterAgent(
            user_id=config.user_id,
            db_path=str(self.wayfarer_db_path),
            cartridge_path=str(self.pinned_cartridge_path),
            host_id=config.host_id,
        )
        self.subject = WayfarerSubjectAdapter(self.agent)
        self.body = TextChannelEmbodimentPort(body_id=config.body_id, channel="text", host_ref=config.host_id)
        self.duck_persistence = DuckPersistence(self.duck_root)
        state = self.duck_persistence.load() if self.duck_persistence.checkpoint_path.exists() else None
        self.runtime = FutureDuckRuntime(
            self.subject,
            embodiment=self.body,
            persistence=self.duck_persistence,
            state=state,
        )
        # Replace the historical missing-model offline bootstrap with the explicit
        # supported offline renderer. This is renderer policy, not identity state.
        self.set_renderer(RendererConfig())
        self._write_host_metadata()

    @classmethod
    def open(
        cls,
        root: str | Path,
        *,
        cartridge_path: str | Path | None = None,
        user_id: str | None = None,
        host_id: str = "local",
        body_id: str = "text-channel",
        ollama_host: str = "http://127.0.0.1:11434",
        debug: bool = False,
    ) -> "FutureDuckHost":
        root_path = Path(root).expanduser().resolve()
        metadata_path = root_path / "host.json"
        saved: dict[str, Any] = {}
        if metadata_path.exists():
            saved = json.loads(metadata_path.read_text(encoding="utf-8"))
            version = int(saved.get("schema_version", 0))
            if version > HOST_SCHEMA_VERSION:
                raise ValueError(f"host schema {version} is newer than this runtime supports")
        pinned = root_path / "config" / "cartridge.snp"
        if pinned.exists():
            chosen_cartridge = pinned
        elif cartridge_path is not None:
            chosen_cartridge = Path(cartridge_path)
        else:
            chosen_cartridge = Path(__file__).resolve().parents[1] / "cartridges" / "neutral.snp"
        chosen_user = str(user_id or saved.get("user_id") or "default_user")
        if saved.get("user_id") and user_id and str(saved["user_id"]) != str(user_id):
            raise ValueError("existing DUCK host cannot be reopened under a different user_id")
        chosen_body = str(saved.get("body_id") or body_id)
        return cls(FutureHostConfig(
            root=str(root_path),
            cartridge_path=str(chosen_cartridge),
            user_id=chosen_user,
            host_id=str(host_id),
            body_id=chosen_body,
            ollama_host=str(ollama_host),
            debug=bool(debug),
        ))

    def _prepare_pinned_cartridge(self, source: Path) -> None:
        if not source.exists() or not source.is_file():
            raise FileNotFoundError(f"DUCK cartridge not found: {source}")
        self.config_root.mkdir(parents=True, exist_ok=True)
        if self.pinned_cartridge_path.exists():
            if source != self.pinned_cartridge_path and _sha256(source) != _sha256(self.pinned_cartridge_path):
                raise ValueError("existing DUCK host cartridge differs from requested cartridge")
            return
        temporary = self.pinned_cartridge_path.with_suffix(".snp.tmp")
        shutil.copy2(source, temporary)
        os.replace(temporary, self.pinned_cartridge_path)

    def _validate_existing_host_metadata(self) -> None:
        if not self.host_metadata_path.exists():
            return
        raw = json.loads(self.host_metadata_path.read_text(encoding="utf-8"))
        version = int(raw.get("schema_version", 0))
        if version > HOST_SCHEMA_VERSION:
            raise ValueError(f"host schema {version} is newer than this runtime supports")
        expected_hash = str(raw.get("cartridge_sha256", ""))
        actual_hash = _sha256(self.pinned_cartridge_path)
        if expected_hash and expected_hash != actual_hash:
            raise ValueError("pinned cartridge checksum does not match host metadata")
        saved_user = str(raw.get("user_id", self.config.user_id))
        if saved_user != self.config.user_id:
            raise ValueError("host metadata user_id does not match requested subject scope")

    def _write_host_metadata(self) -> None:
        payload = {
            "schema_version": HOST_SCHEMA_VERSION,
            "subject_id": self.subject.subject_id,
            "user_id": self.config.user_id,
            "body_id": self.config.body_id,
            "cartridge_path": "config/cartridge.snp",
            "cartridge_sha256": _sha256(self.pinned_cartridge_path),
            "wayfarer_db": "wayfarer.sqlite3",
            "duck_root": "duck",
        }
        if self.host_metadata_path.exists():
            previous = json.loads(self.host_metadata_path.read_text(encoding="utf-8"))
            previous_subject = str(previous.get("subject_id", ""))
            if previous_subject and previous_subject != self.subject.subject_id:
                raise ValueError("persistent subject_id changed while reopening DUCK host")
        _atomic_json(self.host_metadata_path, payload)

    def set_renderer(self, config: RendererConfig | dict[str, Any]) -> dict[str, Any]:
        if isinstance(config, dict):
            config = self.renderer_control.config_from_mapping(config)
        if not isinstance(config, RendererConfig):
            raise TypeError("renderer config must be RendererConfig or mapping")
        renderer = self.renderer_control.build_renderer(config)
        self.agent.set_renderer(renderer)
        return self.agent.engine.renderer_status()

    def renderer_status(self) -> dict[str, Any]:
        return self.agent.engine.renderer_status()

    def discover_renderers(self) -> dict[str, Any]:
        return self.renderer_control.discover()

    def send(self, text: str, *, utc_epoch: float | None = None) -> dict[str, Any]:
        before = len(self.body.outbox)
        event = self.runtime.ingest_user_message(str(text), utc_epoch=utc_epoch)
        trace = self.runtime.step()
        outputs = [dict(item) for item in self.body.outbox[before:]]
        self._write_host_metadata()
        return {
            "subject_id": self.subject.subject_id,
            "event_id": event.event_id,
            "tick": self.runtime.tick,
            "selected_action": (
                trace.selected_intention.get("action", {}).get("action_type")
                if trace is not None else None
            ),
            "outputs": outputs,
            "response": outputs[-1]["text"] if outputs else None,
            "expression": self.runtime.latest_expression(),
        }

    def observe(
        self,
        payload: dict[str, Any],
        *,
        kind: str = "observation",
        source: str = "host",
        utc_epoch: float | None = None,
        process: bool = True,
    ) -> dict[str, Any]:
        event = self.runtime.ingest_observation(
            dict(payload), kind=kind, source=source, utc_epoch=utc_epoch
        )
        trace = self.runtime.step() if process else None
        return {
            "event_id": event.event_id,
            "processed": trace is not None,
            "tick": self.runtime.tick,
        }

    def step(self) -> dict[str, Any] | None:
        trace = self.runtime.step()
        return trace.to_dict() if trace is not None else None

    def save(self) -> dict[str, Any]:
        digest = self.runtime.save()
        self._write_host_metadata()
        return {"subject_id": self.subject.subject_id, "duck_state_sha256": digest}

    def public_status(self) -> dict[str, Any]:
        runtime_status = self.runtime.status()
        return {
            "subject_id": self.subject.subject_id,
            "tick": runtime_status["tick"],
            "temporal_stamp": runtime_status["temporal_stamp"],
            "body": runtime_status["body"],
            "renderer": self.renderer_status(),
            "subject": self.agent.public_status(),
        }

    def debug_status(self) -> dict[str, Any]:
        return {
            "public": self.public_status(),
            "duck": self.runtime.status(),
            "wayfarer": self.agent.debug_snapshot(),
        }
