#!/bin/zsh

docker build --tag whoogle-search:1.0 . && docker run --publish 5000:5000 --detach --name whoogle-search whoogle-search:1.0
