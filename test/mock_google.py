from urllib.parse import parse_qs, unquote, quote

from app.models.config import Config

DEFAULT_RESULTS = [
    ('Example Domain', 'https://example.com/{slug}', 'Example information about {term}.'),
    ('Whoogle Search', 'https://github.com/benbusby/whoogle-search', 'Private self-hosted Google proxy'),
    ('Wikipedia', 'https://en.wikipedia.org/wiki/{title}', '{title} – encyclopedia entry.'),
]


def _result_block(title, href, snippet):
    encoded_href = quote(href, safe=':/')
    return (
        f'<div class="ZINbbc xpd O9g5cc uUPGi">'
        f'<div class="kCrYT">'
        f'<a href="/url?q={encoded_href}&sa=U&ved=2ahUKE">'
        f'<h3 class="BNeawe vvjwJb AP7Wnd">{title}</h3>'
        f'<span class="CVA68e">{title}</span>'
        f'</a>'
        f'<div class="VwiC3b">{snippet}</div>'
        f'</div>'
        f'</div>'
    )


def _main_results(query, params, language='', country=''):
    term = query.lower()
    slug = query.replace(' ', '-')
    results = []

    pref_lang = ''
    pref_country = ''
    if 'preferences' in params:
        try:
            pref_data = Config(**{})._decode_preferences(params['preferences'][0])
            pref_lang = str(pref_data.get('lang_interface', '') or '').lower()
            pref_country = str(pref_data.get('country', '') or '').lower()
        except Exception:
            pref_lang = pref_country = ''
    else:
        pref_lang = pref_country = ''

    if 'wikipedia' in term:
        hl = str(params.get('hl', [''])[0] or '').lower()
        gl = str(params.get('gl', [''])[0] or '').lower()
        lr = str(params.get('lr', [''])[0] or '').lower()
        language_code = str(language or '').lower()
        country_code = str(country or '').lower()
        is_japanese = (
            hl.startswith('ja') or
            gl.startswith('jp') or
            lr.endswith('lang_ja') or
            language_code.endswith('lang_ja') or
            country_code.startswith('jp') or
            pref_lang.endswith('lang_ja') or
            pref_country.startswith('jp')
        )
        if is_japanese:
            results.append((
                'ウィキペディア',
                'https://ja.wikipedia.org/wiki/ウィキペディア',
                '日本語版ウィキペディアの記事です。'
            ))
        else:
            results.append((
                'Wikipedia',
                'https://www.wikipedia.org/wiki/Wikipedia',
                'Wikipedia is a free online encyclopedia.'
            ))

    if 'pinterest' in term:
        results.append((
            'Pinterest',
            'https://www.pinterest.com/ideas/',
            'Discover recipes, home ideas, style inspiration and other ideas.'
        ))

    if 'whoogle' in term:
        results.append((
            'Whoogle Search GitHub',
            'https://github.com/benbusby/whoogle-search',
            'Source code for Whoogle Search.'
        ))

    if 'github' in term:
        results.append((
            'GitHub',
            f'https://github.com/search?q={slug}',
            'GitHub is a development platform to host and review code.'
        ))

    for title, url, snippet in DEFAULT_RESULTS:
        formatted_url = url.format(slug=slug, term=term, title=title.replace(' ', '_'))
        formatted_snippet = snippet.format(term=query, title=title)
        results.append((title, formatted_url, formatted_snippet))

    unique = []
    seen = set()
    for entry in results:
        if entry[1] in seen:
            continue
        seen.add(entry[1])
        unique.append(entry)

    return ''.join(_result_block(*entry) for entry in unique)


def build_mock_response(raw_query, language='', country=''):
    if '&' in raw_query:
        q_part, extra = raw_query.split('&', 1)
    else:
        q_part, extra = raw_query, ''

    query = unquote(q_part)
    params = parse_qs(extra)

    results_html = _main_results(query, params, language, country)
    safe_query = query.replace('"', '')
    pagination = (
        f'<a href="/search?q={q_part}&start=10">Next</a>'
        f'<a href="/search?q={q_part}&start=20">More</a>'
    )

    return (
        '<html>'
        '<head><title>Mock Google Results</title></head>'
        '<body>'
        f'<div id="main">{results_html}</div>'
        f'<form action="/search" method="GET">'
        f'<input name="q" value="{safe_query}">'
        '</form>'
        f'<footer class="TuS8Ad">{pagination}</footer>'
        '</body>'
        '</html>'
    )
