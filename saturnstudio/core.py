"""Core of saturnstudio: people, chart building, structured output."""
from __future__ import annotations

import json
import os
import re
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Literal, Optional
from zoneinfo import ZoneInfo

# Keep caches in writable places (serverless file systems are read-only) and
# keep the ephemeris backend quiet unless asked.
os.environ.setdefault("LIBEPHEMERIS_LOG_LEVEL", "ERROR")
if not os.access(os.path.expanduser("~"), os.W_OK):
    os.environ.setdefault("XDG_CACHE_HOME", "/tmp/.cache")
    os.environ.setdefault("LIBEPHEMERIS_DATA_DIR", "/tmp/.libephemeris")

from kerykeion import (  # noqa: E402
    AstrologicalSubjectFactory,
    ChartDataFactory,
    ChartDrawer,
    CompositeSubjectFactory,
    PlanetaryReturnFactory,
    RelationshipScoreFactory,
    ReportGenerator,
    to_context,
)

warnings.filterwarnings("ignore", category=DeprecationWarning, module="kerykeion")

# ─── Options ────────────────────────────────────────────────────────────────

THEMES = ("dark", "classic", "black-and-white")
STYLES = ("modern", "classic")
LANGUAGES = ("EN", "ES", "FR", "PT", "IT", "DE", "RU", "TR", "CN", "HI")
AYANAMSAS = ("LAHIRI", "RAMAN", "KRISHNAMURTI", "FAGAN_BRADLEY")
HOUSE_SYSTEMS = {
    "P": "Placidus",
    "K": "Koch",
    "W": "Whole Sign",
    "A": "Equal",
    "R": "Regiomontanus",
    "C": "Campanus",
    "O": "Porphyry",
}
#: Every point Studio can draw. Chiron and the asteroids are approximate outside the bundled ephemeris range.
POINTS = (
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
    "True_North_Lunar_Node", "True_South_Lunar_Node", "Mean_North_Lunar_Node", "Mean_South_Lunar_Node",
    "Chiron", "Mean_Lilith", "True_Lilith", "Ceres", "Pallas", "Juno", "Vesta",
    "Pars_Fortunae", "Vertex", "Ascendant", "Medium_Coeli", "Descendant", "Imum_Coeli",
)
#: Sensible default: the ten planets, the true node and the two main angles.
DEFAULT_POINTS = (
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
    "True_North_Lunar_Node", "Ascendant", "Medium_Coeli",
)
SIGN_NAMES = {
    "Ari": "Aries", "Tau": "Taurus", "Gem": "Gemini", "Can": "Cancer", "Leo": "Leo", "Vir": "Virgo",
    "Lib": "Libra", "Sco": "Scorpio", "Sag": "Sagittarius", "Cap": "Capricorn", "Aqu": "Aquarius", "Pis": "Pisces",
}
HOUSE_KEYS = (
    "first_house", "second_house", "third_house", "fourth_house", "fifth_house", "sixth_house",
    "seventh_house", "eighth_house", "ninth_house", "tenth_house", "eleventh_house", "twelfth_house",
)
HOUSE_NUMBER = {k.split("_")[0].capitalize() + "_House": i + 1 for i, k in enumerate(HOUSE_KEYS)}

ChartKind = Literal["natal", "synastry", "transit", "composite", "solar_return", "lunar_return"]


class StudioError(ValueError):
    """Raised for invalid input. The message is safe to show to end users."""


# ─── People ─────────────────────────────────────────────────────────────────


