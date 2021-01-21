#!/bin/bash

if [ "$(whoami)" != "root" ]; then
    tor -f /etc/tor/torrc
else
    service tor start
fi
