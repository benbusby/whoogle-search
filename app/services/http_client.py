import threading
import time
from typing import Any, Dict, Optional, Tuple

import httpx
from cachetools import TTLCache
import ssl
import os


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
        self._http2 = http2

        # Determine verify behavior and initialize client with fallbacks
        self._verify = self._determine_verify_setting()
        try:
            self._client = self._build_client(client_kwargs, self._verify)
        except ssl.SSLError:
            # Fallback to system trust store
            try:
                system_ctx = ssl.create_default_context()
                self._client = self._build_client(client_kwargs, system_ctx)
                self._verify = system_ctx
            except ssl.SSLError:
                insecure_fallback = os.environ.get('WHOOGLE_INSECURE_FALLBACK', '0').lower() in ('1', 'true', 't', 'yes', 'y')
                if insecure_fallback:
                    self._client = self._build_client(client_kwargs, False)
                    self._verify = False
                else:
                    raise
        self._timeout_seconds = timeout_seconds
        self._cache = TTLCache(maxsize=cache_maxsize, ttl=cache_ttl_seconds)
        self._cache_lock = threading.Lock()

    def _determine_verify_setting(self):
        """Determine SSL verification setting from environment.

        Honors:
        - WHOOGLE_CA_BUNDLE: path to CA bundle file
        - WHOOGLE_SSL_VERIFY: '0' to disable verification
        - WHOOGLE_SSL_BACKEND: 'system' to prefer system trust store
        """
        ca_bundle = os.environ.get('WHOOGLE_CA_BUNDLE', '').strip()
        if ca_bundle:
            return ca_bundle

        verify_env = os.environ.get('WHOOGLE_SSL_VERIFY', '1').lower()
        if verify_env in ('0', 'false', 'no', 'n'):
            return False

        backend = os.environ.get('WHOOGLE_SSL_BACKEND', '').lower()
        if backend == 'system':
            return ssl.create_default_context()

        return True

    def _build_client(self, client_kwargs: Dict[str, Any], verify: Any) -> httpx.Client:
        """Construct httpx.Client with proxies and provided verify setting."""
        kwargs = dict(client_kwargs)
        kwargs['verify'] = verify
        if self._proxies:
            proxy_values = list(self._proxies.values())
            single_proxy = proxy_values[0] if proxy_values and all(v == proxy_values[0] for v in proxy_values) else None
            if single_proxy:
                try:
                    return httpx.Client(proxy=single_proxy, **kwargs)
                except TypeError:
                    try:
                        return httpx.Client(proxies=self._proxies, **kwargs)
                    except TypeError:
                        mounts: Dict[str, httpx.Proxy] = {}
                        for scheme_key, url in self._proxies.items():
                            prefix = f"{scheme_key}://"
                            mounts[prefix] = httpx.Proxy(url)
                        return httpx.Client(mounts=mounts, **kwargs)
            else:
                try:
                    return httpx.Client(proxies=self._proxies, **kwargs)
                except TypeError:
                    mounts: Dict[str, httpx.Proxy] = {}
                    for scheme_key, url in self._proxies.items():
                        prefix = f"{scheme_key}://"
                        mounts[prefix] = httpx.Proxy(url)
                    return httpx.Client(mounts=mounts, **kwargs)
        else:
            return httpx.Client(**kwargs)

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
                             follow_redirects=True,
                             http2=self._http2)

        try:
            self._client = self._build_client(client_kwargs, self._verify)
        except ssl.SSLError:
            try:
                system_ctx = ssl.create_default_context()
                self._client = self._build_client(client_kwargs, system_ctx)
                self._verify = system_ctx
            except ssl.SSLError:
                insecure_fallback = os.environ.get('WHOOGLE_INSECURE_FALLBACK', '0').lower() in ('1', 'true', 't', 'yes', 'y')
                if insecure_fallback:
                    self._client = self._build_client(client_kwargs, False)
                    self._verify = False
                else:
                    raise

    def close(self) -> None:
        self._client.close()


