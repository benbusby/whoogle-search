import csv, json, sys
import requests
import collections

# Request list
try:
    r = requests.get('https://duckduckgo.com/bang.v255.js')
    r.raise_for_status()
except requests.exceptions.HTTPError as err:
    raise SystemExit(err)

# Convert to json
data = json.loads(r.text)

# Output CSV
output = csv.writer(sys.stdout)
output.writerow(['tag', 'url', 'domain', 'name'])
for row in data:
    output.writerow([row['t'], row['u'], row['d'], row['s']])
