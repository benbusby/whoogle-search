#!/usr/bin/env python3
"""
Standalone Safari User Agent String Generator

This tool generates Safari 5.0 User Agent strings that can be used with Whoogle.
It can be run independently to generate and display UA strings on demand.

Usage:
    python misc/generate_uas.py [count]
    
Arguments:
    count: Number of UA strings to generate (default: 10)

Examples:
    python misc/generate_uas.py        # Generate 10 UAs
    python misc/generate_uas.py 20     # Generate 20 UAs
"""

import sys
import os

# Default fallback UA if generation fails
DEFAULT_FALLBACK_UA = "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.18.1 (KHTML, like Gecko) Version/5.0 Safari/533.16"

# Try to import from the app module if available
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from app.utils.ua_generator import generate_ua_pool
    USE_APP_MODULE = True
except ImportError:
    USE_APP_MODULE = False
    import random
    
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
        "en", "en-us", "en-US", "en-GB", "en-ca", "en-CA", "en-au", "en-AU",
        "en-NZ", "en-ZA", "en-IN", "en-SG",
        "de", "de-DE", "de-AT", "de-CH",
        "fr", "fr-fr", "fr-FR", "fr-CA", "fr-BE", "fr-CH", "fr-LU",
        "es", "es-es", "es-ES", "es-MX", "es-AR", "es-CO", "es-CL", "es-PE",
        "it", "it-it", "it-IT", "it-CH",
        "pt", "pt-PT", "pt-BR",
        "nl", "nl-NL", "nl-BE",
        "da", "da-DK",
        "sv", "sv-SE",
        "no", "no-NO", "nb", "nn",
        "fi", "fi-FI",
        "is", "is-IS",
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
        "zh", "zh-cn", "zh-CN", "zh-tw", "zh-TW", "zh-HK",
        "ja", "ja-jp", "ja-JP",
        "ko", "ko-kr", "ko-KR",
        "th", "th-TH",
        "vi", "vi-VN",
        "id", "id-ID",
        "ms", "ms-MY",
        "fil", "tl",
        "tr", "tr-TR",
        "ar", "ar-SA", "ar-AE", "ar-EG",
        "he", "he-IL",
        "fa", "fa-IR",
        "hi", "hi-IN",
        "el", "el-gr", "el-GR",
        "ca", "ca-es", "ca-ES",
        "eu", "eu-ES"
    ]
    
    def generate_safari_ua():
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
    
    def load_blacklist():
        blacklist_env = os.environ.get('WHOOGLE_UA_BLACKLIST', '')
        if not blacklist_env:
            return []
        return [term.strip().lower() for term in blacklist_env.split(',') if term.strip()]
        
    def check_blacklist(ua):
        blacklist = load_blacklist()
        if not blacklist:
            return False
        ua_lower = ua.lower()
        for term in blacklist:
            if term in ua_lower:
                return True
        return False

    def generate_ua_pool(count=10):
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


def main():
    count = 10
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
            if count < 1:
                print("Error: Count must be a positive integer", file=sys.stderr)
                sys.exit(1)
        except ValueError:
            print(f"Error: Invalid count '{sys.argv[1]}'. Must be an integer.", file=sys.stderr)
            sys.exit(1)
    
    if USE_APP_MODULE:
        print(f"# Using app.utils.ua_generator module", file=sys.stderr)
    else:
        print(f"# Using standalone generator (app module not available)", file=sys.stderr)
        
    print(f"# Generating {count} Safari 5 User Agent strings...\n", file=sys.stderr)
    
    uas = generate_ua_pool(count)
    
    for ua in uas:
        print(ua)
    
    print(f"\n# Generated {len(uas)} unique User Agent strings", file=sys.stderr)

if __name__ == '__main__':
    main()
