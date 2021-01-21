![Whoogle Search](docs/banner.png)

[![Latest Release](https://img.shields.io/github/v/release/benbusby/whoogle-search)](https://github.com/benbusby/shoogle/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://travis-ci.com/benbusby/whoogle-search.svg?branch=master)](https://travis-ci.com/benbusby/whoogle-search)
[![pep8](https://github.com/benbusby/whoogle-search/workflows/pep8/badge.svg)](https://github.com/benbusby/whoogle-search/actions?query=workflow%3Apep8)
[![codebeat badge](https://codebeat.co/badges/e96cada2-fb6f-4528-8285-7d72abd74e8d)](https://codebeat.co/projects/github-com-benbusby-shoogle-master)
[![Docker Pulls](https://img.shields.io/docker/pulls/benbusby/whoogle-search)](https://hub.docker.com/r/benbusby/whoogle-search)

Get Google search results, but without any ads, javascript, AMP links, cookies, or IP address tracking. Easily deployable in one click as a Docker app, and customizable with a single config file. Quick and simple to implement as a primary search engine replacement on both desktop and mobile.

Contents
1. [Features](#features)
2. [Dependencies](#dependencies)
3. [Install/Deploy](#install)
4. [Environment Variables](#environment-variables)
5. [Usage](#usage)
6. [Extra Steps](#extra-steps)
7. [FAQ](#faq)
8. [Screenshots](#screenshots)

## Features
- No ads or sponsored content
- No javascript
- No cookies
- No tracking/linking of your personal IP address\*
- No AMP links
- No URL tracking tags (i.e. utm=%s)
- No referrer header
- Tor and HTTP/SOCKS proxy support
- Autocomplete/search suggestions
- POST request search and suggestion queries (when possible)
- View images at full res without site redirect (currently mobile only)
- Dark mode
- Randomly generated User Agent
- Easy to install/deploy
- DDG-style bang (i.e. `!<tag> <query>`) searches
- Optional location-based searching (i.e. results near \<city\>)
- Optional NoJS mode to disable all Javascript in results

<sup>*If deployed to a remote server, or configured to send requests through a VPN, Tor, proxy, etc.</sup>

## Dependencies
If using Heroku Quick Deploy, **you can skip this section**.

- Docker ([Windows](https://docs.docker.com/docker-for-windows/install/), [macOS](https://docs.docker.com/docker-for-mac/install/), [Ubuntu](https://docs.docker.com/engine/install/ubuntu/), [other Linux distros](https://docs.docker.com/engine/install/binaries/))
  - Only needed if you intend on deploying the app as a Docker image
- [Python3](https://www.python.org/downloads/)
- `libcurl4-openssl-dev` and `libssl-dev`
  - macOS: `brew install openssl curl-openssl`
  - Ubuntu: `sudo apt-get install -y libcurl4-openssl-dev libssl-dev`
  - Arch: `pacman -S curl openssl`

## Install
There are a few different ways to begin using the app, depending on your preferences:

### A) [Heroku Quick Deploy](https://heroku.com/about)
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/benbusby/whoogle-search/tree/heroku-app)

*Note: Requires a (free) Heroku account*

Provides:
- Free deployment of app
- Free HTTPS url (https://\<your app name\>.herokuapp.com)
- Downtime after periods of inactivity \([solution](https://github.com/benbusby/whoogle-search#prevent-downtime-heroku-only)\)

### B) [Repl.it](https://repl.it)
[![Run on Repl.it](https://repl.it/badge/github/benbusby/whoogle-search)](https://repl.it/github/benbusby/whoogle-search)

Provides:
- Free deployment of app
- Free HTTPS url (https://\<app name\>.\<username\>\.repl\.co)
    - Supports custom domains
- Downtime after periods of inactivity \([solution 1](https://repl.it/talk/ask/use-this-pingmat1replco-just-enter/28821/101298), [solution 2](https://repl.it/talk/learn/How-to-use-and-setup-UptimeRobot/9003)\)

### C) [pipx](https://github.com/pipxproject/pipx#install-pipx)
Persistent install:

`pipx install git+https://github.com/benbusby/whoogle-search.git`

Sandboxed temporary instance:

`pipx run --spec git+https://github.com/benbusby/whoogle-search.git whoogle-search`

### D) pip
`pip install whoogle-search`

```bash
$ whoogle-search --help
usage: whoogle-search [-h] [--port <port number>] [--host <ip address>] [--debug]
                      [--https-only]

Whoogle Search console runner

optional arguments:
  -h, --help            show this help message and exit
  --port <port number>  Specifies a port to run on (default 5000)
  --host <ip address>   Specifies the host address to use (default 127.0.0.1)
  --debug               Activates debug mode for the server (default False)
  --https-only          Enforces HTTPS redirects for all requests (default False)
```
See the [available environment variables](#environment-variables) for additional configuration.

### E) Manual
Clone the repo and run the following commands to start the app in a local-only environment:

```bash
git clone https://github.com/benbusby/whoogle-search.git
cd whoogle-search
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./run
```
See the [available environment variables](#environment-variables) for additional configuration.

#### systemd Configuration
After building the virtual environment, you can add the following to `/lib/systemd/system/whoogle.service` to set up a Whoogle Search systemd service:

```
[Unit]
Description=Whoogle

[Service]
# Basic auth configuration, uncomment to enable
#Environment=WHOOGLE_USER=<username>
#Environment=WHOOGLE_PASS=<password>
# Proxy configuration, uncomment to enable
#Environment=WHOOGLE_PROXY_USER=<proxy username>
#Environment=WHOOGLE_PROXY_PASS=<proxy password>
#Environment=WHOOGLE_PROXY_TYPE=<proxy type (http|proxy4|proxy5)
#Environment=WHOOGLE_PROXY_LOC=<proxy host/ip>
# Site alternative configurations, uncomment to enable
# Note: If not set, the feature will still be available
# with default values. 
#Environment=WHOOGLE_ALT_TW=nitter.net
#Environment=WHOOGLE_ALT_YT=invidious.snopyta.org
#Environment=WHOOGLE_ALT_IG=bibliogram.art/u
Type=simple
User=root
WorkingDirectory=<whoogle_directory>
ExecStart=<whoogle_directory>/venv/bin/python3 -um app --host 0.0.0.0 --port 5000
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=3
SyslogIdentifier=whoogle

[Install]
WantedBy=multi-user.target
```
Then,
```
sudo systemctl daemon-reload
sudo systemctl enable whoogle
sudo systemctl start whoogle
```

### F) Manual (Docker)
1. Ensure the Docker daemon is running, and is accessible by your user account
  - To add user permissions, you can execute `sudo usermod -aG docker yourusername`
  - Running `docker ps` should return something besides an error. If you encounter an error saying the daemon isn't running, try `sudo systemctl start docker` (Linux) or ensure the docker tool is running (Windows/macOS).
2. Clone and deploy the docker app using a method below:

#### Docker CLI

***Note:** For ARM machines, use the `buildx-experimental` Docker tag.*

Through Docker Hub:
```bash
docker pull benbusby/whoogle-search
docker run --publish 5000:5000 --detach --name whoogle-search benbusby/whoogle-search:latest
```

or with docker-compose:

```bash
git clone https://github.com/benbusby/whoogle-search.git
cd whoogle-search
docker-compose up
```

or by building yourself:

```bash
git clone https://github.com/benbusby/whoogle-search.git
cd whoogle-search
docker build --tag whoogle-search:1.0 .
docker run --publish 5000:5000 --detach --name whoogle-search whoogle-search:1.0
```

Optionally, you can also enable some of the following environment variables to further customize your instance:

```bash
docker run --publish 5000:5000 --detach --name whoogle-search \
  -e WHOOGLE_USER=username \
  -e WHOOGLE_PASS=password \
  -e WHOOGLE_PROXY_USER=username \
  -e WHOOGLE_PROXY_PASS=password \
  -e WHOOGLE_PROXY_TYPE=socks5 \
  -e WHOOGLE_PROXY_LOC=ip \
  whoogle-search:1.0
```

And kill with: `docker rm --force whoogle-search`

#### Using [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
```bash
heroku login
heroku container:login
git clone https://github.com/benbusby/whoogle-search.git
cd whoogle-search
heroku create
heroku container:push web
heroku container:release web
heroku open
```

This series of commands can take a while, but once you run it once, you shouldn't have to run it again. The final command, `heroku open` will launch a tab in your web browser, where you can test out Whoogle and even [set it as your primary search engine](https://github.com/benbusby/whoogle#set-whoogle-as-your-primary-search-engine).
You may also edit environment variables from your app’s Settings tab in the Heroku Dashboard.

#### Using your own server, or alternative container deployment
There are other methods for deploying docker containers that are well outlined in [this article](https://rollout.io/blog/the-shortlist-of-docker-hosting/), but there are too many to describe set up for each here. Generally it should be about the same amount of effort as the Heroku deployment.

Depending on your preferences, you can also deploy the app yourself on your own infrastructure. This route would require a few extra steps:
  - A server (I personally recommend [Digital Ocean](https://www.digitalocean.com/pricing/) or [Linode](https://www.linode.com/pricing/), their cheapest tiers will work fine)
  - Your own URL (I suppose this is optional, but recommended)
  - SSL certificates (free through [Let's Encrypt](https://letsencrypt.org/getting-started/))
  - A bit more experience or willingness to work through issues

## Environment Variables
There are a few optional environment variables available for customizing a Whoogle instance:

| Variable           | Description                                                    |
| ------------------ | -------------------------------------------------------------- |
| WHOOGLE_USER       | The username for basic auth. WHOOGLE_PASS must also be set if used. |
| WHOOGLE_PASS       | The password for basic auth. WHOOGLE_USER must also be set if used. |
| WHOOGLE_PROXY_USER | The username of the proxy server.                              |
| WHOOGLE_PROXY_PASS | The password of the proxy server.                              |
| WHOOGLE_PROXY_TYPE | The type of the proxy server. Can be "socks5", "socks4", or "http".           |
| WHOOGLE_PROXY_LOC  | The location of the proxy server (host or ip).                 |
| EXPOSE_PORT        | The port where Whoogle will be exposed.                        |
| HTTPS_ONLY         | Enforce HTTPS. (See [here](https://github.com/benbusby/whoogle-search#https-enforcement)) |
| WHOOGLE_ALT_TW     | The twitter.com alternative to use when site alternatives are enabled in the config. |
| WHOOGLE_ALT_YT     | The youtube.com alternative to use when site alternatives are enabled in the config. |
| WHOOGLE_ALT_IG     | The instagram.com alternative to use when site alternatives are enabled in the config. |

## Usage
Same as most search engines, with the exception of filtering by time range.

To filter by a range of time, append ":past <time>" to the end of your search, where <time> can be `hour`, `day`, `month`, or `year`. Example: `coronavirus updates :past hour`

## Extra Steps
### Set Whoogle as your primary search engine
*Note: If you're using a reverse proxy to run Whoogle Search, make sure the "Root URL" config option on the home page is set to your URL before going through these steps.*

Update browser settings:
  - Firefox (Desktop)
    - Navigate to your app's url, and click the 3 dot menu in the address bar. At the bottom, there should be an option to "Add Search Engine". Once you've clicked this, open your Firefox Preferences menu, click "Search" in the left menu, and use the available dropdown to select "Whoogle" from the list.
  - Firefox (iOS)
    - In the mobile app Settings page, tap "Search" within the "General" section. There should be an option titled "Add Search Engine" to select. It should prompt you to enter a title and search query url - use the following elements to fill out the form:
      - Title: "Whoogle"
      - URL: `http[s]://\<your whoogle url\>/search?q=%s`
  - Firefox (Android)
    - Version <79.0.0
      - Navigate to your app's url
      - Long-press on the search text field
      - Click the "Add Search Engine" menu item
        - Select a name and click ok
      - Click the 3 dot menu in the top right
      - Navigate to the settings menu and select the "Search" sub-menu
      - Select Whoogle and press "Set as default"
    - Version >=79.0.0
      - Click the 3 dot menu in the top right
      - Navigate to the settings menu and select the "Search" sub-menu
      - Click "Add search engine"
      - Select the 'Other' radio button
        - Name: "Whoogle"
        - Search string to use: `https://\<your whoogle url\>/search?q=%s`
  - [Alfred](https://www.alfredapp.com/) (Mac OS X)
	  1. Go to `Alfred Preferences` > `Features` > `Web Search` and click `Add Custom Search`. Then configure these settings
		   - Search URL: `https://\<your whoogle url\>/search?q={query}
		   - Title: `Whoogle for '{query}'` (or whatever you want)
		   - Keyword: `whoogle`

	  2. Go to `Default Results` and click the `Setup fallback results` button. Click `+` and add Whoogle, then  drag it to the top.
  - Others (TODO)

### Customizing and Configuration
Whoogle currently allows a few minor configuration settings, accessible from the home page:
  - "Near"
    - Set to a city name to narrow your results to a general geographic region. This can be useful if you rely on being able to search for things like "pizza places" and see results in your city, rather than results from wherever the server is located.
  - Dark Mode
    - Sets background to pure black
  - NoJS Mode (Experimental)
    - Adds a separate link for each search result that will open the webpage without any javascript content served. Can be useful if you're seeking a no-javascript experience on mobile, but otherwise could just be accomplished with a browser plugin.

### Prevent Downtime (Heroku only)
Part of the deal with Heroku's free tier is that you're allocated 550 hours/month (meaning it can't stay active 24/7), and the app is temporarily shut down after 30 minutes of inactivity. Once it becomes inactive, any Whoogle searches will still work, but it'll take an extra 10-15 seconds for the app to come back online before displaying the result, which can be frustrating if you're in a hurry.

A good solution for this is to set up a simple cronjob on any device at your home that is consistently powered on and connected to the internet (in my case, a PiHole worked perfectly). All the device needs to do is fetch app content on a consistent basis to keep the app alive in whatever ~17 hour window you want it on (17 hrs * 31 days = 527, meaning you'd still have 23 leftover hours each month if you searched outside of your target window).

For instance, adding `*/20 7-23 * * * curl https://<your heroku app name>.herokuapp.com > /home/<username>/whoogle-refresh` will fetch the home page of the app every 20 minutes between 7am and midnight, allowing for downtime from midnight to 7am. And again, this wouldn't be a hard limit - you'd still have plenty of remaining hours of uptime each month in case you were searching after this window has closed.

Since the instance is destroyed and rebuilt after inactivity, config settings will be reset once the app enters downtime. If you have configuration settings active that you'd like to keep between periods of downtime (like dark mode for example), you could instead add `*/20 7-23 * * * curl -d "dark=1" -X POST https://<your heroku app name>.herokuapp.com/config > /home/<username>/whoogle-refresh` to keep these settings more or less permanent, and still keep the app from entering downtime when you're using it.

### HTTPS Enforcement
Only needed if your setup requires Flask to redirect to HTTPS on its own -- generally this is something that doesn't need to be handled by Whoogle Search.

Note: You should have your own domain name and [an https certificate](https://letsencrypt.org/getting-started/) in order for this to work properly.

- Heroku: Ensure that the `Root URL` configuration on the home page begins with `https://` and not `http://`
- Docker build: Add `--build-arg use_https=1` to your run command
- Docker image: Set the environment variable HTTPS_ONLY=1
- Pip/Pipx: Add the `--https-only` flag to the end of the `whoogle-search` command
- Default `run` script: Modify the script locally to include the `--https-only` flag at the end of the python run command

Available config values are `near`, `nojs`, `dark` and `url`.

## FAQ
**What's the difference between this and [Searx](https://github.com/asciimoo/searx)?**

Whoogle is intended to only ever be deployed to private instances by individuals of any background, with as little effort as possible. Prior knowledge of/experience with the command line or deploying applications is not necessary to deploy Whoogle, which isn't the case with Searx. As a result, Whoogle is missing some features of Searx in order to be as easy to deploy as possible.

Whoogle also only uses Google search results, not Bing/Quant/etc, and uses the existing Google search UI to make the transition away from Google search as unnoticeable as possible.

I'm a huge fan of Searx though and encourage anyone to use that instead if they want access to other search engines/a different UI/more configuration.

**Why does the image results page look different?**

A lot of the app currently piggybacks on Google's existing support for fetching results pages with Javascript disabled. To their credit, they've done an excellent job with styling pages, but it seems that the image results page - particularly on mobile - is a little rough. Moving forward, with enough interest, I'd like to transition to fetching the results and parsing them into a unique Whoogle-fied interface that I can style myself.

## Screenshots
#### Desktop
![Whoogle Desktop](docs/screenshot_desktop.jpg)

#### Mobile
![Whoogle Mobile](docs/screenshot_mobile.jpg)
