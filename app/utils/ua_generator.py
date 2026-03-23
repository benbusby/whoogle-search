"""
User Agent Generator for Safari-based UA strings.

This module generates realistic Safari 5.0 User Agent strings based on patterns
found in working UA strings that successfully bypass Google's restrictions.
"""

import json
import os
import random
from datetime import datetime
from typing import List

# Default fallback UA if generation fails
DEFAULT_FALLBACK_UA = "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.18.1 (KHTML, like Gecko) Version/5.0 Safari/533.16"

# Safari UA Pattern Templates
SAFARI_PATTERNS = [
    "Mozilla/5.0 ({system}; U; {os_ver}; {lang}) AppleWebKit/{webkit} (KHTML, like Gecko) Version/5.0 Safari/{safari}"
]

SYSTEMS_AND_VERSIONS = [
    ({"system": "X11", "os_ver": "Linux x86_64"}),
    ({"system": "Windows", "os_ver": "Windows NT 6.1"}),
    ({"system": "Windows", "os_ver": "Windows NT 6.0"}),
    ({"system": "Macintosh", "os_ver": "Intel Mac OS X 10_6_3"}),
    ({"system": "Macintosh", "os_ver": "Intel Mac OS X 10_5_8"}),
    ({"system": "Macintosh", "os_ver": "PPC Mac OS X 10_5_8"}),
    ({"system": "Macintosh", "os_ver": "PPC Mac OS X 10_4_11"}),
    ({"system": "Macintosh", "os_ver": "Intel Mac OS X 10_6_3; HTC-P715a"}),
]

WEBKIT_VERSIONS = [
    "531.2+", "533.16", "533.18.1", "534.1+"
]

SAFARI_VERSIONS = [
    "531.2+", "533.16"
]

LANGUAGES = [
    # English variants
    "en", "en-us", "en-US", "en-GB", "en-ca", "en-CA", "en-au", "en-AU",
    "en-NZ", "en-ZA", "en-IN", "en-SG",
    # Western European
    "de", "de-DE", "de-AT", "de-CH",
    "fr", "fr-fr", "fr-FR", "fr-CA", "fr-BE", "fr-CH", "fr-LU",
    "es", "es-es", "es-ES", "es-MX", "es-AR", "es-CO", "es-CL", "es-PE",
    "it", "it-it", "it-IT", "it-CH",
    "pt", "pt-PT", "pt-BR",
    "nl", "nl-NL", "nl-BE",
    # Nordic languages
    "da", "da-DK",
    "sv", "sv-SE",
    "no", "no-NO", "nb", "nn",
    "fi", "fi-FI",
    "is", "is-IS",
    # Eastern European
    "pl", "pl-PL",
    "cs", "cs-CZ",
    "sk", "sk-SK",
    "hu", "hu-HU",
    "ro", "ro-RO",
    "bg", "bg-BG",
    "hr", "hr-HR",
    "sr", "sr-RS",
    "sl", "sl-SI",
    "uk", "uk-UA",
    "ru", "ru-ru", "ru-RU",
    # Asian languages
    "zh", "zh-cn", "zh-CN", "zh-tw", "zh-TW", "zh-HK",
    "ja", "ja-jp", "ja-JP",
    "ko", "ko-kr", "ko-KR",
    "th", "th-TH",
    "vi", "vi-VN",
    "id", "id-ID",
    "ms", "ms-MY",
    "fil", "tl",
    # Middle Eastern
    "tr", "tr-TR",
    "ar", "ar-SA", "ar-AE", "ar-EG",
    "he", "he-IL",
    "fa", "fa-IR",
    # Other
    "hi", "hi-IN",
    "el", "el-gr", "el-GR",
    "ca", "ca-es", "ca-ES",
    "eu", "eu-ES"
]

def load_blacklist() -> List[str]:
    """Load blacklisted string roots from WHOOGLE_UA_BLACKLIST."""
    blacklist_env = os.environ.get('WHOOGLE_UA_BLACKLIST', '')
    if not blacklist_env:
        return []
    return [term.strip().lower() for term in blacklist_env.split(',') if term.strip()]

