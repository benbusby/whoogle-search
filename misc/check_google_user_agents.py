#!/usr/bin/env python3
"""
Test User Agent strings against Google to find which ones return actual search results
instead of JavaScript pages or upgrade browser messages.

Usage:
    python test_google_user_agents.py <user_agent_file> [--output <output_file>] [--query <search_query>]
"""

import argparse
import random
import sys
import time
from typing import List, Tuple
import requests

# Common search queries to cycle through for more realistic testing
DEFAULT_SEARCH_QUERIES = [
    "python programming",
    "weather today",
    "news",
    "how to cook pasta",
    "best movies 2025",
    "restaurants near me",
    "translate hello",
    "calculator",
    "time",
    "maps",
    "images",
    "videos",
    "shopping",
    "travel",
    "sports scores",
    "stock market",
    "recipes",
    "music",
    "books",
    "technology",
    "AI",
    "AI programming",
    "Why does google hate users?"
]

# Markers that indicate blocked/JS pages
BLOCK_MARKERS = [
    "unusual traffic",
    "sorry but your computer",
    "solve the captcha",
    "request looks automated",
    "g-recaptcha",
    "upgrade your browser",
    "browser is not supported",
    "please upgrade",
    "isn't supported",
    "isn\"t supported",  # With escaped quote
    "upgrade to a recent version",
    "update your browser",
    "your browser isn't supported",
]

# Markers that indicate actual search results
SUCCESS_MARKERS = [
    '<div class="g"',  # Google search result container
    '<div id="search"',  # Search results container
    '<div class="rc"',  # Result container
    'class="yuRUbf"',  # Result link container
    'class="LC20lb"',  # Result title
    '- Google Search</title>',  # Page title indicator
    'id="rso"',  # Results container
    'class="g"',  # Result class (without div tag)
]


