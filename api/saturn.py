"""
Saturn Finder API — POST /api/saturn

Body (JSON):
{
  "first": {"date": "1990-05-15", "time": "14:30", "lat": 28.08, "lon": -80.61, "tz": "America/New_York"},
  "at":    {"date": "2029-03-01", "time": "12:00"},        # optional; default now. Place defaults to birthplace.
  "options": {"zodiac": "tropical", "ayanamsa": "LAHIRI", "house_system": "P"}
}
Leave "time" empty in "first" if the birth time is unknown: houses then count from the Sun sign.

Response: {birth, at, cycle, reasoning, settings, disclaimer}. See saturnstudio/saturn.py.
Privacy: used in memory for one request; nothing stored or logged. License: AGPL-3.0.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("HOME", "/tmp")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/.cache")
os.environ.setdefault("LIBEPHEMERIS_DATA_DIR", "/tmp/.libephemeris")
os.environ.setdefault("LIBEPHEMERIS_LOG_LEVEL", "ERROR")

from saturnstudio.core import AYANAMSAS, HOUSE_SYSTEMS, StudioError  # noqa: E402
from saturnstudio.saturn import saturn_finder  # noqa: E402
from saturnstudio.web import JSONHandler, person  # noqa: E402


def find(body: dict) -> dict:
    first = person(body.get("first"), "You")
    at = person(body["at"], "On this date", fallback=first) if body.get("at") else None
    opts = body.get("options") or {}
    if not isinstance(opts, dict):
        raise StudioError("options must be an object")
    zodiac = str(opts.get("zodiac", "tropical"))
    ayanamsa = str(opts.get("ayanamsa", "LAHIRI"))
    house_system = str(opts.get("house_system", "P"))
    if zodiac not in ("tropical", "sidereal"):
        raise StudioError("zodiac must be 'tropical' or 'sidereal'")
    if ayanamsa not in AYANAMSAS:
        raise StudioError(f"ayanamsa must be one of {AYANAMSAS}")
    if house_system not in HOUSE_SYSTEMS:
        raise StudioError(f"house_system must be one of {tuple(HOUSE_SYSTEMS)}")
    return saturn_finder(first, at, zodiac=zodiac, ayanamsa=ayanamsa, house_system=house_system)


class handler(JSONHandler):
    def info(self) -> dict:
        return {"service": "Where Is Saturn? Saturn Finder API",
                "returns": ["birth", "at", "cycle", "reasoning"]}

    def handle_body(self, body: dict) -> dict:
        return find(body)