def check_blacklist(ua: str) -> bool:
    """Check if the given UA string contains any blacklisted term."""
    blacklist = load_blacklist()
    if not blacklist:
        return False
    ua_lower = ua.lower()
    for term in blacklist:
        if term in ua_lower:
            return True
    return False

def generate_safari_ua() -> str:
    """
    Generate a single random Safari 5.0 User Agent string.
    
    Returns:
        str: A randomly generated Safari UA string
    """
    pattern = random.choice(SAFARI_PATTERNS)
    system_info = random.choice(SYSTEMS_AND_VERSIONS)
    
    params = {
        'system': system_info['system'],
        'os_ver': system_info['os_ver'],
        'lang': random.choice(LANGUAGES),
        'webkit': random.choice(WEBKIT_VERSIONS),
        'safari': random.choice(SAFARI_VERSIONS)
    }
    
    return pattern.format(**params)

def generate_ua_pool(count: int = 10) -> List[str]:
    """
    Generate a pool of unique User Agent strings.
    
    Args:
        count: Number of UA strings to generate (default: 10)
    
    Returns:
        List[str]: List of unique UA strings
    """
    ua_pool = set()
    
    max_attempts = count * 100
    attempts = 0
    
    try:
        while len(ua_pool) < count and attempts < max_attempts:
            ua = generate_safari_ua()
            if not check_blacklist(ua):
                ua_pool.add(ua)
            attempts += 1
    except Exception:
        if not ua_pool:
            return [DEFAULT_FALLBACK_UA]
    
    result = list(ua_pool)
    while len(result) < count:
        result.append(DEFAULT_FALLBACK_UA)
    
    return result

def save_ua_pool(uas: List[str], cache_path: str) -> None:
    cache_data = {
        'generated_at': datetime.now().isoformat(),
        'user_agents': uas
    }
    
    cache_dir = os.path.dirname(cache_path)
    if cache_dir and not os.path.exists(cache_dir):
        os.makedirs(cache_dir, exist_ok=True)
    
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=2)

def load_custom_ua_list(file_path: str) -> List[str]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            uas = [line.strip() for line in f if line.strip()]
        if not uas:
            return []
        
        # Filter by blacklist
        uas = [ua for ua in uas if not check_blacklist(ua)]
        return uas
    except (FileNotFoundError, PermissionError, UnicodeDecodeError):
        return []

def load_ua_pool(cache_path: str, count: int = 10) -> List[str]:
    custom_ua_file = os.environ.get('WHOOGLE_UA_LIST_FILE', '').strip()
    if custom_ua_file:
        custom_uas = load_custom_ua_list(custom_ua_file)
        if custom_uas:
            return custom_uas
        else:
            print(f"Warning: Custom UA list file '{custom_ua_file}' not found or invalid, falling back to auto-generated UAs")

    use_cache = os.environ.get('WHOOGLE_UA_CACHE_PERSISTENT', '1') == '1'
    refresh_days = int(os.environ.get('WHOOGLE_UA_CACHE_REFRESH_DAYS', '0'))
    
    # Check if we should use cache
    if not use_cache:
        uas = generate_ua_pool(count)
        save_ua_pool(uas, cache_path)
        return uas
    
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            if refresh_days > 0:
                generated_at = datetime.fromisoformat(cache_data['generated_at'])
                age_days = (datetime.now() - generated_at).days
                
                if age_days >= refresh_days:
                    uas = generate_ua_pool(count)
                    save_ua_pool(uas, cache_path)
                    return uas
            
            # Filter cached UAs by blacklist just in case it changed
            cached_uas = cache_data['user_agents']
            filtered_uas = [ua for ua in cached_uas if not check_blacklist(ua)]
            if filtered_uas:
                return filtered_uas
            
        except (json.JSONDecodeError, KeyError, ValueError):
            pass
    
    uas = generate_ua_pool(count)
    save_ua_pool(uas, cache_path)
    return uas

def get_random_ua(ua_pool: List[str]) -> str:
    if not ua_pool:
        try:
            ua = generate_safari_ua()
            return ua if not check_blacklist(ua) else DEFAULT_FALLBACK_UA
        except Exception:
            return DEFAULT_FALLBACK_UA
    
    return random.choice(ua_pool)
