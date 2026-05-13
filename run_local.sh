#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
DB_PATH="${DB_PATH:-investment_analysis.db}"

if [[ -n "${PYTHON:-}" ]]; then
  PYTHON_BIN="${PYTHON}"
elif [[ -n "${VIRTUAL_ENV:-}" && -x "${VIRTUAL_ENV}/bin/python" ]]; then
  PYTHON_BIN="${VIRTUAL_ENV}/bin/python"
elif [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
else
  PYTHON_BIN="python3"
fi

if ! "${PYTHON_BIN}" -c "import pandas, openpyxl" >/dev/null 2>&1; then
  echo "Missing Python dependencies in: $("${PYTHON_BIN}" -c 'import sys; print(sys.executable)')"
  echo "Installing project dependencies..."
  "${PYTHON_BIN}" -m pip install -e .
fi

PORT_PIDS="$(lsof -ti tcp:"${PORT}" 2>/dev/null || true)"
if [[ -n "${PORT_PIDS}" ]]; then
  echo "Port ${PORT} is already in use. Stopping existing process(es): ${PORT_PIDS//$'\n'/ }"
  kill ${PORT_PIDS}
  sleep 1
fi

echo "Starting investment analysis service..."
echo "URL: http://${HOST}:${PORT}/"
echo "Python: $("${PYTHON_BIN}" -c 'import sys; print(sys.executable)')"

exec "${PYTHON_BIN}" -m investment_analysis.api --host "${HOST}" --port "${PORT}" --db "${DB_PATH}"
