import json
import requests


def gen_bangs_json(bangs_file):
    # Request list
    try:
        r = requests.get('https://duckduckgo.com/bang.v255.js')
        r.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

    # Convert to json
    data = json.loads(r.text)

    # Set up a json object (with better formatting) for all available bangs
    bangs_data = {}

    for row in data:
        bang_command = '!' + row['t']
        bangs_data[bang_command] = {
            'url': row['u'].replace('{{{s}}}', '{}'),
            'suggestion': bang_command + ' (' + row['s'] + ')'
        }

    json.dump(bangs_data, open(bangs_file, 'w'))
