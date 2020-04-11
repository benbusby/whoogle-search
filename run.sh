#!/bin/bash

SCRIPT=`realpath $0`
SCRIPT_DIR=`dirname $SCRIPT`

if [[ -z "${PORT}" ]]; then
    PORT=5000
fi

# Create config json if it doesn't exist
if [[ ! -f $SCRIPT_DIR/app/static/config.json ]]; then
    echo "{}" > $SCRIPT_DIR/app/static/config.json
fi

pkill flask

flask run --host="0.0.0.0" --port=$PORT
