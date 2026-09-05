"""Portable, checksum-verified backup and restore for a DUCK host directory."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
import zipfile
from typing import Any


BACKUP_SCHEMA = "duck-host-backup-v1"


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _copy_sqlite(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    source_conn = sqlite3.connect(str(source))
    destination_conn = sqlite3.connect(str(destination))
    try:
        source_conn.backup(destination_conn)
        destination_conn.commit()
    finally:
        destination_conn.close()
        source_conn.close()


class DuckBackupManager:
    @staticmethod
    def create(root: str | Path, archive_path: str | Path) -> dict[str, Any]:
        root = Path(root).expanduser().resolve()
        archive_path = Path(archive_path).expanduser().resolve()
        metadata_path = root / "host.json"
        if not metadata_path.exists():
            raise FileNotFoundError("host.json is required before DUCK backup")
        host_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(prefix="duck-backup-") as temp_name:
            stage = Path(temp_name) / "payload"
            stage.mkdir(parents=True)
            shutil.copy2(metadata_path, stage / "host.json")
            cartridge = root / "config" / "cartridge.snp"
            if not cartridge.exists():
                raise FileNotFoundError("pinned cartridge missing from DUCK host")
            (stage / "config").mkdir()
            shutil.copy2(cartridge, stage / "config" / "cartridge.snp")
            database = root / "wayfarer.sqlite3"
            if database.exists():
                _copy_sqlite(database, stage / "wayfarer.sqlite3")
            duck_root = root / "duck"
            if duck_root.exists():
                shutil.copytree(duck_root, stage / "duck")

            files: dict[str, str] = {}
            for path in sorted(stage.rglob("*")):
                if path.is_file():
                    relative = path.relative_to(stage).as_posix()
                    files[relative] = _hash(path)
            manifest = {
                "schema": BACKUP_SCHEMA,
                "subject_id": str(host_metadata.get("subject_id", "")),
                "files": files,
            }
            (stage / "manifest.json").write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = archive_path.with_suffix(archive_path.suffix + ".tmp")
            with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for path in sorted(stage.rglob("*")):
                    if path.is_file():
                        archive.write(path, path.relative_to(stage).as_posix())
            os.replace(temporary, archive_path)
        return {
            "archive": str(archive_path),
            "subject_id": manifest["subject_id"],
            "file_count": len(files),
            "sha256": _hash(archive_path),
        }

    @staticmethod
    def inspect(archive_path: str | Path) -> dict[str, Any]:
        archive_path = Path(archive_path).expanduser().resolve()
        with zipfile.ZipFile(archive_path, "r") as archive:
            names = archive.namelist()
            DuckBackupManager._validate_names(names)
            try:
                manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
            except KeyError as exc:
                raise ValueError("DUCK backup has no manifest.json") from exc
        if manifest.get("schema") != BACKUP_SCHEMA:
            raise ValueError(f"unsupported DUCK backup schema: {manifest.get('schema')}")
        return manifest

    @staticmethod
    def restore(
        archive_path: str | Path,
        destination_root: str | Path,
        *,
        overwrite: bool = False,
        expected_subject_id: str | None = None,
    ) -> dict[str, Any]:
        archive_path = Path(archive_path).expanduser().resolve()
        destination_root = Path(destination_root).expanduser().resolve()
        manifest = DuckBackupManager.inspect(archive_path)
        subject_id = str(manifest.get("subject_id", ""))
        if expected_subject_id and subject_id != str(expected_subject_id):
            raise ValueError("backup subject_id does not match expected subject")
        if destination_root.exists() and any(destination_root.iterdir()) and not overwrite:
            raise FileExistsError("restore destination is not empty; pass overwrite=True explicitly")

        with tempfile.TemporaryDirectory(prefix="duck-restore-") as temp_name:
            stage = Path(temp_name) / "payload"
            stage.mkdir(parents=True)
            with zipfile.ZipFile(archive_path, "r") as archive:
                names = archive.namelist()
                DuckBackupManager._validate_names(names)
                archive.extractall(stage)
            files = dict(manifest.get("files", {}))
            for relative, expected in files.items():
                path = stage / relative
                if not path.exists() or not path.is_file():
                    raise ValueError(f"backup payload missing file: {relative}")
                if _hash(path) != str(expected):
                    raise ValueError(f"backup checksum mismatch: {relative}")
            actual_payload_files = {
                path.relative_to(stage).as_posix()
                for path in stage.rglob("*")
                if path.is_file() and path.name != "manifest.json"
            }
            if actual_payload_files != set(files):
                raise ValueError("backup contains unmanifested or missing payload files")

            destination_root.mkdir(parents=True, exist_ok=True)
            if overwrite:
                for child in list(destination_root.iterdir()):
                    if child.is_dir():
                        shutil.rmtree(child)
                    else:
                        child.unlink()
            for relative in sorted(files):
                source = stage / relative
                target = destination_root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
        return {
            "destination": str(destination_root),
            "subject_id": subject_id,
            "file_count": len(manifest.get("files", {})),
        }

    @staticmethod
    def _validate_names(names: list[str]) -> None:
        for raw in names:
            normalized = raw.replace("\\", "/")
            path = Path(normalized)
            if path.is_absolute() or ".." in path.parts or normalized.startswith("/"):
                raise ValueError(f"unsafe backup member path: {raw}")
