#!/usr/bin/env python3
"""
Standalone Opera User Agent String Generator

This tool generates Opera-based User Agent strings that can be used with Whoogle.
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
DEFAULT_FALLBACK_UA = "Opera/9.30 (Nintendo Wii; U; ; 3642; en)"

# Try to import from the app module if available
try:
    # Add parent directory to path to allow imports
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from app.utils.ua_generator import generate_ua_pool
    USE_APP_MODULE = True
except ImportError:
    USE_APP_MODULE = False
    # Self-contained version if app module is not available
    import random
    
    # Opera UA Pattern Templates
    OPERA_PATTERNS = [
        "Opera/9.80 (J2ME/MIDP; Opera Mini/{version}/{build}; U; {lang}) Presto/{presto} Version/{final}",
        "Opera/9.80 (Android; Linux; Opera Mobi/{build}; U; {lang}) Presto/{presto} Version/{final}",
        "Opera/9.80 (iPhone; Opera Mini/{version}/{build}; U; {lang}) Presto/{presto} Version/{final}",
        "Opera/9.80 (iPad; Opera Mini/{version}/{build}; U; {lang}) Presto/{presto} Version/{final}",
    ]
    
    OPERA_MINI_VERSIONS = [
        "4.0", "4.1.11321", "4.2.13337", "4.2.14912", "4.2.15410", "4.3.24214",
        "5.0.18741", "5.1.22296", "5.1.22783", "6.0.24095", "6.24093", "7.1.32444",
        "7.6.35766", "36.2.2254"
    ]
    
    OPERA_MOBI_BUILDS = [
        "27", "49", "447", "1209", "3730", "ADR-1012221546", "SYB-1107071606"
    ]
    
    BUILD_NUMBERS = [
        "22.387", "22.478", "23.334", "23.377", "24.746", "24.783", "25.657",
        "27.1407", "28.2647", "35.5706", "119.132", "870", "886"
    ]
    
    PRESTO_VERSIONS = [
        "2.4.15", "2.4.18", "2.5.25", "2.8.119", "2.12.423"
    ]
    
    FINAL_VERSIONS = [
        "10.00", "10.1", "10.54", "11.10", "12.16", "13.00"
    ]
    
    LANGUAGES = [
        # English variants
        "en", "en-US", "en-GB", "en-CA", "en-AU", "en-NZ", "en-ZA", "en-IN", "en-SG",
        # Western European
        "de", "de-DE", "de-AT", "de-CH",
        "fr", "fr-FR", "fr-CA", "fr-BE", "fr-CH", "fr-LU",
        "es", "es-ES", "es-MX", "es-AR", "es-CO", "es-CL", "es-PE", "es-VE", "es-LA",
        "it", "it-IT", "it-CH",
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
        "ru", "ru-RU",
        # Asian languages
        "zh", "zh-CN", "zh-TW", "zh-HK",
        "ja", "ja-JP",
        "ko", "ko-KR",
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
        "bn", "bn-IN",
        "ta", "ta-IN",
        "te", "te-IN",
        "mr", "mr-IN",
        "el", "el-GR",
        "ca", "ca-ES",
        "eu", "eu-ES"
    ]
    
    def generate_opera_ua():
        """Generate a single random Opera User Agent string."""
        pattern = random.choice(OPERA_PATTERNS)
        params = {'lang': random.choice(LANGUAGES)}
        
        if '{version}' in pattern:
            params['version'] = random.choice(OPERA_MINI_VERSIONS)
        if '{build}' in pattern:
            if "Opera Mobi" in pattern:
                params['build'] = random.choice(OPERA_MOBI_BUILDS)
            else:
                params['build'] = random.choice(BUILD_NUMBERS)
        if '{presto}' in pattern:
            params['presto'] = random.choice(PRESTO_VERSIONS)
        if '{final}' in pattern:
            params['final'] = random.choice(FINAL_VERSIONS)
        
        return pattern.format(**params)
    
    def generate_ua_pool(count=10):
        """Generate a pool of unique Opera User Agent strings."""
        ua_pool = set()
        max_attempts = count * 100
        attempts = 0
        
        try:
            while len(ua_pool) < count and attempts < max_attempts:
                ua = generate_opera_ua()
                ua_pool.add(ua)
                attempts += 1
        except Exception:
            # If generation fails entirely, return at least the default fallback
            if not ua_pool:
                return [DEFAULT_FALLBACK_UA]
        
        # If we couldn't generate enough, fill remaining with default
        result = list(ua_pool)
        while len(result) < count:
            result.append(DEFAULT_FALLBACK_UA)
        
        return result


def main():
    """Main function to generate and display UA strings."""
    # Parse command line argument
    count = 10  # Default
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
            if count < 1:
                print("Error: Count must be a positive integer", file=sys.stderr)
                sys.exit(1)
        except ValueError:
            print(f"Error: Invalid count '{sys.argv[1]}'. Must be an integer.", file=sys.stderr)
            sys.exit(1)
    
    # Show which mode we're using (to stderr so it doesn't interfere with output)
    if USE_APP_MODULE:
        print(f"# Using app.utils.ua_generator module", file=sys.stderr)
    else:
        print(f"# Using standalone generator (app module not available)", file=sys.stderr)
    
    print(f"# Generating {count} Opera User Agent strings...\n", file=sys.stderr)
    
    # Generate UAs
    uas = generate_ua_pool(count)
    
    # Display them (one per line, no numbering)
    for ua in uas:
        print(ua)
    
    # Summary to stderr so it doesn't interfere with piping
    print(f"\n# Generated {len(uas)} unique User Agent strings", file=sys.stderr)


if __name__ == '__main__':
    main()

