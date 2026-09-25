"""Tests for saturnstudio. Run: python -m pytest -q"""
import json

import pytest

from saturnstudio import DEFAULT_POINTS, Person, Studio, StudioError

ANDRE = Person("Andre", "1990-05-15", "14:30", lat=28.0836, lon=-80.6081, tz="America/New_York", place="Melbourne, FL, USA")
JORDAN = Person("Jordan", "1992-11-03", "08:05", lat=40.7128, lon=-74.006, tz="America/New_York", place="New York, NY, USA")


def point(result, role, name):
    return next(p for p in result.data["subjects"][role]["points"] if p["name"] == name)


@pytest.fixture(scope="module")
def studio():
    return Studio()


def test_natal_positions_match_reference(studio):
    r = studio.natal(ANDRE)
    sat = point(r, "natal", "Saturn")
    # Swiss Ephemeris / JPL reference: Saturn 25°14′41″ Capricorn, retrograde
    assert sat["sign"] == "Capricorn"
    assert abs(sat["degree"] - 25.2448) < 0.01
    assert sat["retrograde"] is True
    sun = point(r, "natal", "Sun")
    assert sun["sign"] == "Taurus" and abs(sun["degree"] - 24.657) < 0.01
    assert len(r.data["subjects"]["natal"]["houses"]) == 12
    assert r.data["subjects"]["natal"]["houses"][0]["sign"] == "Virgo"  # Ascendant 12°26′ Virgo


def test_structured_data_is_json_ready(studio):
    r = studio.natal(ANDRE)
    parsed = json.loads(r.to_json())
    assert parsed["kind"] == "natal"
    assert set(parsed["elements"]) == {"fire", "earth", "air", "water"}
    assert sum(parsed["elements"].values()) in range(98, 103)
    assert parsed["subjects"]["natal"]["moon_phase"]["name"] == "Waning Gibbous"
    assert {p["name"] for p in parsed["subjects"]["natal"]["points"]} == set(DEFAULT_POINTS)
    assert all({"p1", "p2", "aspect", "orb"} <= set(a) for a in parsed["aspects"])


@pytest.mark.parametrize("kind", ["natal", "synastry", "transit", "composite", "solar_return", "lunar_return"])
def test_every_chart_type_renders_svg(studio, kind):
    second = JORDAN if kind in ("synastry", "composite") else None
    r = studio.build(kind, ANDRE, second, year=2026, month=9)
    assert r.svg.lstrip().startswith("<!--") or "<svg" in r.svg[:500]
    assert "</svg>" in r.svg
    assert r.data["kind"] == kind


def test_solar_return_is_on_the_birthday(studio):
    r = studio.solar_return(ANDRE, 2026)
    local = r.data["subjects"]["return"]["local_datetime"]
    assert local.startswith("2026-05-15")
    sun_return = point(r, "return", "Sun")
    sun_natal = point(r, "natal", "Sun")
    assert abs(sun_return["longitude"] - sun_natal["longitude"]) < 0.001


def test_lunar_return_moon_matches_natal_moon(studio):
    r = studio.lunar_return(ANDRE, 2026, 9)
    moon_r = point(r, "return", "Moon")["longitude"]
    moon_n = point(r, "natal", "Moon")["longitude"]
    assert abs(((moon_r - moon_n) + 180) % 360 - 180) < 0.01


def test_synastry_includes_relationship_score(studio):
    r = studio.synastry(ANDRE, JORDAN)
    assert r.score is not None and isinstance(r.score["value"], int)
    assert r.score == studio.relationship_score(ANDRE, JORDAN)
    assert {a["p1_owner"] for a in r.data["aspects"]} <= {"Andre", "Jordan"}


def test_styles_themes_languages_wheel_only_and_points():
    full = Studio().natal(ANDRE).svg
    wheel = Studio(wheel_only=True).natal(ANDRE).svg
    assert len(wheel) < len(full)
    for theme in ("dark", "classic", "black-and-white"):
        for style in ("modern", "classic"):
            assert "</svg>" in Studio(theme=theme, style=style).natal(ANDRE).svg
    es = Studio(language="ES").natal(ANDRE).svg
    assert es != full
    r = Studio(points=["Sun", "Moon", "Saturn"]).natal(ANDRE)
    assert [p["name"] for p in r.data["subjects"]["natal"]["points"]] == ["Sun", "Moon", "Saturn"]


def test_sidereal_lahiri(studio):
    r = Studio(zodiac="sidereal", ayanamsa="LAHIRI").natal(ANDRE)
    sat = point(r, "natal", "Saturn")
    assert sat["sign"] == "Capricorn" and abs(sat["degree"] - 1.519) < 0.02


def test_report_and_ai_context(studio):
    r = studio.natal(ANDRE)
    assert "Natal Chart Report" in r.report()
    ctx = r.context()
    assert ctx.startswith("<chart_analysis") and "Saturn" in ctx


@pytest.mark.parametrize(
    "kwargs",
    [dict(date="1990-02-30"), dict(time="25:00"), dict(tz="Mars/Olympus"), dict(lat=95)],
)
def test_invalid_people_raise_friendly_errors(kwargs):
    base = dict(name="X", date="1990-05-15", time="14:30", lat=28.0, lon=-80.0, tz="America/New_York")
    base.update(kwargs)
    with pytest.raises(StudioError):
        Person(**base)


def test_invalid_options():
    with pytest.raises(StudioError):
        Studio(theme="neon")
    with pytest.raises(StudioError):
        Studio(points=["Sun", "Nibiru"])
    with pytest.raises(StudioError):
        Studio(language="XX")


def test_online_lookup_requires_username(monkeypatch):
    monkeypatch.delenv("GEONAMES_USERNAME", raising=False)
    monkeypatch.delenv("KERYKEION_GEONAMES_USERNAME", raising=False)
    with pytest.raises(StudioError):
        Person.lookup("X", "1990-05-15", "14:30", city="Rome", country="IT")
