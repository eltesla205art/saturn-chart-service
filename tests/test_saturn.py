"""Saturn Finder: birth, any-date and cycle calculations, plus the /api/saturn layer."""
import importlib.util
import json
import os

import pytest

from saturnstudio import Person, StudioError, saturn_finder

HERE = dict(lat=28.0836, lon=-80.6081, tz="America/New_York")
A = Person("Andre", "1990-05-15", "14:30", **HERE)


@pytest.fixture(scope="module")
def at_return():
    return saturn_finder(A, at=Person("At", "2020-02-10", "12:00", **HERE))


def test_birth_saturn(at_return):
    b = at_return["birth"]
    assert b["sign"] == "Capricorn" and b["position"] == "25°14′ Capricorn"
    assert b["house"] == 5 and b["house_mode"] == "natal" and b["retrograde"] and b["dignity"] == "domicile"
    assert {"target": "Sun", "aspect": "trine"}.items() <= b["aspects"][0].items()


def test_at_date_and_ingresses(at_return):
    at = at_return["at"]
    assert at["sign"] == "Capricorn" and not at["retrograde"]
    assert at["entered_sign"] == {"date": "2017-12-20", "sign": "Capricorn", "from": "Sagittarius"}
    assert at["next_sign"]["sign"] == "Aquarius" and at["next_sign"]["date"] == "2020-03-22"


def test_cycle_events(at_return):
    ev = at_return["cycle"]["events"]
    names = [e["event"] for e in ev]
    assert names[:4] == ["Waxing Saturn square", "Saturn opposition", "Waning Saturn square", "Saturn return #1"]
    ret = ev[3]
    assert ret["dates"] == ["2020-02-02"] and 29 < ret["age"] < 30 and ret["status"] == "now"
    assert at_return["cycle"]["current"] == "Saturn return #1"
    opp = ev[1]
    assert len(opp["dates"]) == 3  # retrograde triple pass in 2004–05
    assert all(e["age"] > 5 for e in ev)  # no false "return" from the post-birth retrograde wobble


def test_reasoning_links_claims_to_reasons(at_return):
    r = at_return["reasoning"]
    topics = [x["topic"] for x in r]
    assert topics[:3] == ["birth-sign", "birth-house", "birth-retrograde"] and "cycle-now" in topics
    assert r[0]["link"] == "/signs/capricorn"
    assert all(x["claim"] and x["because"] for x in r)
    json.dumps(at_return)


def test_unknown_time_uses_solar_houses():
    x = Person.from_dict({"name": "X", "date": "2000-01-01", "time": "", "lat": 51.5, "lon": -0.12, "tz": "Europe/London"})
    r = saturn_finder(x, at=Person("At", "2026-09-27", "12:00", lat=51.5, lon=-0.12, tz="Europe/London"))
    assert r["birth"]["house_mode"] == "solar" and r["birth"]["sun_sign"] == "Capricorn"
    assert r["birth"]["sign"] == "Taurus" and r["birth"]["house"] == 5  # Capricorn → Taurus = 5th sign
    assert "Sun sign" in r["reasoning"][1]["because"]
    assert not any(a["target"] in ("Ascendant", "Medium_Coeli") for a in r["at"]["aspects"])


def test_api_layer():
    spec = importlib.util.spec_from_file_location("saturn_api", os.path.join(os.path.dirname(__file__), "..", "api", "saturn.py"))
    api = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api)
    out = api.find({"first": {"date": "1990-05-15", "time": "14:30", **HERE}, "at": {"date": "2029-03-01", "time": "12:00"},
                    "options": {"zodiac": "sidereal"}})
    assert out["settings"]["zodiac"] == "sidereal" and out["at"]["date"].startswith("2029-03-01")
    assert out["birth"]["sign"] == "Capricorn" and out["birth"]["degree"] < 3  # sidereal ≈ 1.5° Capricorn
    with pytest.raises(StudioError):
        api.find({"first": {"date": "1990-05-15", **HERE}, "options": {"house_system": "Z"}})
