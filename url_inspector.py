
#!/usr/bin/env python3
# url_inspector.py – Python 3.11.9

import ssl
import json
from urllib.parse import urlparse, parse_qs

import requests
from requests.adapters import HTTPAdapter

# ─── Custom HTTPS Adapter ─────────────────────────────────────────────────────
class LegacyRenegAdapter(HTTPAdapter):
    """
    Transport adapter that enables legacy TLS renegotiation
    (OP_LEGACY_SERVER_CONNECT = 0x4 in OpenSSL 3.x).
    """
    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        # Create default SSLContext and add the legacy renegotiation flag
        ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
        ctx.options |= getattr(ssl, "OP_LEGACY_SERVER_CONNECT", 0x4)
        pool_kwargs["ssl_context"] = ctx
        return super().init_poolmanager(connections, maxsize, block=block, **pool_kwargs)

# ─── URL Parsing & HTTP Fetch ──────────────────────────────────────────────────
def parse_url_components(url: str) -> dict:
    p = urlparse(url)
    return {
        "scheme":   p.scheme,
        "host":     p.hostname,
        "port":     p.port,
        "path":     p.path,
        "query":    parse_qs(p.query),
        "fragment": p.fragment,
    }

def fetch_http_details(url: str) -> dict:
    session = requests.Session()
    # Mount the legacy TLS adapter for HTTPS
    session.mount("https://", LegacyRenegAdapter())
    try:
        resp = session.get(url, timeout=15)
    except requests.RequestException as e:
        # Return the error message in the report
        return {"error": str(e)}
    return {
        "status_code":    resp.status_code,
        "content_type":   resp.headers.get("Content-Type"),
        "headers":        dict(resp.headers),
        "payload_bytes":  len(resp.content),
        "redirect_chain": [r.url for r in resp.history] + [resp.url],
    }

# ─── Main Inspection Flow ─────────────────────────────────────────────────────
def inspect_url(url: str):
    comps = parse_url_components(url)
    http  = fetch_http_details(url)

    report = {
        "url_components": comps,
        "http_details":   http,
    }
    print(json.dumps(report, indent=2, default=str))

if __name__ == "__main__":
    # Prompt the user for the URL first
    url = input("Please enter the URL to inspect: ").strip()
    if not url:
        print("No URL provided. Exiting.")
    else:
        inspect_url(url)
