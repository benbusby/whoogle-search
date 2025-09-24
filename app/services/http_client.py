import threading
import time
from typing import Any, Dict, Optional, Tuple

import httpx
from cachetools import TTLCache


class HttpxClient:
    """Thin wrapper around httpx.Client providing simple retries and optional TTL caching.

    The client is intended to be safe for reuse across requests. Per-request
    overrides for headers/cookies are supported.
    """

    def __init__(
            self,
            proxies: Optional[Dict[str, str]] = None,
            timeout_seconds: float = 15.0,
            cache_ttl_seconds: int = 30,
            cache_maxsize: int = 256,
            http2: bool = True) -> None:
        client_kwargs = dict(http2=http2,
                             timeout=timeout_seconds,
                             follow_redirects=True)
        # Prefer future-proof mounts when proxies are provided; fall back to proxies=
        self._proxies = proxies or {}
        if self._proxies:
            # If both schemes map to the same proxy, try the newer proxy= API first
            proxy_values = list(self._proxies.values())
            single_proxy = proxy_values[0] if proxy_values and all(v == proxy_values[0] for v in proxy_values) else None
            if single_proxy:
                try:
                    self._client = httpx.Client(proxy=single_proxy, **client_kwargs)
                except TypeError:
                    # Older httpx that doesn't support proxy=; try proxies=
                    try:
                        self._client = httpx.Client(proxies=self._proxies, **client_kwargs)
                    except TypeError:
                        mounts: Dict[str, httpx.Proxy] = {}
                        for scheme_key, url in self._proxies.items():
                            prefix = f"{scheme_key}://"
                            mounts[prefix] = httpx.Proxy(url)
                        self._client = httpx.Client(mounts=mounts, **client_kwargs)
            else:
                # Distinct proxies per scheme; use mounts fallback if needed
                try:
                    self._client = httpx.Client(proxies=self._proxies, **client_kwargs)
                except TypeError:
                    mounts: Dict[str, httpx.Proxy] = {}
                    for scheme_key, url in self._proxies.items():
                        prefix = f"{scheme_key}://"
                        mounts[prefix] = httpx.Proxy(url)
                    self._client = httpx.Client(mounts=mounts, **client_kwargs)
        else:
            self._client = httpx.Client(**client_kwargs)
        self._timeout_seconds = timeout_seconds
        self._cache = TTLCache(maxsize=cache_maxsize, ttl=cache_ttl_seconds)
        self._cache_lock = threading.Lock()

    @property
    def proxies(self) -> Dict[str, str]:
        return self._proxies

    def _cache_key(self, method: str, url: str, headers: Optional[Dict[str, str]]) -> Tuple[str, str, Tuple[Tuple[str, str], ...]]:
        normalized_headers = tuple(sorted((headers or {}).items()))
        return (method.upper(), url, normalized_headers)

    def get(self,
            url: str,
            headers: Optional[Dict[str, str]] = None,
            cookies: Optional[Dict[str, str]] = None,
            retries: int = 2,
            backoff_seconds: float = 0.5,
            use_cache: bool = False) -> httpx.Response:
        if use_cache:
            key = self._cache_key('GET', url, headers)
            with self._cache_lock:
                cached = self._cache.get(key)
            if cached is not None:
                return cached

        last_exc: Optional[Exception] = None
        attempt = 0
        while attempt <= retries:
            try:
                # Check if client is closed and recreate if needed
                if self._client.is_closed:
                    self._recreate_client()
                    
                response = self._client.get(url, headers=headers, cookies=cookies)
                if use_cache and response.status_code == 200:
                    with self._cache_lock:
                        self._cache[key] = response
                return response
            except (httpx.HTTPError, RuntimeError) as exc:
                last_exc = exc
                if "client has been closed" in str(exc).lower():
                    # Recreate client and try again
                    self._recreate_client()
                    if attempt < retries:
                        continue
                if attempt == retries:
                    raise
                time.sleep(backoff_seconds * (2 ** attempt))
                attempt += 1

        # Should not reach here
        if last_exc:
            raise last_exc
        raise httpx.HTTPError('Unknown HTTP error')

    def _recreate_client(self) -> None:
        """Recreate the HTTP client when it has been closed."""
        try:
            self._client.close()
        except Exception:
            pass  # Client might already be closed
        
        # Recreate with same configuration
        client_kwargs = dict(timeout=self._timeout_seconds,
                             follow_redirects=True)
        
        if self._proxies:
            proxy_values = list(self._proxies.values())
            single_proxy = proxy_values[0] if proxy_values and all(v == proxy_values[0] for v in proxy_values) else None
            if single_proxy:
                try:
                    self._client = httpx.Client(proxy=single_proxy, **client_kwargs)
                except TypeError:
                    try:
                        self._client = httpx.Client(proxies=self._proxies, **client_kwargs)
                    except TypeError:
                        mounts: Dict[str, httpx.Proxy] = {}
                        for scheme_key, url in self._proxies.items():
                            prefix = f"{scheme_key}://"
                            mounts[prefix] = httpx.Proxy(url)
                        self._client = httpx.Client(mounts=mounts, **client_kwargs)
            else:
                try:
                    self._client = httpx.Client(proxies=self._proxies, **client_kwargs)
                except TypeError:
                    mounts: Dict[str, httpx.Proxy] = {}
                    for scheme_key, url in self._proxies.items():
                        prefix = f"{scheme_key}://"
                        mounts[prefix] = httpx.Proxy(url)
                    self._client = httpx.Client(mounts=mounts, **client_kwargs)
        else:
            self._client = httpx.Client(**client_kwargs)

    def close(self) -> None:
        self._client.close()


