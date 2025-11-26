# NOTE: ARMv7 support has been dropped due to lack of pre-built cryptography wheels for Alpine/musl.
# To restore ARMv7 support for local builds:
# 1. Change requirements.txt:
#    cryptography==3.3.2; platform_machine == 'armv7l'
#    cryptography==46.0.1; platform_machine != 'armv7l'
#    pyOpenSSL==19.1.0; platform_machine == 'armv7l'
#    pyOpenSSL==25.3.0; platform_machine != 'armv7l'
# 2. Add linux/arm/v7 to --platform flag when building:
#    docker buildx build --platform linux/amd64,linux/arm/v7,linux/arm64 .

FROM python:3.12-alpine3.22 AS builder

RUN apk --no-cache add \
    build-base \
    libxml2-dev \
    libxslt-dev \
    openssl-dev \
    libffi-dev

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --prefix /install --no-warn-script-location --no-cache-dir -r requirements.txt

FROM python:3.12-alpine3.22

# Remove bridge package to avoid CVEs (not needed for Docker containers)
RUN apk add --no-cache --no-scripts tor curl openrc libstdc++ && \
    apk del --no-cache bridge || true
# git go //for obfs4proxy
# libcurl4-openssl-dev
RUN pip install --upgrade pip
RUN apk --no-cache upgrade && \
    apk del --no-cache --rdepends bridge || true

# uncomment to build obfs4proxy
# RUN git clone https://gitlab.com/yawning/obfs4.git
# WORKDIR /obfs4
# RUN go build -o obfs4proxy/obfs4proxy ./obfs4proxy
# RUN cp ./obfs4proxy/obfs4proxy /usr/bin/obfs4proxy

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
ARG reddit_alt='farside.link/libreddit'
ARG medium_alt='farside.link/scribe'
ARG translate_alt='farside.link/lingva'
ARG imgur_alt='farside.link/rimgo'
ARG wikipedia_alt='farside.link/wikiless'
ARG imdb_alt='farside.link/libremdb'
ARG quora_alt='farside.link/quetre'
ARG so_alt='farside.link/anonymousoverflow'

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
    WHOOGLE_ALT_RD=$reddit_alt \
    WHOOGLE_ALT_MD=$medium_alt \
    WHOOGLE_ALT_TL=$translate_alt \
    WHOOGLE_ALT_IMG=$imgur_alt \
    WHOOGLE_ALT_WIKI=$wikipedia_alt \
    WHOOGLE_ALT_IMDB=$imdb_alt \
    WHOOGLE_ALT_QUORA=$quora_alt \
    WHOOGLE_ALT_SO=$so_alt

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

CMD ["/bin/sh", "-c", "misc/tor/start-tor.sh & ./run"]
