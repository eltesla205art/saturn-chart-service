"""
Chart Studio API — POST /api/studio

Body (JSON):
{
  "kind": "natal" | "synastry" | "transit" | "composite" | "solar_return" | "lunar_return",
  "first":  {"name": "A", "date": "1990-05-15", "time": "14:30", "lat": 28.08, "lon": -80.61,
             "tz": "America/New_York", "place": "Melbourne, FL, USA"},
  "second": {...},                      # synastry / composite: the other person
  "transit": {"date": "2026-09-25", "time": "12:00"},   # optional; default now, natal place
  "year": 2026, "month": 9,             # solar / lunar returns
  "options": {"style": "modern", "theme": "dark", "language": "EN", "wheel_only": false,
              "points": ["Sun", ...], "zodiac": "tropical", "ayanamsa": "LAHIRI", "house_system": "P"},
  "include": ["svg", "data", "report", "context"]
}

Response: {"svg": "...", "data": {...}, "report": "...", "context": "...", "score": {...} | null}

Privacy: data is used in memory for one request; nothing is stored or logged.
License: AGPL-3.0. Source: SOURCE_URL.
"""
from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("HOME", "/tmp")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/.cache")
os.environ.setdefault("LIBEPHEMERIS_DATA_DIR", "/tmp/.libephemeris")
os.environ.setdefault("LIBEPHEMERIS_LOG_LEVEL", "ERROR")

from saturnstudio import Person, Studio, StudioError  # noqa: E402

SOURCE_URL = os.environ.get("SOURCE_URL", "https://github.com/eltesla205art/saturn-chart-service")
ALLOWED_ORIGINS = {
    o.strip()
    for o in os.environ.get(
        "ALLOWED_ORIGINS",
        "https://whereismysaturn.com,https://www.whereismysaturn.com,http://localhost:3000,http://localhost:3100",
    ).split(",")
    if o.strip()
}
MAX_BODY = 16_384
KINDS = {"natal", "synastry", "transit", "composite", "solar_return", "lunar_return"}
INCLUDES = {"svg", "data", "report", "context"}


def person(d: object, default_name: str, fallback: Person | None = None) -> Person:
    if not isinstance(d, dict):
        raise StudioError(f"{default_name}: birth details missing")
    d = dict(d)
    if fallback is not None:  # a moment (transit) that inherits the natal place
        for k in ("lat", "lon", "tz", "place"):
            d.setdefault(k, getattr(fallback, k))
    name = str(d.get("name") or default_name)[:40]
    d["name"] = name
    return Person.from_dict(d, default_name)


def build(body: dict) -> dict:
    kind = body.get("kind", "natal")
    if kind not in KINDS:
        raise StudioError("kind must be natal, synastry, transit, composite, solar_return or lunar_return")
    opts = body.get("options") or {}
    if not isinstance(opts, dict):
        raise StudioError("options must be an object")
    studio = Studio(
        style=str(opts.get("style", "modern")),
        theme=str(opts.get("theme", "dark")),
        language=str(opts.get("language", "EN")),
        wheel_only=bool(opts.get("wheel_only", False)),
        points=opts.get("points") or None,
        zodiac=str(opts.get("zodiac", "tropical")),
        ayanamsa=str(opts.get("ayanamsa", "LAHIRI")),
        house_system=str(opts.get("house_system", "P")),
    )
    first = person(body.get("first"), "Person A")
    second = None
    if kind in ("synastry", "composite"):
        second = person(body.get("second"), "Person B")
    elif kind == "transit" and body.get("transit"):
        second = person(body.get("transit"), "Transits", fallback=first)

    year = body.get("year")
    month = body.get("month")
    if year is not None and not (isinstance(year, int) and 1800 <= year <= 2200):
        raise StudioError("year must be between 1800 and 2200")
    if month is not None and not (isinstance(month, int) and 1 <= month <= 12):
        raise StudioError("month must be 1–12")

    result = studio.build(kind, first, second, year=year, month=month)
    include = set(body.get("include") or ["svg", "data"]) & INCLUDES
    out: dict = {"kind": kind, "score": result.score, "source": SOURCE_URL}
    if "svg" in include:
        out["svg"] = result.svg
    if "data" in include:
        out["data"] = result.data
    if "report" in include:
        out["report"] = result.report()
    if "context" in include:
        out["context"] = result.context()
    return out


class handler(BaseHTTPRequestHandler):
    def _cors(self) -> None:
        origin = self.headers.get("Origin", "")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "86400")

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False, default=str).encode()
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Source-Code", SOURCE_URL)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        self._json(200, {
            "service": "Where Is Saturn? Chart Studio API",
            "kinds": sorted(KINDS),
            "includes": sorted(INCLUDES),
            "license": "AGPL-3.0",
            "source": SOURCE_URL,
            "built_on": "https://github.com/g-battaglia/kerykeion",
        })

    def do_POST(self) -> None:  # noqa: N802
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_BODY:
            return self._json(400, {"error": "Send a JSON body smaller than 16 KB."})
        try:
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise StudioError("JSON object expected")
            return self._json(200, build(body))
        except StudioError as e:
            return self._json(400, {"error": str(e)})
        except json.JSONDecodeError:
            return self._json(400, {"error": "Invalid JSON."})
        except Exception:
            return self._json(500, {"error": "The chart could not be calculated. Please check the details and try again."})

    def log_message(self, format: str, *args) -> None:
        return
