#!/usr/bin/env python3
"""
Standalone User Agent String Generator

This tool generates User Agent strings that can be used with Whoogle.
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
DEFAULT_FALLBACK_UA = "Opera/12.02 (Android 4.1; Linux; Opera Mobi/ADR-1111101157; U; en-US) Presto/2.9.201 Version/12.02"

# Try to import from the app module if available
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from app.utils.ua_generator import generate_ua_pool
    USE_APP_MODULE = True
except ImportError:
    USE_APP_MODULE = False
    import random
    
    UA_PATTERNS = [
        "HTC_Touch_3G Mozilla/4.0 (compatible; MSIE 6.0; Windows CE; IEMobile 7.11)",
        "Opera/12.02 (Android {android_ver}; Linux; Opera Mobi/ADR-1111101157; U; {lang}) Presto/2.9.201 Version/12.02"
    ]
    
    ANDROID_VERSIONS = ["4.0", "4.1", "4.2", "4.3", "4.4"]
    
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
        pattern = random.choice(UA_PATTERNS)
        params = {
            'lang': random.choice(LANGUAGES),
            'android_ver': random.choice(ANDROID_VERSIONS)
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
        
    print(f"# Generating {count} randomized User Agent strings...\n", file=sys.stderr)
    
    uas = generate_ua_pool(count)
    
    for ua in uas:
        print(ua)
    
    print(f"\n# Generated {len(uas)} unique User Agent strings", file=sys.stderr)

if __name__ == '__main__':
    main()
