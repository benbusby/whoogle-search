FROM python:3.8-slim as builder

RUN apt-get update && apt-get install -y \
    build-essential \
    libxml2-dev \
    libxslt-dev \
    libssl-dev \
    libffi-dev

COPY requirements.txt .

RUN pip install --prefix /install --no-warn-script-location --no-cache-dir -r requirements.txt

FROM python:3.8-slim

RUN apt-get update && apt-get install -y \
    libcurl4-openssl-dev \
    tor \
    curl \
    && rm -rf /var/lib/apt/lists/*

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

ARG whoogle_dotenv=''
ENV WHOOGLE_DOTENV=$whoogle_dotenv

ARG use_https=''
ENV HTTPS_ONLY=$use_https

ARG whoogle_port=5000
ENV EXPOSE_PORT=$whoogle_port

ARG twitter_alt='nitter.net'
ENV WHOOGLE_ALT_TW=$twitter_alt
ARG youtube_alt='invidious.snopyta.org'
ENV WHOOGLE_ALT_YT=$youtube_alt
ARG instagram_alt='bibliogram.art/u'
ENV WHOOGLE_ALT_IG=$instagram_alt
ARG reddit_alt='libredd.it'
ENV WHOOGLE_ALT_RD=$reddit_alt
ARG translate_alt='lingva.ml'
ENV WHOOGLE_ALT_TL=$translate_alt

WORKDIR /whoogle

COPY --from=builder /install /usr/local
COPY misc/tor/torrc /etc/tor/torrc
COPY misc/tor/start-tor.sh misc/tor/start-tor.sh
COPY app/ app/
COPY run .
COPY whoogle.env .

# Allow writing symlinks to build dir
RUN chown 102:102 app/static/build

EXPOSE $EXPOSE_PORT

HEALTHCHECK  --interval=30s --timeout=5s \
  CMD curl -f http://localhost:${EXPOSE_PORT}/healthz || exit 1

CMD misc/tor/start-tor.sh & ./run