@dataclass
class Person:
    """Birth details for one person (or one moment).

    Offline (recommended): give ``lat``, ``lon`` and an IANA ``tz``.
    Online: use :meth:`Person.lookup` with a city and country, which calls the
    GeoNames API (needs a free GeoNames username).
    """

    name: str
    date: str  # YYYY-MM-DD
    time: str = "12:00"  # HH:MM, local time at the place
    lat: Optional[float] = None
    lon: Optional[float] = None
    tz: Optional[str] = None
    place: Optional[str] = None
    country: Optional[str] = None  # ISO code, used for labels and online lookup
    online: bool = False
    geonames_username: Optional[str] = None
    time_known: bool = True

    def __post_init__(self) -> None:
        m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", str(self.date))
        if not m:
            raise StudioError(f"{self.name}: date must be YYYY-MM-DD")
        self._y, self._mo, self._d = map(int, m.groups())
        if not 1800 <= self._y <= 2200:
            raise StudioError(f"{self.name}: year must be between 1800 and 2200")
        try:
            datetime(self._y, self._mo, self._d)
        except ValueError:
            raise StudioError(f"{self.name}: that date does not exist") from None
        t = re.fullmatch(r"(\d{1,2}):(\d{2})", str(self.time))
        if not t or int(t.group(1)) > 23 or int(t.group(2)) > 59:
            raise StudioError(f"{self.name}: time must be HH:MM (24-hour)")
        self._h, self._mi = int(t.group(1)), int(t.group(2))
        if not self.online:
            if self.lat is None or self.lon is None or not self.tz:
                raise StudioError(f"{self.name}: give lat, lon and tz, or use Person.lookup(...) for online lookup")
            if not (-90 <= float(self.lat) <= 90 and -180 <= float(self.lon) <= 180):
                raise StudioError(f"{self.name}: lat/lon out of range")
            try:
                ZoneInfo(self.tz)
            except Exception:
                raise StudioError(f"{self.name}: unknown time zone {self.tz!r}") from None

    @classmethod
    def lookup(
        cls,
        name: str,
        date: str,
        time: str = "12:00",
        *,
        city: str,
        country: str,
        geonames_username: Optional[str] = None,
    ) -> "Person":
        """Online location lookup by city and ISO country code (e.g. "US", "IN") via GeoNames."""
        username = geonames_username or os.environ.get("KERYKEION_GEONAMES_USERNAME") or os.environ.get("GEONAMES_USERNAME")
        if not username:
            raise StudioError("Online lookup needs a GeoNames username (free at geonames.org) or set GEONAMES_USERNAME")
        return cls(name, date, time, place=city, country=country, online=True, geonames_username=username)

    @classmethod
    def now(cls, lat: float, lon: float, tz: str, name: str = "Now", place: Optional[str] = None) -> "Person":
        """The current moment at a place — handy for transits."""
        local = datetime.now(ZoneInfo(tz))
        return cls(name, local.strftime("%Y-%m-%d"), local.strftime("%H:%M"), lat=lat, lon=lon, tz=tz, place=place)

    @classmethod
    def from_dict(cls, d: dict, default_name: str = "Person") -> "Person":
        known = {"name", "date", "time", "lat", "lon", "tz", "place", "country", "time_known"}
        kwargs = {k: v for k, v in d.items() if k in known}
        kwargs.setdefault("name", default_name)
        if kwargs.get("time") in (None, ""):
            kwargs["time"] = "12:00"
            kwargs["time_known"] = False
        return cls(**kwargs)

    def _label(self) -> tuple[str, str]:
        label = (self.place or "Birthplace").strip()
        if self.country:
            return label, self.country
        city, _, nation = label.rpartition(", ")
        return (city, nation) if city else (label, "—")

    def subject(self, zodiac: str = "tropical", ayanamsa: str = "LAHIRI", house_system: str = "P", points: Iterable[str] = DEFAULT_POINTS):
        city, nation = self._label()
        kwargs: dict[str, Any] = dict(
            name=self.name, year=self._y, month=self._mo, day=self._d, hour=self._h, minute=self._mi,
            city=city, nation=nation, houses_system_identifier=house_system,
            active_points=list(points), suppress_geonames_warning=True,
        )
        if self.online:
            kwargs.update(online=True, geonames_username=self.geonames_username, city=self.place, nation=self.country)
        else:
            kwargs.update(online=False, lat=float(self.lat), lng=float(self.lon), tz_str=self.tz)
        if zodiac == "sidereal":
            kwargs.update(zodiac_type="Sidereal", sidereal_mode=ayanamsa)
        try:
            return AstrologicalSubjectFactory.from_birth_data(**kwargs)
        except Exception as e:  # geonames / backend errors
            raise StudioError(f"{self.name}: could not compute the chart ({e.__class__.__name__})") from e


# ─── Results ────────────────────────────────────────────────────────────────


