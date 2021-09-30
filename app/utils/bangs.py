import json
import requests

DDG_BANGS = 'https://duckduckgo.com/bang.v255.js'


def gen_bangs_json(bangs_file: str) -> None:
    """Generates a json file from the DDG bangs list

    Args:
        bangs_file: The str path to the new DDG bangs json file

    Returns:
        None

    """
    try:
        # Request full list from DDG
        r = requests.get(DDG_BANGS)
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


def resolve_bang(query: str, bangs_dict: dict) -> str:
    """Transform's a user's query to a bang search, if an operator is found

    Args:
        query: The search query
        bangs_dict: The dict of available bang operators, with corresponding
                    format string search URLs
                    (i.e. "!w": "https://en.wikipedia.org...?search={}")

    Returns:
        str: A formatted redirect for a bang search, or an empty str if there
             wasn't a match or didn't contain a bang operator

    """
    # Ensure bang search is case insensitive
    query = query.lower()
    split_query = query.split(' ')
    for operator in bangs_dict.keys():
        if operator not in split_query:
            continue

        return bangs_dict[operator]['url'].format(
            query.replace(operator, '').strip())
    return ''
