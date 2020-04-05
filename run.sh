#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Set NOJS mode to false if unavailable
if [[ -z "$NOJS" ]]; then
    export NOJS=0
fi

# Create config json if it doesn't exist
if [[ -f $SCRIPT_DIR/config.json ]]; then
    echo "{}" > $SCRIPT_DIR/config.json
fi

pkill flask

# TODO: Set up the following for running over https
#--cert=./app/cert.pem --key=./app/key.pem
$SCRIPT_DIR/venv/bin/flask run
