#!/bin/sh
# Usage:
# ./run # Runs the full web app
# ./run test # Runs the testing suite

set -e

SCRIPT_DIR="$(CDPATH= command cd -- "$(dirname -- "$0")" && pwd -P)"

# Set directory to serve static content from
SUBDIR="${1:-app}"
export APP_ROOT="$SCRIPT_DIR/$SUBDIR"
export STATIC_FOLDER="$APP_ROOT/static"

# Clear out build directory
rm -f "$SCRIPT_DIR"/app/static/build/*.js
rm -f "$SCRIPT_DIR"/app/static/build/*.css

# Check for regular vs test run
if [ "$SUBDIR" = "test" ]; then
    # Set up static files for testing
    rm -rf "$STATIC_FOLDER"
    ln -s "$SCRIPT_DIR/app/static" "$STATIC_FOLDER"
    pytest -sv
else
    mkdir -p "$STATIC_FOLDER"

    if [ ! -z "$UNIX_SOCKET" ]; then
        python3 -um app \
          --unix-socket "$UNIX_SOCKET"
    else
        python3 -um app \
          --host "${ADDRESS:-0.0.0.0}" \
          --port "${PORT:-"${EXPOSE_PORT:-5000}"}"
    fi
fi
