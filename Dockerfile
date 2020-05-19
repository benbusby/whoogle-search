FROM lsiobase/python:3.11

# set version release
ARG WHOOGLESEARCH_RELEASE
ARG BUILD_DATE=unspecified
ARG VCS_REF=unspecified

# set python to use utf-8 rather than ascii.
ENV PYTHONIOENCODING="UTF-8"

# enforced https, default false
ARG use_https=''
ENV HTTPS_ONLY="$use_https"

LABEL org.label-schema.name="Whoogle Search"
LABEL org.label-schema.description="Self-hosted, ad-free, privacy-respecting Google metasearch engine"
LABEL org.label-schema.vcs-url="https://github.com/benbusby/whoogle-search"
LABEL org.label-schema.build-date="${BUILD_DATE}"
LABEL org.label-schema.vcs-ref="${VCS_REF}"

RUN \
 echo "**** install build packages ****" && \
 apk add --no-cache --upgrade --virtual .build-dependencies \
      g++ \
      git \
      curl-dev \
      libressl-dev \
      libffi-dev \
      python3-dev && \
 echo "**** install runtime packages ****" && \
 apk add --no-cache --upgrade \
      curl \
      py3-pip \
      python3 \
      tar && \
 echo "**** install app ****" && \
 mkdir -p \
      /tmp/whooglesearch && \
 if [ -z ${WHOOGLESEARCH_RELEASE+x} ]; then \
      WHOOGLESEARCH_RELEASE=$(curl -sX GET "https://api.github.com/repos/benbusby/whoogle-search/commits/master" \
      | awk '/sha/{print $4;exit}' FS='[""]'); \
 fi && \
 curl -o \
      /tmp/whooglesearch.tar.gz -L \
      "https://github.com/benbusby/whoogle-search/archive/${WHOOGLESEARCH_RELEASE}.tar.gz" && \
 tar xf \
      /tmp/whooglesearch.tar.gz -C \
      /tmp/whooglesearch --strip-components=1 && \
 echo "**** install pip packages ****" && \
 pip3 install --no-cache-dir -r \
      /tmp/whooglesearch/requirements.txt && \
      cp -r /tmp/whooglesearch/app / && \
 echo "**** clean up ****" && \
 apk del --purge \
	.build-dependencies && \
 rm -rf \
	/tmp/*

# set config location
ENV CONFIG_VOLUME="/config"

# add local files
COPY root/ /

# ports and volumes
EXPOSE 5000
VOLUME /config
