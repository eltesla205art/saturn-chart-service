"""Built-in reading, tarot correspondences and the AI deep-reading layer (no network)."""
import importlib.util
import json
import os

import pytest

from saturnstudio import Person, Studio, cards_for, interpret, to_markdown
from saturnstudio.ai import anonymized, build_prompt
from saturnstudio.interpret import house_of
from saturnstudio.tarot import decan_card

A = Person("Andre", "1990-05-15", "14:30", lat=28.0836, lon=-80.6081, tz="America/New_York", place="Melbourne, FL, USA")
B = Person("Sam", "1992-11-03", "08:05", lat=40.7128, lon=-74.006, tz="America/New_York", place="New York, NY, USA")
NO_TIME = Person.from_dict({"name": "X", "date": "2000-01-01", "time": "", "lat": 51.5, "lon": -0.12, "tz": "Europe/London"})


@pytest.fixture(scope="module")
def studio():
    return Studio()


@pytest.fixture(scope="module")
def natal(studio):
    return studio.natal(A)


def _items(reading):
    return [i for s in reading["sections"] for i in s["items"]]


# ── tarot ──
def test_tarot_golden_dawn_mapping():
    sun = cards_for("Sun", "Taurus", 24.65)
    assert [c["name"] for c in sun] == ["The Sun", "The Hierophant", "Seven of Pentacles"]
    assert sun[2]["keywords"] == "Lord of Success Unfulfilled" and sun[2]["file"] == "70"
    assert decan_card("Aries", 0.5)["name"] == "Two of Wands"
    assert decan_card("Pisces", 29.9)["name"] == "Ten of Cups"
    assert decan_card("Gemini", 15)["name"] == "Nine of Swords"
    assert cards_for("Ascendant", "Virgo", 12.4)[0]["name"] == "The Hermit"  # no planet card for angles


# ── houses ──
def test_house_of_wraps_around_aries():
    cusps = [350 + 30 * i for i in range(12)]
    cusps = [c % 360 for c in cusps]
    assert house_of(355, cusps) == 1 and house_of(5, cusps) == 1 and house_of(21, cusps) == 2 and house_of(349, cusps) == 12


# ── natal reading ──
def test_natal_reading_structure(natal):
    r = natal.interpret()
    ids = [s["id"] for s in r["sections"]]
    assert ids[:2] == ["big-three", "placements"] and "aspects" in ids and "balance" in ids and "moon-phase" in ids
    titles = [i["title"] for i in _items(r)]
    assert "Sun in Taurus" in titles and "Moon in Aquarius" in titles and "Ascendant in Virgo" in titles
    assert "Chart ruler: Mercury in Taurus" in titles
    saturn = next(i for i in _items(r) if i["title"] == "Saturn in Capricorn")
    assert saturn["link"] == "/signs/capricorn" and "5th house" in saturn["subtitle"]
    assert all(i["text"] for i in _items(r))
    json.dumps(r)  # JSON-ready


def test_markdown(natal):
    md = natal.reading_markdown()
    assert md.startswith("# Your natal chart reading") and "## The Big Three" in md and "Tarot: The Sun" in md
    assert md == to_markdown(interpret(natal.data))


def test_unknown_time_drops_houses_and_angles(studio):
    r = studio.natal(NO_TIME).interpret()
    assert r["sections"][0]["id"] == "note"
    titles = [i["title"] for i in _items(r)]
    assert not any(t.startswith(("Ascendant", "Midheaven", "Chart ruler")) for t in titles)
    assert not any("house" in (i.get("subtitle") or "") for i in _items(r))


@pytest.mark.parametrize("kind", ["synastry", "transit", "composite", "solar_return", "lunar_return"])
def test_every_kind_reads(studio, kind):
    res = studio.build(kind, A, B if kind in ("synastry", "composite") else None, year=2026, month=9)
    r = res.interpret()
    assert r["kind"] == kind and r["sections"] and all(s["items"] for s in r["sections"])
    assert len(to_markdown(r)) > 1500


def test_synastry_overlays_and_score(studio):
    r = studio.synastry(A, B).interpret()
    ids = [s["id"] for s in r["sections"]]
    assert ids[0] == "score" and "overlays" in ids
    assert any(i["title"].startswith("Andre's Sun in Sam's") for i in _items(r))


def test_transit_skips_fast_moon(studio):
    r = studio.transit(A, when=Person("T", "2026-09-25", "12:00", lat=28.0836, lon=-80.6081, tz="America/New_York")).interpret()
    active = next(s for s in r["sections"] if s["id"] == "aspects")["items"]
    assert not any(i["title"].startswith("Transiting Moon") for i in active)
    slow = next(s for s in r["sections"] if s["id"] == "slow")["items"]
    assert slow[1]["title"].startswith("Saturn") and slow[1]["link"].startswith("/signs/")


# ── AI layer (no network) ──
def test_anonymized_payload_has_no_identifying_data(studio):
    data = studio.synastry(A, B).data
    blob = json.dumps(anonymized(data))
    for leak in ("Andre", "Sam", "Melbourne", "New York", "1990", "1992", "28.08", "-80.6", "America/New_York"):
        assert leak not in blob
    assert "Person A" in blob and "relationship_score" in blob


def test_prompt_language_and_task(studio, natal):
    system, user = build_prompt(natal.data, "ES")
    assert "Spanish" in system and "natal chart" in system and "Do not predict death" in system
    assert '"chart_type":"natal"' in user


def test_interpret_endpoint_with_fake_model(monkeypatch):
    spec = importlib.util.spec_from_file_location("interp_api", os.path.join(os.path.dirname(__file__), "..", "api", "interpret.py"))
    api = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api)
    seen = {}

    def fake(system, user):
        seen["user"] = user
        return {"markdown": "## Hello\nA reading.", "model": "fake", "stop_reason": "end_turn"}

    body = {"kind": "natal", "first": {"name": "Andre", "date": "1990-05-15", "time": "14:30", "lat": 28.0836,
                                       "lon": -80.6081, "tz": "America/New_York", "place": "Melbourne, FL, USA"}}
    out = api.interpret(body, caller=fake)
    assert out["markdown"].startswith("## Hello") and not out["truncated"]
    assert "Andre" not in seen["user"] and "Melbourne" not in seen["user"]
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(api.HTTPError) as e:
        api.interpret(body)
    assert e.value.status == 503