@dataclass
class ChartResult:
    kind: str
    svg: str
    data: dict
    model: Any = field(repr=False)
    score: Optional[dict] = None

    def to_json(self, indent: Optional[int] = 2) -> str:
        return json.dumps(self.data, indent=indent, ensure_ascii=False, default=str)

    def report(self, max_aspects: Optional[int] = 20) -> str:
        return ReportGenerator(self.model, max_aspects=max_aspects).generate_report()

    def context(self) -> str:
        """Compact XML description of the chart, designed to paste into an LLM prompt."""
        return to_context(self.model)

    def save_svg(self, path: str) -> str:
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.svg)
        return path


def _point(p: Any, owner: Optional[str] = None) -> dict:
    d = p.model_dump() if hasattr(p, "model_dump") else dict(p)
    house = d.get("house")
    out = {
        "name": d.get("name"),
        "sign": SIGN_NAMES.get(d.get("sign"), d.get("sign")),
        "sign_abbr": d.get("sign"),
        "degree": round(d.get("position") or 0.0, 4),
        "longitude": round(d.get("abs_pos") or 0.0, 4),
        "element": d.get("element"),
        "quality": d.get("quality"),
        "house": HOUSE_NUMBER.get(house) if house else None,
        "retrograde": bool(d.get("retrograde")),
        "speed": round(d["speed"], 5) if d.get("speed") is not None else None,
    }
    if owner:
        out["owner"] = owner
    return out


def _subject_block(s: Any, points: Iterable[str]) -> dict:
    pts = []
    for name in points:
        obj = getattr(s, name.lower(), None)
        if obj is not None:
            pts.append(_point(obj))
    houses = []
    for i, key in enumerate(HOUSE_KEYS):
        h = getattr(s, key, None)
        if h is not None:
            houses.append({"house": i + 1, "sign": SIGN_NAMES.get(h.sign, h.sign), "degree": round(h.position, 4), "longitude": round(h.abs_pos, 4)})
    block = {
        "name": getattr(s, "name", None),
        "local_datetime": getattr(s, "iso_formatted_local_datetime", None),
        "utc_datetime": getattr(s, "iso_formatted_utc_datetime", None),
        "place": getattr(s, "city", None),
        "lat": getattr(s, "lat", None),
        "lon": getattr(s, "lng", None),
        "tz": getattr(s, "tz_str", None),
        "zodiac": getattr(s, "zodiac_type", None),
        "ayanamsa": getattr(s, "sidereal_mode", None),
        "house_system": getattr(s, "houses_system_name", None),
        "points": pts,
        "houses": houses,
    }
    lp = getattr(s, "lunar_phase", None)
    if lp is not None:
        lpd = lp.model_dump()
        block["moon_phase"] = {
            "name": lpd.get("moon_phase_name"),
            "major_phase": lpd.get("major_phase"),
            "stage": lpd.get("stage"),
            "phase_day": lpd.get("moon_phase"),
            "sun_moon_angle": round(lpd.get("degrees_between_s_m") or 0.0, 2),
            "emoji": lpd.get("moon_emoji"),
        }
    rt = getattr(s, "return_type", None)
    if rt:
        block["return_type"] = rt
    return block


def _aspects(model: Any) -> list[dict]:
    out = []
    for a in getattr(model, "aspects", []) or []:
        d = a.model_dump()
        out.append({
            "p1": d.get("p1_name"), "p1_owner": d.get("p1_owner"),
            "p2": d.get("p2_name"), "p2_owner": d.get("p2_owner"),
            "aspect": d.get("aspect"), "angle": d.get("aspect_degrees"),
            "orb": round(d.get("orbit") or 0.0, 3), "movement": d.get("aspect_movement"),
        })
    return out


def _distributions(model: Any) -> dict:
    e = model.element_distribution.model_dump()
    q = model.quality_distribution.model_dump()
    return {
        "elements": {k: e[f"{k}_percentage"] for k in ("fire", "earth", "air", "water")},
        "qualities": {k: q[f"{k}_percentage"] for k in ("cardinal", "fixed", "mutable")},
    }


def _score(model: Any) -> Optional[dict]:
    rs = getattr(model, "relationship_score", None)
    if rs is None:
        return None
    d = rs.model_dump()
    return {
        "value": d.get("score_value"),
        "description": d.get("score_description"),
        "destiny_sign": d.get("is_destiny_sign"),
        "breakdown": [
            {"rule": b.get("rule"), "description": b.get("description"), "points": b.get("points"), "details": b.get("details")}
            for b in d.get("score_breakdown") or []
        ],
    }


