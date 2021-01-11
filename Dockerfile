FROM python:3.8-slim

WORKDIR /usr/src/app
RUN apt-get update && apt-get install -y \
    build-essential \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    libxslt-dev \
    libffi-dev \
    tor

COPY misc/tor/torrc /etc/tor/torrc
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ARG config_dir=/config
RUN mkdir -p $config_dir
VOLUME $config_dir
ENV CONFIG_VOLUME=$config_dir

ARG username=''
ENV WHOOGLE_USER=$username
ARG password=''
ENV WHOOGLE_PASS=$password

ARG proxyuser=''
ENV WHOOGLE_PROXY_USER=$proxyuser
ARG proxypass=''
ENV WHOOGLE_PROXY_PASS=$proxypass
ARG proxytype=''
ENV WHOOGLE_PROXY_TYPE=$proxytype
ARG proxyloc=''
ENV WHOOGLE_PROXY_LOC=$proxyloc

ARG use_https=''
ENV HTTPS_ONLY=$use_https

ARG whoogle_port=5000
ENV EXPOSE_PORT=$whoogle_port

ARG twitter_alt='nitter.net'
ENV WHOOGLE_ALT_TW=$twitter_alt
ARG youtube_alt='invidious.snopyta.org'
ENV WHOOGLE_ALT_YT=$youtube_alt
ARG instagram_alt='bibliogram.art/u'
ENV WHOOGLE_ALT_YT=$instagram_alt

COPY . .

EXPOSE $EXPOSE_PORT

CMD misc/tor/start-tor.sh & ./run
