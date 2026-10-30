"""Outbound HTTP that still works when Windows points at a SOCKS proxy."""

from __future__ import annotations

import requests

# requests crashes on socks4:// unless PySocks is installed. Direct access works here.
_PROXY_ERRORS = (
    requests.exceptions.InvalidSchema,
    requests.exceptions.ProxyError,
)


def http_call(method: str, url: str, **kwargs) -> requests.Response:
    try:
        return requests.request(method, url, **kwargs)
    except _PROXY_ERRORS:
        session = requests.Session()
        session.trust_env = False
        try:
            return session.request(method, url, **kwargs)
        finally:
            session.close()
