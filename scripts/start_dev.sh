#!/bin/bash
# Helper to launch OmniBAR dev environment.
# Opens three Terminal tabs (macOS) for backend, frontend, and a spare shell.

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENVDIR="$ROOT_DIR/.venv"

if [ ! -d "$VENVDIR" ]; then
  python3 -m venv "$VENVDIR"
fi

activate_venv="source $VENVDIR/bin/activate"

# pull OPENAI_API_KEY from .env if present
OPENAI_LINE=$(grep '^OPENAI_API_KEY=' "$ROOT_DIR/.env" 2>/dev/null)
if [ -n "$OPENAI_LINE" ]; then
  OPENAI_VALUE="${OPENAI_LINE#OPENAI_API_KEY=}"  # keep surrounding quotes if user added them
else
  OPENAI_VALUE=""
fi

BACKEND_CMD="cd $ROOT_DIR && $activate_venv && export PYTHONPATH=$ROOT_DIR:\$PYTHONPATH"
if [ -n "$OPENAI_VALUE" ]; then
  BACKEND_CMD+=" && export OPENAI_API_KEY=$OPENAI_VALUE"
fi
BACKEND_CMD+=" && uvicorn backend.app:app --reload --port 8000"

FRONTEND_CMD="cd $ROOT_DIR/frontend && $activate_venv && npm install && npm run dev"

SHELL_CMD="cd $ROOT_DIR && $activate_venv"

osascript <<OSA
on run_command(cmd)
  tell application "Terminal"
    do script cmd
  end tell
end run_command

run_command "$BACKEND_CMD"
run_command "$FRONTEND_CMD"
run_command "$SHELL_CMD"
OSA
