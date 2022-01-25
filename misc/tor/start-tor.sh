#!/bin/sh

if [ "$(whoami)" != "root" ]; then
    tor -f /etc/tor/torrc
else
    if (grep alpine /etc/os-release >/dev/null); then
        rc-service tor start
    else
        service tor start
    fi
fi
