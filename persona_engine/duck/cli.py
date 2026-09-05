"""Command-line entry point for the DUCK future runtime."""

from __future__ import annotations

import argparse
import ipaddress
import json
from pathlib import Path
import sys

from .backup import DuckBackupManager
from .host import FutureDuckHost


def _host_from_args(args) -> FutureDuckHost:
    host = FutureDuckHost.open(
        args.root,
        cartridge_path=getattr(args, "cartridge", None),
        user_id=getattr(args, "user_id", None),
        host_id=getattr(args, "host_id", "local"),
        ollama_host=getattr(args, "ollama_host", "http://127.0.0.1:11434"),
        debug=getattr(args, "debug", False),
    )
    provider = getattr(args, "provider", "offline")
    model = getattr(args, "model", "offline-template")
    if provider != "offline" or model != "offline-template":
        host.set_renderer({
            "provider": provider,
            "model_name": model,
            "thinking_mode": getattr(args, "thinking", "off"),
            "timeout_seconds": getattr(args, "timeout", 60.0),
            "token_budget": getattr(args, "tokens", 256),
        })
    return host


def _add_host_options(parser):
    parser.add_argument("--root", default="duck_state", help="Persistent DUCK host directory")
    parser.add_argument("--cartridge", default=None, help="Cartridge used only when creating a new host")
    parser.add_argument("--user-id", default=None)
    parser.add_argument("--host-id", default="local")
    parser.add_argument("--ollama-host", default="http://127.0.0.1:11434")


def _add_renderer_options(parser):
    parser.add_argument("--provider", choices=["offline", "ollama"], default="offline")
    parser.add_argument("--model", default="offline-template")
    parser.add_argument("--thinking", choices=["auto", "on", "off"], default="off")
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--tokens", type=int, default=256)


def _loopback_only(bind: str) -> bool:
    if bind.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(bind).is_loopback
    except ValueError:
        return False


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run the DUCK future cognitive-organism runtime")
    subparsers = parser.add_subparsers(dest="command", required=True)

    chat = subparsers.add_parser("chat", help="Interactive terminal conversation")
    _add_host_options(chat); _add_renderer_options(chat)

    send = subparsers.add_parser("send", help="Send one message and print the response")
    _add_host_options(send); _add_renderer_options(send)
    send.add_argument("text")

    status = subparsers.add_parser("status", help="Show public runtime status")
    _add_host_options(status)

    discover = subparsers.add_parser("renderers", help="Discover available renderer backends")
    _add_host_options(discover)

    serve = subparsers.add_parser("serve", help="Run local DUCK HTTP API")
    _add_host_options(serve); _add_renderer_options(serve)
    serve.add_argument("--bind", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--allow-remote", action="store_true", help="Explicitly allow non-loopback API binding")
    serve.add_argument("--debug", action="store_true")

    backup = subparsers.add_parser("backup", help="Create a portable checksum-verified backup")
    _add_host_options(backup)
    backup.add_argument("archive")

    restore = subparsers.add_parser("restore", help="Restore a DUCK host backup")
    restore.add_argument("archive")
    restore.add_argument("--root", default="duck_state")
    restore.add_argument("--overwrite", action="store_true")

    args = parser.parse_args(argv)

    if args.command == "restore":
        result = DuckBackupManager.restore(args.archive, args.root, overwrite=args.overwrite)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    host = _host_from_args(args)

    if args.command == "status":
        print(json.dumps(host.public_status(), indent=2, sort_keys=True))
        return 0
    if args.command == "renderers":
        print(json.dumps(host.discover_renderers(), indent=2, sort_keys=True))
        return 0
    if args.command == "send":
        result = host.send(args.text)
        if result["response"] is not None:
            print(result["response"])
        else:
            print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.command == "backup":
        host.save()
        result = DuckBackupManager.create(host.root, args.archive)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.command == "chat":
        print(f"DUCK subject {host.subject.subject_id}. Type /quit to exit.")
        while True:
            try:
                text = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not text:
                continue
            if text in {"/quit", "/exit"}:
                break
            result = host.send(text)
            print(result["response"] if result["response"] is not None else "[no outward action]")
        host.save()
        return 0
    if args.command == "serve":
        if not _loopback_only(args.bind) and not args.allow_remote:
            parser.error("non-loopback binding requires --allow-remote")
        try:
            import uvicorn
        except Exception as exc:
            raise SystemExit("Install server dependencies with: pip install -e '.[ui]'") from exc
        from .api import create_app
        uvicorn.run(create_app(host, debug=args.debug), host=args.bind, port=args.port)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
