![Whoogle Search](docs/banner.png)

### Whoogle search light without TOR.


### G) Manual (Docker)
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

## Usage
Same as most search engines, with the exception of filtering by time range.

To filter by a range of time, append ":past <time>" to the end of your search, where <time> can be `hour`, `day`, `month`, or `year`. Example: `coronavirus updates :past hour`

## Extra Steps
### Set Whoogle as your primary search engine
*Note: If you're using a reverse proxy to run Whoogle Search, make sure the "Root URL" config option on the home page is set to your URL before going through these steps.*

Browser settings:
  - Firefox (Desktop)
    - Version 89+
      - Navigate to your app's url, right click the address bar, and select "Add Search Engine".
    - Previous versions
      - Navigate to your app's url, and click the 3 dot menu in the address bar. At the bottom, there should be an option to "Add Search Engine".
    - Once you've added the new search engine, open your Firefox Preferences menu, click "Search" in the left menu, and use the available dropdown to select "Whoogle" from the list.
    - **Note**: If your Whoogle instance uses Firefox Containers, you'll need to [go through the steps here](#using-with-firefox-containers) to get it working properly.
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
  - Chrome/Chromium-based Browsers
    - Automatic
      - Visit the home page of your Whoogle Search instance -- this may automatically add the search engine to your list of search engines. If not, you can add it manually.
    - Manual
      - Under search engines > manage search engines > add, manually enter your Whoogle instance details with a `<whoogle url>/search?q=%s` formatted search URL.
