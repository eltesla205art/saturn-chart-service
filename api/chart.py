"""
Where Is Saturn? — birth-chart wheel service.

POST /api/chart  (JSON body)
    {
      "date": "1990-05-15",          # required, YYYY-MM-DD
      "time": "14:30",               # required, HH:MM (24h, local time at birthplace)
      "lat": 28.0836, "lon": -80.6081,  # required
      "tz": "America/New_York",      # required, IANA time zone
      "place": "Melbourne, FL, USA", # optional label printed on the chart
      "zodiac": "tropical" | "sidereal",  # optional, default tropical
      "ayanamsa": "LAHIRI" | "RAMAN" | "KRISHNAMURTI"  # optional, sidereal only
    }
    → 200 image/svg+xml

Privacy: birth data is used only to draw the chart in memory. Nothing is
stored or logged, and the request body never appears in URLs.

Built on Kerykeion (https://github.com/g-battaglia/kerykeion), AGPL-3.0.
This service is also AGPL-3.0; its complete source is at SOURCE_URL.
"""
from __future__ import annotations

import json
import os
import re
from http.server import BaseHTTPRequestHandler
from zoneinfo import ZoneInfo

# Serverless filesystems are read-only except /tmp: point every cache there
# *before* importing Kerykeion / libephemeris / skyfield.
os.environ.setdefault("HOME", "/tmp")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/.cache")
os.environ.setdefault("LIBEPHEMERIS_DATA_DIR", "/tmp/.libephemeris")
os.environ.setdefault("LIBEPHEMERIS_LOG_LEVEL", "ERROR")

from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer  # noqa: E402

SOURCE_URL = os.environ.get("SOURCE_URL", "https://github.com/eltesla205art/saturn-chart-service")
ALLOWED_ORIGINS = {
    o.strip()
    for o in os.environ.get(
        "ALLOWED_ORIGINS",
        "https://whereismysaturn.com,https://www.whereismysaturn.com,http://localhost:3000,http://localhost:3100",
    ).split(",")
    if o.strip()
}
AYANAMSAS = {"LAHIRI", "RAMAN", "KRISHNAMURTI"}
POINTS = [
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
    "True_North_Lunar_Node", "Ascendant", "Medium_Coeli",
]
MAX_BODY = 4096


class BadRequest(ValueError):
    pass


def parse(body: dict) -> dict:
    date = str(body.get("date", ""))
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", date)
    if not m:
        raise BadRequest("date must be YYYY-MM-DD")
    year, month, day = map(int, m.groups())
    if not 1800 <= year <= 2100:
        raise BadRequest("year must be between 1800 and 2100")
    t = re.fullmatch(r"(\d{1,2}):(\d{2})", str(body.get("time", "")))
    if not t:
        raise BadRequest("time must be HH:MM — a full chart needs a birth time")
    hour, minute = map(int, t.groups())
    if hour > 23 or minute > 59:
        raise BadRequest("time out of range")
    try:
        lat = float(body["lat"])
        lon = float(body["lon"])
    except (KeyError, TypeError, ValueError):
        raise BadRequest("lat and lon are required numbers") from None
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise BadRequest("lat/lon out of range")
    tz = str(body.get("tz", ""))
    try:
        ZoneInfo(tz)
    except Exception:
        raise BadRequest("tz must be an IANA time zone, e.g. America/New_York") from None
    zodiac = str(body.get("zodiac", "tropical")).lower()
    if zodiac not in {"tropical", "sidereal"}:
        raise BadRequest("zodiac must be tropical or sidereal")
    ayanamsa = str(body.get("ayanamsa", "LAHIRI")).upper()
    if ayanamsa not in AYANAMSAS:
        raise BadRequest("ayanamsa must be LAHIRI, RAMAN or KRISHNAMURTI")
    place = re.sub(r"[^\w\s,.\-()'’]", "", str(body.get("place", "")))[:80].strip() or None
    return dict(year=year, month=month, day=day, hour=hour, minute=minute, lat=lat, lon=lon, tz=tz,
                zodiac=zodiac, ayanamsa=ayanamsa, place=place)


def render(p: dict) -> str:
    # Kerykeion prints "city, nation"; split our "City, Region, Country" label accordingly.
    label = p["place"] or "Birthplace"
    city, _, nation = label.rpartition(", ")
    if not city:
        city, nation = label, "—"
    kwargs = dict(
        name="Birth Chart",
        year=p["year"], month=p["month"], day=p["day"], hour=p["hour"], minute=p["minute"],
        lat=p["lat"], lng=p["lon"], tz_str=p["tz"], city=city, nation=nation,
        online=False, active_points=POINTS, suppress_geonames_warning=True,
    )
    if p["zodiac"] == "sidereal":
        kwargs.update(zodiac_type="Sidereal", sidereal_mode=p["ayanamsa"])
    subject = AstrologicalSubjectFactory.from_birth_data(**kwargs)
    data = ChartDataFactory.create_natal_chart_data(subject, active_points=POINTS)
    title = "Your Birth Chart" + (f" · Sidereal ({p['ayanamsa'].title()})" if p["zodiac"] == "sidereal" else "")
    drawer = ChartDrawer(data, theme="dark", custom_title=title, show_degree_indicators=True)
    svg = drawer.generate_svg_string()
    credit = (
        f"<!-- Drawn by Where Is Saturn? chart service using Kerykeion (AGPL-3.0). Source: {SOURCE_URL} -->"
    )
    return credit + "\n" + svg


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
        body = json.dumps(payload).encode()
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        self._json(200, {
            "service": "Where Is Saturn? chart service",
            "usage": "POST JSON {date, time, lat, lon, tz, place?, zodiac?, ayanamsa?} to /api/chart",
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
            return self._json(400, {"error": "Send a small JSON body."})
        try:
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise BadRequest("JSON object expected")
            svg = render(parse(body)).encode()
        except BadRequest as e:
            return self._json(400, {"error": str(e)})
        except json.JSONDecodeError:
            return self._json(400, {"error": "Invalid JSON."})
        except Exception:
            # Never echo birth data back into logs or errors.
            return self._json(500, {"error": "The chart could not be drawn. Please try again."})
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "image/svg+xml; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; img-src data:")
        self.send_header("X-Source-Code", SOURCE_URL)
        self.send_header("Content-Length", str(len(svg)))
        self.end_headers()
        self.wfile.write(svg)

    def log_message(self, format: str, *args) -> None:  # silence default request logging
        return
