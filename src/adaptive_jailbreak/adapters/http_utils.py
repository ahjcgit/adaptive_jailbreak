from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class HttpResponse:
    status: int
    json: dict[str, Any] | None
    text: str
    latency_s: float


def post_json(url: str, payload: dict[str, Any], timeout_s: float, headers: dict[str, str] | None = None) -> HttpResponse:
    body = json.dumps(payload).encode("utf-8")
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)

    req = urllib.request.Request(url=url, data=body, headers=req_headers, method="POST")
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read()
            latency_s = time.perf_counter() - t0
            txt = raw.decode("utf-8", errors="replace")
            try:
                js = json.loads(txt)
            except json.JSONDecodeError:
                js = None
            return HttpResponse(status=getattr(resp, "status", 200), json=js, text=txt, latency_s=latency_s)
    except urllib.error.HTTPError as e:
        raw = e.read() if hasattr(e, "read") else b""
        latency_s = time.perf_counter() - t0
        txt = raw.decode("utf-8", errors="replace")
        try:
            js = json.loads(txt)
        except json.JSONDecodeError:
            js = None
        return HttpResponse(status=int(getattr(e, "code", 0) or 0), json=js, text=txt, latency_s=latency_s)

