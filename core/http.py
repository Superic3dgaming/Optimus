from __future__ import annotations
import time, random
from typing import Dict, Optional
import requests

class ResilientHTTP:
    def __init__(
        self,
        timeout_connect: float = 5.0,
        timeout_read: float = 5.0,
        default_attempts: int = 3,
        base_backoff: float = 0.4,
        max_sleep: float = 3.0,
        retry_on: Optional[tuple] = (429, 500, 502, 503, 504),
        no_retry_on: Optional[tuple] = (400, 401, 403, 404),
    ):
        self.timeout_connect = timeout_connect
        self.timeout_read = timeout_read
        self.default_attempts = default_attempts
        self.base_backoff = base_backoff
        self.max_sleep = max_sleep
        self.retry_on = retry_on or ()
        self.no_retry_on = no_retry_on or ()

    def get(self, url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, object]] = None, attempts: Optional[int] = None):
        attempts = attempts or self.default_attempts
        last_exc = None
        for i in range(attempts):
            try:
                r = requests.get(url, headers=headers, params=params, timeout=(self.timeout_connect, self.timeout_read))
                status = r.status_code
                if 200 <= status < 300:
                    return r
                if status in self.no_retry_on:
                    r.raise_for_status()
                if status not in self.retry_on:
                    r.raise_for_status()
            except requests.RequestException as e:
                last_exc = e
            if i < attempts - 1:
                sleep = self.base_backoff * (2 ** i)
                time.sleep(min(self.max_sleep, sleep + random.uniform(0, self.base_backoff)))
        if last_exc:
            raise last_exc
        raise RuntimeError("HTTP GET failed without a successful response.")
