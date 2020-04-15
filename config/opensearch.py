import os
import sys

script_path = os.path.dirname(os.path.realpath(__file__))
template_path = script_path + '/../app/static/opensearch.template'
opensearch_path = script_path + '/../app/static/opensearch.xml'
replace_tag = 'SHOOGLE_URL'

if len(sys.argv) != 2:
    print('You must provide the url as an argument for this script.')
    print('Example: python opensearch.py "https://my-app-1776.herokuapps.com"')
    sys.exit(0)

app_url = sys.argv[1].rstrip('/')
opensearch_template = open(template_path, 'r').read()

with open(opensearch_path, 'w') as opensearch_xml:
    opensearch_xml.write(opensearch_template.replace(replace_tag, app_url))
    opensearch_xml.close()

print('\nDone - you may now set Shoogle as your primary search engine')
