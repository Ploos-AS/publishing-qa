from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any


class HTTPJSONClient:
    def __init__(self, *, timeout: int = 120, retries: int = 3, backoff: float = 1.0):
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff

    def post(self, url: str, *, headers: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        last = None
        for attempt in range(self.retries + 1):
            req = urllib.request.Request(url, data=body, headers={**headers, "Content-Type":"application/json"}, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                last = exc
                if exc.code not in {408, 409, 429, 500, 502, 503, 504} or attempt >= self.retries:
                    raise
            except (urllib.error.URLError, TimeoutError) as exc:
                last = exc
                if attempt >= self.retries:
                    raise
            time.sleep(self.backoff * (2 ** attempt))
        raise RuntimeError(f"HTTP request failed: {last}")
