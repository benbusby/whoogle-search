#!/bin/sh

if [ "$WHOOGLE_TOR_SERVICE" == "0" ]; then
    echo "Skipping Tor startup..."
    exit 0
fi

if [ "$(whoami)" != "root" ]; then
    tor -f /etc/tor/torrc
else
    if (grep alpine /etc/os-release >/dev/null); then
        rc-service tor start
    else
        service tor start
    fi
fi
