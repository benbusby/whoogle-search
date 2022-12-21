import json
import pathlib
import requests

lingva = 'https://lingva.ml/api/v1/en'


def format_lang(lang: str) -> str:
    # Chinese (traditional and simplified) require
    # a different format for lingva translations
    if 'zh-' in lang:
        if lang == 'zh-TW':
            return 'zh_HANT'
        return 'zh'

    # Strip lang prefix to leave only the actual
    # language code (i.e. 'en', 'fr', etc)
    return lang.replace('lang_', '')


def translate(v: str, lang: str) -> str:
    # Strip lang prefix to leave only the actual
    #language code (i.e. "es", "fr", etc)
    lang = format_lang(lang)

    lingva_req = f'{lingva}/{lang}/{v}'

    response = requests.get(lingva_req).json()

    if 'translation' in response:
        return response['translation']
    return ''


if __name__ == '__main__':
    file_path = pathlib.Path(__file__).parent.resolve()
    tl_path = 'app/static/settings/translations.json'

    with open(f'{file_path}/../{tl_path}', 'r+', encoding='utf-8') as tl_file:
        tl_data = json.load(tl_file)

        # If there are any english translations that don't
        # exist for other languages, extract them and translate
        # them now
        en_tl = tl_data['lang_en']
        for k, v in en_tl.items():
            for lang in tl_data:
                if lang == 'lang_en' or k in tl_data[lang]:
                    continue

                translation = ''
                if len(k) == 0:
                    # Special case for placeholder text that gets used
                    # for translations without any key present
                    translation = v
                else:
                    # Translate the string using lingva
                    translation = translate(v, lang)

                if len(translation) == 0:
                    print(f'! Unable to translate {lang}[{k}]')
                    continue
                print(f'{lang}[{k}] = {translation}')
                tl_data[lang][k] = translation

        # Write out updated translations json
        print(json.dumps(tl_data, indent=4, ensure_ascii=False))
