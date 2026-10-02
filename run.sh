#!/usr/bin/env sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ "${1:-}" = "--check" ]; then
	exec python3 "$SCRIPT_DIR/aegisai_text_injection_test/bootstrap.py" --check
fi
exec python3 "$SCRIPT_DIR/aegisai_text_injection_test/bootstrap.py" -- "$@"