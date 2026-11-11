#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"
export PYTHONPATH="src"

if [ -x ".venv/bin/python" ]; then
    ".venv/bin/python" "src/filtros/ui/main_flet.py"
elif command -v python3 >/dev/null 2>&1; then
    python3 "src/filtros/ui/main_flet.py"
else
    python "src/filtros/ui/main_flet.py"
fi
