# Shoogle
Get Google search results, but without any ads, javascript, or AMP links. Easily deployable via Docker, and customizable with a single config text file. Quick and simple to integrate as a primary search engine replacement on both desktop and mobile.

## Prerequisites
- Docker ([Windows](https://docs.docker.com/docker-for-windows/install/), [macOS](https://docs.docker.com/docker-for-mac/install/), [Ubuntu](https://docs.docker.com/engine/install/ubuntu/), [other Linux distros](https://docs.docker.com/engine/install/binaries/))
- [A Heroku Account](https://www.heroku.com/)
  - Optional, but recommended. Allows for free hosting of the web app.
  - Alternatively, you can host the app using a different service, or deploy it to your own server (explained below).
- [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)

## Setup
1. Ensure the Docker daemon is running, and is accessible by your user account
  - To add user permissions, you can execute `sudo usermod -aG docker yourusername`
  - Running `docker ps` should return something besides an error. If you encounter an error saying the daemon isn't running, try `sudo systemctl start docker` (Linux) or ensure the docker tool is running (Windows/macOS).
2. Clone and deploy the docker app using a method below:

#### Using Heroku (Free)
```bash
heroku login
heroku container:login
git clone https://github.com/benbusby/shoogle.git
cd shoogle
heroku create
heroku container:push web
heroku container:release web
heroku open
```

#### Using _____
TODO

## Extra Steps
- Set Shoogle as your primary search engine
  - From the main shoogle folder, run `python opensearch.py "\<your app url\>"`
  - Firefox (Desktop)
    - Navigate to your app's url, and click the 3 dot menu in the address bar. At the bottom, there should be an option to "Add Search Engine". Once you've clicked this, open your Firefox Preferences menu, click "Search" in the left menu, and use the available dropdown to select "Shoogle" from the list.
  - Firefox (Mobile)
    - In the mobile app Settings page, tap "Search" within the "General" section. There should be an option titled "Add Search Engine" to select. It should prompt you to enter a title and search query url - use the following elements to fill out the form:
      - Title: "Shoogle"
      - URL: "https://\<your shoogle url\>/search?q=%s"
