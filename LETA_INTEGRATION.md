# Mullvad Leta Backend Integration

## Overview

Whoogle Search now supports using Mullvad Leta (https://leta.mullvad.net) as an alternative search backend. This provides an additional privacy-focused search option that routes queries through Mullvad's infrastructure.

## Features

- **Backend Selection**: Users can choose between Google (default) and Mullvad Leta as the search backend
- **Privacy-Focused**: Leta is designed for privacy and doesn't track searches
- **Seamless Integration**: Results from Leta are automatically converted to Whoogle's display format
- **Automatic Tab Filtering**: Image, video, news, and map tabs are automatically hidden when using Leta (as these are not supported)

## Limitations

When using the Mullvad Leta backend, the following search types are **NOT supported**:
- Image search (`tbm=isch`)
- Video search (`tbm=vid`)
- News search (`tbm=nws`)
- Map search

Attempting to use these search types with Leta enabled will show an error message and redirect to the home page.

## Configuration

### Via Web Interface

1. Click the "Config" button on the Whoogle home page
2. Scroll down to find the "Use Mullvad Leta Backend" checkbox
3. **Leta is enabled by default** - uncheck the box to use Google instead
4. Click "Apply" to save your settings

### Via Environment Variable

Leta is **enabled by default**. To disable it and use Google instead:
```bash
WHOOGLE_CONFIG_USE_LETA=0
```

To explicitly enable it (though it's already default):
```bash
WHOOGLE_CONFIG_USE_LETA=1
```

## Implementation Details

### Files Modified

1. **app/models/config.py**
   - Added `use_leta` configuration option
   - Added to `safe_keys` list for URL parameter passing

2. **app/request.py**
   - Modified `Request.__init__()` to use Leta URL when configured
   - Added `gen_query_leta()` function to format queries for Leta's API
   - Leta uses different query parameters than Google:
     - `engine=google` (or `brave`)
     - `country=XX` (lowercase country code)
     - `language=XX` (language code without `lang_` prefix)
     - `lastUpdated=d|w|m|y` (time period filter)
     - `page=N` (pagination, 1-indexed)

3. **app/filter.py**
   - Added `convert_leta_to_whoogle()` method to parse Leta's HTML structure
   - Modified `clean()` method to detect and convert Leta results
   - Leta results use `<article>` tags with specific classes that are converted to Whoogle's format

4. **app/routes.py**
   - Added validation to prevent unsupported search types when using Leta
   - Shows user-friendly error message when attempting image/video/news/map searches with Leta

5. **app/utils/results.py**
   - Modified `get_tabs_content()` to accept `use_leta` parameter
   - Filters out non-web search tabs when Leta is enabled

6. **app/templates/index.html**
   - Added checkbox in settings panel for enabling/disabling Leta backend
   - Includes helpful tooltip explaining Leta's limitations

## Technical Details

### Query Parameter Mapping

| Google Parameter | Leta Parameter | Notes |
|-----------------|----------------|-------|
| `q=<query>` | `q=<query>` | Same format |
| `gl=<country>` | `country=<code>` | Lowercase country code |
| `lr=<lang>` | `language=<code>` | Without `lang_` prefix |
| `tbs=qdr:d` | `lastUpdated=d` | Time filters mapped |
| `start=10` | `page=2` | Converted to 1-indexed pages |
| `tbm=isch/vid/nws` | N/A | Not supported |

### Leta HTML Structure

Leta returns results in this structure:
```html
<article class="svelte-fmlk7p">
  <a href="<result-url>">
    <h3>Result Title</h3>
  </a>
  <cite>display-url.com</cite>
  <p class="result__body">Result snippet/description</p>
</article>
```

This is converted to Whoogle's expected format for consistent display.

## Testing

To test the Leta integration:

1. Enable Leta in settings
2. Perform a regular web search - should see results from Leta
3. Try to access an image/video/news tab - should see error message
4. Check pagination works correctly
5. Verify country and language filters work
6. Test time period filters (past day/week/month/year)

## Environment Variables

- `WHOOGLE_CONFIG_USE_LETA`: Set to `0` to disable Leta and use Google instead (default: `1` - Leta enabled)

## Future Enhancements

Potential improvements for future versions:
- Add Brave as an alternative engine option (Leta supports both Google and Brave)
- Implement image search support if Leta adds this capability
- Add per-query backend selection (bang-style syntax)
- Cache Leta results for improved performance

## Notes

- Leta's search results are cached on their end, so you may see "cached X days ago" messages
- Leta requires no API key or authentication
- Leta respects Tor configuration if enabled in Whoogle
- User agent settings apply to Leta requests as well

