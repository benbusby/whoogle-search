"""
User Agent Generator for Opera-based UA strings.

This module generates realistic Opera User Agent strings based on patterns
found in working UA strings that successfully bypass Google's restrictions.
"""

import json
import os
import random
from datetime import datetime, timedelta
from typing import List, Dict


# Default fallback UA if generation fails
DEFAULT_FALLBACK_UA = "Opera/9.80 (iPad; Opera Mini/5.0.17381/503; U; eu) Presto/2.6.35 Version/11.10)"

# Opera UA Pattern Templates
OPERA_PATTERNS = [
    # Opera Mini (J2ME/MIDP)
    "Opera/9.80 (J2ME/MIDP; Opera Mini/{version}/{build}; U; {lang}) Presto/{presto} Version/{final}",
    
    # Opera Mobile (Android)
    "Opera/9.80 (Android; Linux; Opera Mobi/{build}; U; {lang}) Presto/{presto} Version/{final}",
    
    # Opera Mobile (iPhone)
    "Opera/9.80 (iPhone; Opera Mini/{version}/{build}; U; {lang}) Presto/{presto} Version/{final}",
    
    # Opera Mobile (iPad)
    "Opera/9.80 (iPad; Opera Mini/{version}/{build}; U; {lang}) Presto/{presto} Version/{final}",
]

# Randomization pools based on working UAs
OPERA_MINI_VERSIONS = [
    "4.0", "4.1.11321", "4.1.12965", "4.1.13573", "4.1.13907", "4.1.14287", 
    "4.1.15082", "4.2.13057", "4.2.13221", "4.2.13265", "4.2.13337", 
    "4.2.13400", "4.2.13918", "4.2.13943", "4.2.14320", "4.2.14409", 
    "4.2.14753", "4.2.14881", "4.2.14885", "4.2.14912", "4.2.15066",
    "4.2.15410", "4.2.16007", "4.2.16320", "4.2.18887", "4.2.19634",
    "4.2.21465", "4.2.22228", "4.2.23453", "4.2.24721", "4.3.13337",
    "4.3.24214", "4.4.26736", "4.4.29476", "4.5.33867", "4.5.40312",
    "5.0.15650", "5.0.16823", "5.0.17381", "5.0.17443", "5.0.18635",
    "5.0.18741", "5.0.19683", "5.0.19693", "5.0.20873", "5.0.22349",
    "5.1.21051", "5.1.21126", "5.1.21214", "5.1.21415", "5.1.21594",
    "5.1.21595", "5.1.22296", "5.1.22303", "5.1.22396", "5.1.22460",
    "5.1.22783", "5.1.22784", "6.0.24095", "6.0.24212", "6.0.24455",
    "6.1.25375", "6.1.25378", "6.1.25759", "6.24093", "6.24096",
    "6.24209", "6.24288", "6.5.26955", "6.5.29702", "7.0.29952",
    "7.1.32052", "7.1.32444", "7.1.32694", "7.29530", "7.5.33361",
    "7.6.35766", "9.80", "36.2.2254"
]

OPERA_MOBI_BUILDS = [
    "27", "49", "447", "498", "1181", "1209", "3730",
    "ADR-1011151731", "ADR-1012211514", "ADR-1012221546", "ADR-1012272315",
    "SYB-1103211396", "SYB-1104061449", "SYB-1107071606",
    "ADR-1111101157"
]

BUILD_NUMBERS = [
    "18.678", "18.684", "18.738", "18.794", "19.892", "19.916",
    "20.2477", "20.2479", "20.2485", "20.2489", "21.529", "22.387",
    "22.394", "22.401", "22.414", "22.453", "22.478", "23.317",
    "23.333", "23.334", "23.377", "23.390", "24.741", "24.743",
    "24.746", "24.783", "24.838", "24.871", "24.899", "25.657",
    "25.677", "25.729", "25.872", "26.1305", "27.1366", "27.1407",
    "27.1573", "28.2075", "28.2555", "28.2647", "28.2766", "29.3594",
    "30.3316", "31.1350", "35.2883", "35.5706", "37.6584", "119.132",
    "170.51", "170.54", "764", "870", "886", "490", "503"
]

PRESTO_VERSIONS = [
    "2.2.0", "2.4.15", "2.4.154.15", "2.4.18", "2.5.25", "2.5.28",
    "2.6.35", "2.7.60", "2.7.81", "2.8.119", "2.8.149", "2.8.191",
    "2.9.201", "2.12.423"
]

