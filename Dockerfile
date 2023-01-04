FROM python:3.11.0a5-alpine as builder

RUN apk --update add \
    build-base \
    libxml2-dev \
    libxslt-dev \
    openssl-dev \
    libffi-dev

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --prefix /install --no-warn-script-location --no-cache-dir -r requirements.txt

FROM python:3.11.0a5-alpine

RUN apk add --update --no-cache tor curl openrc libstdc++
# libcurl4-openssl-dev

RUN apk -U upgrade

ARG DOCKER_USER=whoogle
ARG DOCKER_USERID=927
ARG config_dir=/config
RUN mkdir -p $config_dir
RUN chmod a+w $config_dir
VOLUME $config_dir

ARG url_prefix=''
ARG username=''
ARG password=''
ARG proxyuser=''
ARG proxypass=''
ARG proxytype=''
ARG proxyloc=''
ARG whoogle_dotenv=''
ARG use_https=''
ARG whoogle_port=5000
ARG twitter_alt='farside.link/nitter'
ARG youtube_alt='farside.link/invidious'
ARG instagram_alt='farside.link/bibliogram/u'
ARG reddit_alt='farside.link/libreddit'
ARG medium_alt='farside.link/scribe'
ARG translate_alt='farside.link/lingva'
ARG imgur_alt='farside.link/rimgo'
ARG wikipedia_alt='farside.link/wikiless'
ARG imdb_alt='farside.link/libremdb'
ARG quora_alt='farside.link/quetre'

ENV CONFIG_VOLUME=$config_dir \
    WHOOGLE_URL_PREFIX=$url_prefix \
    WHOOGLE_USER=$username \
    WHOOGLE_PASS=$password \
    WHOOGLE_PROXY_USER=$proxyuser \
    WHOOGLE_PROXY_PASS=$proxypass \
    WHOOGLE_PROXY_TYPE=$proxytype \
    WHOOGLE_PROXY_LOC=$proxyloc \
    WHOOGLE_DOTENV=$whoogle_dotenv \
    HTTPS_ONLY=$use_https \
    EXPOSE_PORT=$whoogle_port \
    WHOOGLE_ALT_TW=$twitter_alt \
    WHOOGLE_ALT_YT=$youtube_alt \
    WHOOGLE_ALT_IG=$instagram_alt \
    WHOOGLE_ALT_RD=$reddit_alt \
    WHOOGLE_ALT_MD=$medium_alt \
    WHOOGLE_ALT_TL=$translate_alt \
    WHOOGLE_ALT_IMG=$imgur_alt \
    WHOOGLE_ALT_WIKI=$wikipedia_alt \
    WHOOGLE_ALT_IMDB=$imdb_alt \
    WHOOGLE_ALT_QUORA=$quora_alt

WORKDIR /whoogle

COPY --from=builder /install /usr/local
COPY misc/tor/torrc /etc/tor/torrc
COPY misc/tor/start-tor.sh misc/tor/start-tor.sh
COPY app/ app/
COPY run whoogle.env* ./

# Create user/group to run as
RUN adduser -D -g $DOCKER_USERID -u $DOCKER_USERID $DOCKER_USER

# Fix ownership / permissions
RUN chown -R ${DOCKER_USER}:${DOCKER_USER} /whoogle /var/lib/tor

# Allow writing symlinks to build dir
RUN chown $DOCKER_USERID:$DOCKER_USERID app/static/build

USER $DOCKER_USER:$DOCKER_USER

EXPOSE $EXPOSE_PORT

HEALTHCHECK --interval=30s --timeout=5s \
  CMD curl -f http://localhost:${EXPOSE_PORT}/healthz || exit 1

CMD misc/tor/start-tor.sh & ./run
