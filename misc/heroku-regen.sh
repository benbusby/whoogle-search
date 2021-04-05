#!/bin/bash
# Assumes this is being executed from a session that has already logged
# into Heroku with "heroku login -i" beforehand.
# 
# You can set this up to run every night when you aren't using the
# instance with a cronjob. For example:
# 0 3 * * * /home/pi/whoogle-search/config/heroku-regen.sh <app_name>

HEROKU_CLI_SITE="https://devcenter.heroku.com/articles/heroku-cli"

if ! [[ -x "$(command -v heroku)" ]]; then
    echo "Must have heroku cli installed: $HEROKU_CLI_SITE"
    exit 1
fi

cd "$(builtin cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)/../"

if [[ $# -ne 1 ]]; then
    echo -e "Must provide the name of the Whoogle instance to regenerate"
    exit 1
fi

APP_NAME="$1"

heroku apps:destroy "$APP_NAME" --confirm "$APP_NAME"
heroku apps:create "$APP_NAME"
heroku container:login
heroku container:push web
heroku container:release web
