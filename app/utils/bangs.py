import json
import requests
import urllib.parse as urlparse
import os
import glob

bangs_dict = {}
DDG_BANGS = 'https://duckduckgo.com/bang.js'


def load_all_bangs(ddg_bangs_file: str, ddg_bangs: dict = {}):
    """Loads all the bang files in alphabetical order

    Args:
        ddg_bangs_file: The str path to the new DDG bangs json file
        ddg_bangs: The dict of ddg bangs. If this is empty, it will load the
                   bangs from the file

    Returns:
        None

    """
    global bangs_dict
    ddg_bangs_file = os.path.normpath(ddg_bangs_file)

    if (bangs_dict and not ddg_bangs) or os.path.getsize(ddg_bangs_file) <= 4:
        return

    bangs = {}
    bangs_dir = os.path.dirname(ddg_bangs_file)
    bang_files = glob.glob(os.path.join(bangs_dir, '*.json'))

    # Normalize the paths
    bang_files = [os.path.normpath(f) for f in bang_files]

    # Move the ddg bangs file to the beginning
    bang_files = sorted([f for f in bang_files if f != ddg_bangs_file])

    if ddg_bangs:
        bangs |= ddg_bangs
    else:
        bang_files.insert(0, ddg_bangs_file)

    for i, bang_file in enumerate(bang_files):
        try:
            bangs |= json.load(open(bang_file))
        except json.decoder.JSONDecodeError:
            # Ignore decoding error only for the ddg bangs file, since this can
            # occur if file is still being written
            if i != 0:
                raise

    bangs_dict = dict(sorted(bangs.items()))


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
    print('* Finished creating ddg bangs json')
    load_all_bangs(bangs_file, bangs_data)


def suggest_bang(query: str) -> list[str]:
    """Suggests bangs for a user's query

    Args:
        query: The search query

    Returns:
        list[str]: A list of bang suggestions

    """
    global bangs_dict
    return [bangs_dict[_]['suggestion'] for _ in bangs_dict if _.startswith(query)]


def resolve_bang(query: str) -> str:
    """Transform's a user's query to a bang search, if an operator is found

    Args:
        query: The search query

    Returns:
        str: A formatted redirect for a bang search, or an empty str if there
             wasn't a match or didn't contain a bang operator

    """
    global bangs_dict

    #if ! not in query simply return (speed up processing)
    if '!' not in query:
        return ''

    split_query = query.strip().split(' ')

    # look for operator in query if one is found, list operator should be of
    # length 1, operator should not be case-sensitive here to remove it later
    operator = [
        word
        for word in split_query
        if word.lower() in bangs_dict
    ]
    if len(operator) == 1:
        # get operator
        operator = operator[0]

        # removes operator from query
        split_query.remove(operator)

        # rebuild the query string
        bang_query = ' '.join(split_query).strip()

        # Check if operator is a key in bangs and get bang if exists
        bang = bangs_dict.get(operator.lower(), None)
        if bang:
            bang_url = bang['url']

            if bang_query:
                return bang_url.replace('{}', bang_query, 1)
            else:
                parsed_url = urlparse.urlparse(bang_url)
                return f'{parsed_url.scheme}://{parsed_url.netloc}'
    return ''
