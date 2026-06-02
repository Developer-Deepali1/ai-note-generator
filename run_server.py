#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CLIENT_DIR = ROOT / 'client'
SERVER_DIR = ROOT / 'server'


def run_command(cmd: list[str], cwd: Path | None = None) -> int:
    try:
        return subprocess.call(cmd, cwd=str(cwd) if cwd else None)
    except FileNotFoundError:
        print(f"Command not found: {cmd[0]}")
        return 127


def build_frontend() -> None:
    print('Building frontend (client)...')
    if not CLIENT_DIR.exists():
        print('client directory not found; please ensure you are in the project root.')
        return
    # Check for npm availability
    npm_path = shutil.which('npm')
    dist_dir = CLIENT_DIR / 'dist'
    if npm_path is None:
        if dist_dir.exists():
            print('`npm` not found in PATH — skipping build and using existing `client/dist`.')
            return
        print('`npm` not found in PATH and `client/dist` is missing.')
        print('Starting backend only. Install Node.js/npm later if you want the frontend served from Flask.')
        return

    # Run the build (npm available)
    code = run_command(['npm.cmd', 'run', 'build'], cwd=CLIENT_DIR) 
    if code != 0:
        if dist_dir.exists():
            print('Frontend build failed (npm returned code', code, '), but existing `client/dist` will be used.')
            return
        print('Frontend build failed (npm returned code', code, '). Starting backend only.')


def start_backend() -> None:
    print('Starting backend (Flask)...')
    # Make sure server package is importable
    sys.path.insert(0, str(SERVER_DIR))
    try:
        from app import create_app

        app = create_app()
        host = os.getenv('HOST', '0.0.0.0')
        port = int(os.getenv('PORT', '5000'))
        debug = os.getenv('FLASK_DEBUG', '0') in ('1', 'true', 'True')
        app.run(host=host, port=port, debug=debug)
    except Exception as exc:
        print('Failed to start backend:', exc)
        sys.exit(1)


def main() -> None:
    # 1) Build frontend
    build_frontend()
    # 2) Start backend (serves built frontend)
    start_backend()


if __name__ == '__main__':
    main()