# ─── Studio ────────────────────────────────────────────────────────────────


class Studio:
    """Chart settings shared by every chart it draws.

    Args:
        style: "modern" (default) or "classic".
        theme: "dark" (default), "classic" or "black-and-white".
        language: chart labels — one of LANGUAGES (default "EN").
        wheel_only: draw only the wheel, without tables.
        points: which planets/points to include (default DEFAULT_POINTS).
        zodiac: "tropical" (default) or "sidereal".
        ayanamsa: sidereal offset — "LAHIRI" (default), "RAMAN", "KRISHNAMURTI", "FAGAN_BRADLEY".
        house_system: one-letter code from HOUSE_SYSTEMS (default "P", Placidus).
        title: optional custom chart title.
    """

    def __init__(
        self,
        *,
        style: str = "modern",
        theme: str = "dark",
        language: str = "EN",
        wheel_only: bool = False,
        points: Optional[Iterable[str]] = None,
        zodiac: str = "tropical",
        ayanamsa: str = "LAHIRI",
        house_system: str = "P",
        title: Optional[str] = None,
    ) -> None:
        if style not in STYLES:
            raise StudioError(f"style must be one of {STYLES}")
        if theme not in THEMES:
            raise StudioError(f"theme must be one of {THEMES}")
        language = language.upper()
        if language not in LANGUAGES:
            raise StudioError(f"language must be one of {LANGUAGES}")
        if zodiac not in ("tropical", "sidereal"):
            raise StudioError("zodiac must be 'tropical' or 'sidereal'")
        if ayanamsa not in AYANAMSAS:
            raise StudioError(f"ayanamsa must be one of {AYANAMSAS}")
        if house_system not in HOUSE_SYSTEMS:
            raise StudioError(f"house_system must be one of {tuple(HOUSE_SYSTEMS)}")
        pts = list(dict.fromkeys(points or DEFAULT_POINTS))
        bad = [p for p in pts if p not in POINTS]
        if bad:
            raise StudioError(f"unknown points: {', '.join(bad)}")
        if not any(p in pts for p in ("Sun", "Moon")):
            raise StudioError("include at least the Sun or the Moon")
        self.style, self.theme, self.language = style, theme, language
        self.wheel_only, self.points = wheel_only, pts
        self.zodiac, self.ayanamsa, self.house_system = zodiac, ayanamsa, house_system
        self.title = title

    # -- helpers
    def _subject(self, person: Person):
        return person.subject(self.zodiac, self.ayanamsa, self.house_system, self.points)

    def _draw(self, model: Any, default_title: str) -> str:
        drawer = ChartDrawer(
            model,
            theme=self.theme,
            style=self.style,
            chart_language=self.language,
            custom_title=self.title or default_title,
        )
        return drawer.generate_wheel_only_svg_string() if self.wheel_only else drawer.generate_svg_string()

    def _settings(self) -> dict:
        return {
            "style": self.style, "theme": self.theme, "language": self.language, "wheel_only": self.wheel_only,
            "points": self.points, "zodiac": self.zodiac,
            "ayanamsa": self.ayanamsa if self.zodiac == "sidereal" else None,
            "house_system": HOUSE_SYSTEMS[self.house_system],
        }

    def _result(self, kind: str, model: Any, title: str, subjects: list[tuple[str, Any]]) -> ChartResult:
        data = {
            "kind": kind,
            "settings": self._settings(),
            "subjects": {role: _subject_block(s, self.points) for role, s in subjects},
            "aspects": _aspects(model),
            **_distributions(model),
        }
        score = _score(model)
        if score:
            data["relationship_score"] = score
        return ChartResult(kind=kind, svg=self._draw(model, title), data=data, model=model, score=score)

    # -- chart types
    def natal(self, person: Person) -> ChartResult:
        s = self._subject(person)
        model = ChartDataFactory.create_natal_chart_data(s, active_points=self.points)
        return self._result("natal", model, f"{person.name} — Natal Chart", [("natal", s)])

    def synastry(self, first: Person, second: Person) -> ChartResult:
        a, b = self._subject(first), self._subject(second)
        model = ChartDataFactory.create_synastry_chart_data(a, b, active_points=self.points, include_relationship_score=True)
        return self._result("synastry", model, f"{first.name} & {second.name} — Synastry", [("first", a), ("second", b)])

    def transit(self, person: Person, when: Optional[Person] = None) -> ChartResult:
        """Transits for ``when`` (default: now, at the natal place) over the natal chart."""
        natal = self._subject(person)
        if when is None:
            if person.online:
                raise StudioError("give a transit moment when using online lookup")
            when = Person.now(float(person.lat), float(person.lon), str(person.tz), name="Transits", place=person.place)
        t = self._subject(when)
        model = ChartDataFactory.create_transit_chart_data(natal, t, active_points=self.points)
        return self._result("transit", model, f"{person.name} — Transits {when.date}", [("natal", natal), ("transit", t)])

    def composite(self, first: Person, second: Person) -> ChartResult:
        a, b = self._subject(first), self._subject(second)
        comp = CompositeSubjectFactory(a, b, chart_name=f"{first.name} & {second.name}").get_midpoint_composite_subject_model()
        model = ChartDataFactory.create_composite_chart_data(comp, active_points=self.points)
        return self._result("composite", model, f"{first.name} & {second.name} — Composite", [("composite", comp)])

    def _return(self, person: Person, kind: str, year: int, month: int, location: Optional[Person]) -> ChartResult:
        natal = self._subject(person)
        loc = location or person
        if loc.online:
            raise StudioError("returns need an offline location (lat, lon, tz)")
        city, nation = loc._label()
        factory = PlanetaryReturnFactory(
            natal, lat=float(loc.lat), lng=float(loc.lon), tz_str=loc.tz, city=city, nation=nation, online=False
        )
        rtype = "Solar" if kind == "solar_return" else "Lunar"
        ret = factory.next_return_from_date(year, month, 1, return_type=rtype)
        model = ChartDataFactory.create_return_chart_data(natal, ret, active_points=self.points)
        label = "Solar Return" if rtype == "Solar" else "Lunar Return"
        return self._result(kind, model, f"{person.name} — {label} {ret.iso_formatted_local_datetime[:10]}", [("natal", natal), ("return", ret)])

    def solar_return(self, person: Person, year: Optional[int] = None, location: Optional[Person] = None) -> ChartResult:
        """The next Solar Return on or after 1 January of ``year`` (default: this year)."""
        return self._return(person, "solar_return", year or datetime.now(timezone.utc).year, 1, location)

    def lunar_return(self, person: Person, year: Optional[int] = None, month: Optional[int] = None, location: Optional[Person] = None) -> ChartResult:
        """The next Lunar Return on or after the 1st of ``month``/``year`` (default: this month)."""
        now = datetime.now(timezone.utc)
        return self._return(person, "lunar_return", year or now.year, month or now.month, location)

    def relationship_score(self, first: Person, second: Person) -> dict:
        """Compatibility score (Ciro Discepolo method, as in Kerykeion). Higher is stronger."""
        rs = RelationshipScoreFactory(self._subject(first), self._subject(second)).get_relationship_score()
        d = rs.model_dump()
        return {
            "value": d.get("score_value"),
            "description": d.get("score_description"),
            "destiny_sign": d.get("is_destiny_sign"),
            "breakdown": [
                {"rule": b.get("rule"), "description": b.get("description"), "points": b.get("points"), "details": b.get("details")}
                for b in d.get("score_breakdown") or []
            ],
        }

    def build(self, kind: ChartKind, first: Person, second: Optional[Person] = None, **kw: Any) -> ChartResult:
        """Dispatch by name — convenient for APIs and CLIs."""
        if kind == "natal":
            return self.natal(first)
        if kind in ("synastry", "composite"):
            if second is None:
                raise StudioError(f"{kind} needs two people")
            return getattr(self, kind)(first, second)
        if kind == "transit":
            return self.transit(first, second)
        if kind == "solar_return":
            return self.solar_return(first, kw.get("year"))
        if kind == "lunar_return":
            return self.lunar_return(first, kw.get("year"), kw.get("month"))
        raise StudioError("kind must be natal, synastry, transit, composite, solar_return or lunar_return")
