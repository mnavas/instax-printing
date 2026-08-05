#!/usr/bin/env bash
# Launch instax-printing. On first run it creates a local .venv and installs
# dependencies; after that it just starts the app.
set -euo pipefail

cd "$(dirname "$(readlink -f "$0")")"

VENV=".venv"
PYTHON="${PYTHON:-python3}"

if [ ! -d "$VENV" ]; then
    echo "First run — creating virtual environment in $VENV ..."
    "$PYTHON" -m venv "$VENV"
    "$VENV/bin/pip" install --upgrade pip >/dev/null
    echo "Installing dependencies ..."
    "$VENV/bin/pip" install -r requirements.txt
fi

exec "$VENV/bin/python" main.py "$@"
