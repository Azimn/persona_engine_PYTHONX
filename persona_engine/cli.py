"""Small command-line entry points for local package installs."""

from __future__ import annotations

import argparse


def run_ui(argv=None) -> int:
    """Run the optional FastAPI human-testing UI with Uvicorn."""

    parser = argparse.ArgumentParser(description="Run the Persona Engine human-testing UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--cartridge", default=None)
    parser.add_argument("--db", default="persona_ui_state.db")
    parser.add_argument("--user-id", default="ui_user")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args(argv)

    try:
        import uvicorn
    except Exception as exc:  # pragma: no cover - exercised by dependency setup, not core tests
        raise SystemExit("Install UI dependencies with: python -m pip install -r requirements-ui.txt") from exc

    from .ui import create_app

    app = create_app(
        cartridge_path=args.cartridge,
        db_path=args.db,
        user_id=args.user_id,
        debug=args.debug,
    )
    uvicorn.run(app, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(run_ui())