FINAL_VERSIONS = [
    "10.00", "10.1", "10.5", "10.54", "10.5454", "11.00", "11.10",
    "12.02", "12.16", "13.00"
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



def generate_opera_ua() -> str:
    """
    Generate a single random Opera User Agent string.
    
    Returns:
        str: A randomly generated Opera UA string
    """
    pattern = random.choice(OPERA_PATTERNS)
    
    # Determine which parameters to use based on the pattern
    params = {
        'lang': random.choice(LANGUAGES)
    }
    
    if '{version}' in pattern:
        params['version'] = random.choice(OPERA_MINI_VERSIONS)
    
    if '{build}' in pattern:
        # Use MOBI build for "Opera Mobi", regular build for "Opera Mini"
        if "Opera Mobi" in pattern:
            params['build'] = random.choice(OPERA_MOBI_BUILDS)
        else:
            params['build'] = random.choice(BUILD_NUMBERS)
    
    if '{presto}' in pattern:
        params['presto'] = random.choice(PRESTO_VERSIONS)
    
    if '{final}' in pattern:
        params['final'] = random.choice(FINAL_VERSIONS)
    
    return pattern.format(**params)


def generate_ua_pool(count: int = 10) -> List[str]:
    """
    Generate a pool of unique Opera User Agent strings.
    
    Args:
        count: Number of UA strings to generate (default: 10)
    
    Returns:
        List[str]: List of unique UA strings
    """
    ua_pool = set()
    
    # Keep generating until we have enough unique UAs
    # Add safety limit to prevent infinite loop
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


def save_ua_pool(uas: List[str], cache_path: str) -> None:
    """
    Save UA pool to cache file.
    
    Args:
        uas: List of UA strings to save
        cache_path: Path to cache file
    """
    cache_data = {
        'generated_at': datetime.now().isoformat(),
        'user_agents': uas
    }
    
    # Ensure directory exists
    cache_dir = os.path.dirname(cache_path)
    if cache_dir and not os.path.exists(cache_dir):
        os.makedirs(cache_dir, exist_ok=True)
    
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=2)


def load_custom_ua_list(file_path: str) -> List[str]:
    """
    Load custom UA list from a text file.
    
    Args:
        file_path: Path to text file containing UA strings (one per line)
    
    Returns:
        List[str]: List of UA strings, or empty list if file is invalid
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            uas = [line.strip() for line in f if line.strip()]
        
        # Validate that we have at least one UA
        if not uas:
            return []
        
        return uas
    except (FileNotFoundError, PermissionError, UnicodeDecodeError):
        return []


def load_ua_pool(cache_path: str, count: int = 10) -> List[str]:
    """
    Load UA pool from custom list file, cache, or generate new one.
    
    Priority order:
    1. Custom UA list file (if WHOOGLE_UA_LIST_FILE is set)
    2. Cached auto-generated UAs
    3. Newly generated UAs
    
    Args:
        cache_path: Path to cache file
        count: Number of UAs to generate if cache is invalid (default: 10)
    
    Returns:
        List[str]: List of UA strings
    """
    # Check for custom UA list file first (highest priority)
    custom_ua_file = os.environ.get('WHOOGLE_UA_LIST_FILE', '').strip()
    if custom_ua_file:
        custom_uas = load_custom_ua_list(custom_ua_file)
        if custom_uas:
            # Custom list loaded successfully
            return custom_uas
        else:
            # Custom file specified but invalid, log warning and fall back
            print(f"Warning: Custom UA list file '{custom_ua_file}' not found or invalid, falling back to auto-generated UAs")
    
    # Check if we should use cache
    use_cache = os.environ.get('WHOOGLE_UA_CACHE_PERSISTENT', '1') == '1'
    refresh_days = int(os.environ.get('WHOOGLE_UA_CACHE_REFRESH_DAYS', '0'))
    
    # If cache disabled, always generate new
    if not use_cache:
        uas = generate_ua_pool(count)
        save_ua_pool(uas, cache_path)
        return uas
    
    # Try to load from cache
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Check if cache is expired (if refresh_days > 0)
            if refresh_days > 0:
                generated_at = datetime.fromisoformat(cache_data['generated_at'])
                age_days = (datetime.now() - generated_at).days
                
                if age_days >= refresh_days:
                    # Cache expired, generate new
                    uas = generate_ua_pool(count)
                    save_ua_pool(uas, cache_path)
                    return uas
            
            # Cache is valid, return it
            return cache_data['user_agents']
        except (json.JSONDecodeError, KeyError, ValueError):
            # Cache file is corrupted, generate new
            pass
    
    # No valid cache, generate new
    uas = generate_ua_pool(count)
    save_ua_pool(uas, cache_path)
    return uas


def get_random_ua(ua_pool: List[str]) -> str:
    """
    Get a random UA from the pool.
    
    Args:
        ua_pool: List of UA strings
    
    Returns:
        str: Random UA string from the pool
    """
    if not ua_pool:
        # Fallback to generating one if pool is empty
        try:
            return generate_opera_ua()
        except Exception:
            # If generation fails, use default fallback
            return DEFAULT_FALLBACK_UA
    
    return random.choice(ua_pool)

