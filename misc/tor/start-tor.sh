#!/bin/sh

FF_STRING="FascistFirewall 1"

if [ "$WHOOGLE_TOR_SERVICE" == "0" ]; then
    echo "Skipping Tor startup..."
    exit 0
fi

if [ "$WHOOGLE_TOR_FF" == "1" ]; then
    if (grep -q "$FF_STRING" /etc/tor/torrc); then
        echo "FascistFirewall feature already enabled."
    else
        echo "$FF_STRING" >> /etc/tor/torrc

        if [ "$?" -eq 0 ]; then
            echo "FascistFirewall added to /etc/tor/torrc"
        else
            echo "ERROR: Unable to modify /etc/tor/torrc with $FF_STRING."
            exit 1
        fi
    fi
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
