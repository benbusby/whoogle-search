# Whoogle Search

[![Latest Release](https://img.shields.io/github/v/release/benbusby/whoogle-search)](https://github.com/benbusby/shoogle/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://travis-ci.com/benbusby/whoogle-search.svg?branch=master)](https://travis-ci.com/benbusby/whoogle-search)
[![codebeat badge](https://codebeat.co/badges/e96cada2-fb6f-4528-8285-7d72abd74e8d)](https://codebeat.co/projects/github-com-benbusby-shoogle-master)

Get Google search results, but without any ads, javascript, AMP links, cookies, or IP address tracking. Easily deployable in one click as a Docker app, and customizable with a single config file. Quick and simple to implement as a primary search engine replacement on both desktop and mobile.

Contents
1. [Features](#features)
2. [Dependencies](#dependencies)
3. [Install/Deploy](#install)
4. [Usage](#usage)
5. [Extra Steps](#extra-steps)
6. [FAQ](#faq)
7. [Screenshots](#screenshots)

## Features
- No ads or sponsored content
- No javascript
- No cookies
- No tracking/linking of your personal IP address
- No AMP links
- No URL tracking tags (i.e. utm=%s)
- No referrer header
- POST request search queries (when possible)
- View images at full res without site redirect (currently mobile only)
- Dark mode
- Randomly generated User Agent
- Easy to install/deploy
- Optional location-based searching (i.e. results near \<city\>)
- Optional NoJS mode to disable all Javascript in results

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
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/benbusby/whoogle-search)

*Note: Requires a (free) Heroku account*

Provides:
- Free deployment of app
- Free https url (https://\<your app name\>.herokuapp.com)
- Downtime after periods of inactivity \([solution](https://github.com/benbusby/whoogle-search#prevent-downtime-heroku-only)\)

### B) [pipx](https://github.com/pipxproject/pipx#install-pipx)
Persistent install: 

`pipx install git+https://github.com/benbusby/whoogle-search.git`

Sandboxed temporary instance: 

`pipx run git+https://github.com/benbusby/whoogle-search.git whoogle-search`

### C) pip
`pip install whoogle-search`

```bash
$ whoogle-search --help
usage: whoogle-search [-h] [--port <port number>] [--host <ip address>] [--debug]

Whoogle Search console runner

optional arguments:
  -h, --help            show this help message and exit
  --port <port number>  Specifies a port to run on (default 8888)
  --host <ip address>   Specifies the host address to use (default 127.0.0.1)
  --debug               Activates debug mode for the Flask server (default False)
```

### D) Manual
Clone the repo and run the following commands to start the app in a local-only environment:

```bash
git clone https://github.com/benbusby/whoogle-search.git
cd whoogle-search
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./whoogle-search
```

### E) Manual (Docker)
1. Ensure the Docker daemon is running, and is accessible by your user account
  - To add user permissions, you can execute `sudo usermod -aG docker yourusername`
  - Running `docker ps` should return something besides an error. If you encounter an error saying the daemon isn't running, try `sudo systemctl start docker` (Linux) or ensure the docker tool is running (Windows/macOS).
2. Clone and deploy the docker app using a method below:

#### Docker CLI
```bash
git clone https://github.com/benbusby/whoogle-search.git
cd whoogle-search
docker build --tag whooglesearch:1.0 .
docker run --publish 8888:5000 --detach --name whooglesearch whooglesearch:1.0
```

And kill with: `docker rm --force whooglesearch`

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

#### Using your own server, or alternative container deployment
There are other methods for deploying docker containers that are well outlined in [this article](https://rollout.io/blog/the-shortlist-of-docker-hosting/), but there are too many to describe set up for each here. Generally it should be about the same amount of effort as the Heroku deployment.

Depending on your preferences, you can also deploy the app yourself on your own infrastructure. This route would require a few extra steps:
  - A server (I personally recommend [Digital Ocean](https://www.digitalocean.com/pricing/) or [Linode](https://www.linode.com/pricing/), their cheapest tiers will work fine)
  - Your own URL (I suppose this is optional, but recommended)
  - SSL certificates (free through [Let's Encrypt](https://letsencrypt.org/getting-started/))
  - A bit more experience or willingness to work through issues

## Usage
Same as most search engines, with the exception of filtering by time range.

To filter by a range of time, append ":past <time>" to the end of your search, where <time> can be `hour`, `day`, `month`, or `year`. Example: `coronavirus updates :past hour`

## Extra Steps
### Set Whoogle as your primary search engine
Update browser settings:
  - Firefox (Desktop)
    - Navigate to your app's url, and click the 3 dot menu in the address bar. At the bottom, there should be an option to "Add Search Engine". Once you've clicked this, open your Firefox Preferences menu, click "Search" in the left menu, and use the available dropdown to select "Whoogle" from the list.
  - Firefox (iOS)
    - In the mobile app Settings page, tap "Search" within the "General" section. There should be an option titled "Add Search Engine" to select. It should prompt you to enter a title and search query url - use the following elements to fill out the form:
      - Title: "Whoogle"
      - URL: "https://\<your whoogle url\>/search?q=%s"
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

Since the instance is destroyed and rebuilt after inactivity, config settings will be reset once the app enters downtime. If you have configuration settings active that you'd like to keep between periods of downtime (like dark mode for example), you could instead add `*/20 7-23 * * * curl -d "dark=1" -X POST https://<your heroku app name>.herokuapp.com > /home/<username>/whoogle-refresh` to keep these settings more or less permanent, and still keep the app from entering downtime when you're using it. 

## FAQ
**What's the difference between this and [Searx](https://github.com/asciimoo/searx)?**

Whoogle is intended to only ever be deployed to private instances by individuals of any background, with as little effort as possible. Prior knowledge of/experience with the command line or deploying applications is not necessary to deploy Whoogle, which isn't the case with Searx. As a result, Whoogle is missing some features of Searx in order to be as easy to deploy as possible.

Whoogle also only uses Google search results, not Bing/Quant/etc, and uses the existing Google search UI to make the transition away from Google search as unnoticeable as possible.

I'm a huge fan of Searx though and encourage anyone to use that instead if they want access to other search engines/a different UI/more configuration.

**Why does the image results page look different?**

A lot of the app currently piggybacks on Google's existing support for fetching results pages with Javascript disabled. To their credit, they've done an excellent job with styling pages, but it seems that the image results page - particularly on mobile - is a little rough. Moving forward, with enough interest, I'd like to transition to fetching the results and parsing them into a unique Whoogle-fied interface that I can style myself.

## Screenshots
#### Desktop
![Whoogle Desktop](app/static/img/docs/screenshot_desktop.jpg)

#### Mobile
![Whoogle Mobile](app/static/img/docs/screenshot_mobile.jpg)
