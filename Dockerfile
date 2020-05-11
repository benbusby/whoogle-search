FROM lsiobase/python:3.11

ARG WHOOGLESEARCH_RELEASE
ARG BUILD_DATE=unspecified
ARG VCS_REF=unspecified

# set python to use utf-8 rather than ascii.
ENV PYTHONIOENCODING="UTF-8"

LABEL org.label-schema.name="Whoogle Search"
LABEL org.label-schema.description="Self-hosted, ad-free, privacy-respecting alternative to Google search"
LABEL org.label-schema.vcs-url="https://github.com/benbusby/whoogle-search"
LABEL org.label-schema.build-date="${BUILD_DATE:-unspecified}"
LABEL org.label-schema.vcs-ref="${VCS_REF:-unspecified}"

RUN \
 echo "**** install build packages ****" && \
 apk add --no-cache --upgrade \
	cmake \
	g++ \
	gcc \
	git \
	make \
	curl-dev \
	libressl-dev \
	libffi-dev \
	python3-dev && \
 echo "**** install runtime packages ****" && \
 apk add --no-cache --upgrade \
	curl \
	nano \
	py3-pip \
	py3-pylast \
	python3 \
	tar \
	wget && \
 echo "**** install app ****" && \
 mkdir -p /tmp/whooglesearch && \
 if [ -z ${WHOOGLESEARCH_RELEASE+x} ]; then \
 	WHOOGLESEARCH_RELEASE=$(curl -sX GET "https://api.github.com/repos/benbusby/whoogle-search/commits/master" \
        | awk '/sha/{print $4;exit}' FS='[""]'); \
 fi && \
 curl -o \
	/tmp/whooglesearch.tar.gz -L \
	"https://github.com/benbusby/whoogle-search/archive/${WHOOGLESEARCH_RELEASE}.tar.gz" && \
 tar xf /tmp/whooglesearch.tar.gz -C \
	/tmp/whooglesearch --strip-components=1 && \
 echo "**** install pip packages ****" && \
 pip3 install --no-cache-dir -r \
	/tmp/whooglesearch/requirements.txt && \
	cp -r /tmp/whooglesearch/app / && \
 echo "**** Cleanup ****" && \
 rm -Rf /tmp/*

# add local files
COPY root/ /

WORKDIR /app

# ports and volumes
EXPOSE 5000
