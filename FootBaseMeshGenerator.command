#!/bin/bash
set -e

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"
TTY_NAME="$(tty 2>/dev/null || true)"

echo "Foot Base Mesh Generator"
echo "Working directory: $APP_DIR"
echo
echo "Log file: $APP_DIR/foot_app_launch.log"
echo

unset PYTHONHOME
unset VIRTUAL_ENV
unset __PYVENV_LAUNCHER__

has_deps() {
  "$1" - <<'PY'
import importlib.util
missing = [m for m in ("PySimpleGUI", "cv2", "numpy") if importlib.util.find_spec(m) is None]
raise SystemExit(1 if missing else 0)
PY
}

choose_ready_python() {
  for candidate in \
    "/Users/naoto/miniforge3/envs/hand-obj/bin/python" \
    "/Users/naoto/miniforge3/envs/pose311/bin/python" \
    "$APP_DIR/.venv/bin/python" \
    "/Users/naoto/miniforge3/bin/python" \
    "$(command -v python3)"
  do
    if [ -x "$candidate" ] && has_deps "$candidate"; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}

APP_PYTHON="$(choose_ready_python || true)"

if [ -z "$APP_PYTHON" ]; then
  BASE_PYTHON="/Users/naoto/miniforge3/bin/python"
  if [ ! -x "$BASE_PYTHON" ]; then
    BASE_PYTHON="$(command -v python3)"
  fi
  if [ ! -d ".venv" ]; then
    echo "Creating local virtual environment with $BASE_PYTHON..."
    "$BASE_PYTHON" -m venv .venv
  fi
  APP_PYTHON="$APP_DIR/.venv/bin/python"
  echo "Installing dependencies..."
  "$APP_PYTHON" -m pip install --upgrade pip
  "$APP_PYTHON" -m pip install -r requirements.txt
fi

echo "Launching app with $APP_PYTHON..."
set +e
PYTHONPATH="$APP_DIR" "$APP_PYTHON" - <<'PY'
from main import main

main()
PY
APP_EXIT=$?
set -e

if [ "${TERM_PROGRAM:-}" = "Apple_Terminal" ] && [[ "$TTY_NAME" == /dev/ttys* ]]; then
  /usr/bin/osascript <<OSA >/dev/null 2>&1 &
tell application "Terminal"
  repeat with terminalWindow in windows
    repeat with terminalTab in tabs of terminalWindow
      if tty of terminalTab is "$TTY_NAME" then
        close terminalWindow
        return
      end if
    end repeat
  end repeat
end tell
OSA
fi

exit "$APP_EXIT"