def read_user_agents(file_path: str) -> List[str]:
    """Read user agent strings from a file, one per line."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            user_agents = [line.strip() for line in f if line.strip()]
        return user_agents
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)


def test_user_agent(user_agent: str, query: str = "test", timeout: float = 10.0) -> Tuple[bool, str]:
    """
    Test a user agent against Google search.
    
    Returns:
        Tuple of (is_working: bool, reason: str)
    """
    url = "https://www.google.com/search"
    params = {"q": query, "gbv": "1", "num": "10"}
    
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=timeout)
        
        # Check HTTP status
        if response.status_code == 429:
            # Rate limited - raise this so we can handle it specially
            raise Exception(f"Rate limited (429)")
        if response.status_code >= 500:
            return False, f"Server error ({response.status_code})"
        if response.status_code == 403:
            return False, f"Blocked ({response.status_code})"
        if response.status_code >= 400:
            return False, f"HTTP {response.status_code}"
        
        body_lower = response.text.lower()
        
        # Check for block markers
        for marker in BLOCK_MARKERS:
            if marker.lower() in body_lower:
                return False, f"Blocked: {marker}"
        
        # Check for redirect indicators first - these indicate non-working responses
        has_redirect = ("window.location" in body_lower or "location.href" in body_lower) and "google.com" not in body_lower
        if has_redirect:
            return False, "JavaScript redirect detected"
        
        # Check for noscript redirect (another indicator of JS-only page)
        if 'noscript' in body_lower and 'http-equiv="refresh"' in body_lower:
            return False, "NoScript redirect page"
        
        # Check for success markers (actual search results)
        # We need at least one strong indicator of search results
        has_results = any(marker in response.text for marker in SUCCESS_MARKERS)
        
        if has_results:
            return True, "OK - Has search results"
        else:
            # Check for very short responses (likely error pages)
            if len(response.text) < 1000:
                return False, "Response too short (likely error page)"
            # If we don't have success markers, it's not a working response
            # Even if it's substantial and doesn't have block markers, it might be a JS-only page
            return False, "No search results found"
            
    except requests.Timeout:
        return False, "Request timeout"
    except requests.HTTPError as e:
        if e.response and e.response.status_code == 429:
            # Rate limited - raise this so we can handle it specially
            raise Exception(f"Rate limited (429) - {str(e)}")
        return False, f"HTTP error: {str(e)}"
    except requests.RequestException as e:
        # Check if it's a 429 in the response
        if hasattr(e, 'response') and e.response and e.response.status_code == 429:
            raise Exception(f"Rate limited (429) - {str(e)}")
        return False, f"Request error: {str(e)}"


def main():
    parser = argparse.ArgumentParser(
        description="Test User Agent strings against Google to find working ones.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_google_user_agents.py UAs.txt
  python test_google_user_agents.py UAs.txt --output working_uas.txt
  python test_google_user_agents.py UAs.txt --query "python programming"
        """
    )
    parser.add_argument(
        "user_agent_file",
        help="Path to file containing user agent strings (one per line)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file to write working user agents (default: stdout)"
    )
    parser.add_argument(
        "--query", "-q",
        default=None,
        help="Search query to use for testing (default: cycles through random queries)"
    )
    parser.add_argument(
        "--random-queries", "-r",
        action="store_true",
        help="Use random queries from a predefined list (default: True if --query not specified)"
    )
    parser.add_argument(
        "--timeout", "-t",
        type=float,
        default=10.0,
        help="Request timeout in seconds (default: 10.0)"
    )
    parser.add_argument(
        "--delay", "-d",
        type=float,
        default=0.5,
        help="Delay between requests in seconds (default: 0.5)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed results for each user agent"
    )
    
    args = parser.parse_args()
    
    # Determine query strategy
    use_random_queries = args.random_queries or (args.query is None)
    if use_random_queries:
        search_queries = DEFAULT_SEARCH_QUERIES.copy()
        random.shuffle(search_queries)  # Shuffle for variety
        current_query_idx = 0
        query_display = f"cycling through {len(search_queries)} random queries"
    else:
        search_queries = [args.query]
        query_display = f"'{args.query}'"
    
    # Read user agents
    user_agents = read_user_agents(args.user_agent_file)
    if not user_agents:
        print("No user agents found in file.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Testing {len(user_agents)} user agents against Google...", file=sys.stderr)
    print(f"Query: {query_display}", file=sys.stderr)
    if args.output:
        print(f"Output file: {args.output} (appending results incrementally)", file=sys.stderr)
    print(file=sys.stderr)
    
    # Load existing working user agents from output file to avoid duplicates
    existing_working = set()
    if args.output:
        try:
            with open(args.output, 'r', encoding='utf-8') as f:
                existing_working = {line.strip() for line in f if line.strip()}
            if existing_working:
                print(f"Found {len(existing_working)} existing user agents in output file", file=sys.stderr)
        except FileNotFoundError:
            # File doesn't exist yet, that's fine
            pass
        except Exception as e:
            print(f"Warning: Could not read existing output file: {e}", file=sys.stderr)
    
    # Open output file for incremental writing if specified (append mode)
    output_file = None
    if args.output:
        try:
            output_file = open(args.output, 'a', encoding='utf-8')
        except Exception as e:
            print(f"Error opening output file: {e}", file=sys.stderr)
            sys.exit(1)
    
    working_agents = []
    failed_count = 0
    skipped_count = 0
    last_successful_idx = 0
    
    try:
        for idx, ua in enumerate(user_agents, 1):
            # Skip testing if this UA is already in the working file
            if args.output and ua in existing_working:
                skipped_count += 1
                if args.verbose:
                    print(f"[{idx}/{len(user_agents)}] ⊘ SKIPPED - Already in working file", file=sys.stderr)
                last_successful_idx = idx
                continue
            
            try:
                # Get the next query (cycle through if using random queries)
                if use_random_queries:
                    query = search_queries[current_query_idx % len(search_queries)]
                    current_query_idx += 1
                else:
                    query = args.query
                
                is_working, reason = test_user_agent(ua, query, args.timeout)
                
                if is_working:
                    working_agents.append(ua)
                    status = "✓"
                    # Write immediately to output file if specified (skip if duplicate)
                    if output_file:
                        if ua not in existing_working:
                            output_file.write(ua + '\n')
                            output_file.flush()  # Ensure it's written to disk
                            existing_working.add(ua)  # Track it to avoid duplicates
                        else:
                            if args.verbose:
                                print(f"[{idx}/{len(user_agents)}] {status} WORKING (duplicate, skipped) - {reason}", file=sys.stderr)
                    # Also print to stdout if no output file
                    if not args.output:
                        print(ua)
                    
                    if args.verbose:
                        print(f"[{idx}/{len(user_agents)}] {status} WORKING - {reason}", file=sys.stderr)
                else:
                    failed_count += 1
                    status = "✗"
                    if args.verbose:
                        print(f"[{idx}/{len(user_agents)}] {status} FAILED - {reason}", file=sys.stderr)
                
                last_successful_idx = idx
                
                # Progress indicator for non-verbose mode
                if not args.verbose and idx % 10 == 0:
                    print(f"Progress: {idx}/{len(user_agents)} tested ({len(working_agents)} working, {failed_count} failed)", file=sys.stderr)
                
                # Delay between requests to avoid rate limiting
                if idx < len(user_agents):
                    time.sleep(args.delay)
                    
            except KeyboardInterrupt:
                print(file=sys.stderr)
                print(f"\nInterrupted by user at index {idx}/{len(user_agents)}", file=sys.stderr)
                print(f"Last successful test: {last_successful_idx}/{len(user_agents)}", file=sys.stderr)
                break
            except Exception as e:
                # Handle unexpected errors (like network issues or rate limits)
                error_msg = str(e)
                if "429" in error_msg or "Rate limited" in error_msg:
                    print(file=sys.stderr)
                    print(f"\n⚠️  RATE LIMIT DETECTED at index {idx}/{len(user_agents)}", file=sys.stderr)
                    print(f"Last successful test: {last_successful_idx}/{len(user_agents)}", file=sys.stderr)
                    print(f"Working user agents found so far: {len(working_agents)}", file=sys.stderr)
                    if args.output:
                        print(f"Results saved to: {args.output}", file=sys.stderr)
                    print(f"\nTo resume later, you can skip the first {last_successful_idx} user agents.", file=sys.stderr)
                    raise  # Re-raise to exit the loop
                else:
                    print(f"[{idx}/{len(user_agents)}] ERROR - {error_msg}", file=sys.stderr)
                    failed_count += 1
                    last_successful_idx = idx
                    if idx < len(user_agents):
                        time.sleep(args.delay)
                    continue
    
    finally:
        # Close output file if opened
        if output_file:
            output_file.close()
    
    # Summary
    print(file=sys.stderr)
    tested_count = last_successful_idx - skipped_count
    print(f"Summary: {len(working_agents)} working, {failed_count} failed, {skipped_count} skipped out of {last_successful_idx} processed (of {len(user_agents)} total)", file=sys.stderr)
    if last_successful_idx < len(user_agents):
        print(f"Note: Processing stopped at index {last_successful_idx}. {len(user_agents) - last_successful_idx} user agents not processed.", file=sys.stderr)
        if args.output:
            print(f"Results saved to: {args.output}", file=sys.stderr)
    
    return 0 if working_agents else 1


if __name__ == "__main__":
    sys.exit(main())

