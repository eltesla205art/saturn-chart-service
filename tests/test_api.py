"""API-level tests for /api/studio (without HTTP)."""
import importlib.util
import os

import pytest

from saturnstudio import StudioError

spec = importlib.util.spec_from_file_location("studio_api", os.path.join(os.path.dirname(__file__), "..", "api", "studio.py"))
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)

A = {"date": "1990-05-15", "time": "14:30", "lat": 28.0836, "lon": -80.6081, "tz": "America/New_York", "place": "Melbourne, FL, USA"}
B = {"date": "1992-11-03", "time": "08:05", "lat": 40.7128, "lon": -74.006, "tz": "America/New_York", "place": "New York, NY, USA"}


def test_natal_bundle():
    out = api.build({"kind": "natal", "first": A, "include": ["svg", "data", "report", "context"]})
    assert "</svg>" in out["svg"] and out["data"]["kind"] == "natal"
    assert "Report" in out["report"] and out["context"].startswith("<chart_analysis")


def test_synastry_score_and_default_names():
    out = api.build({"kind": "synastry", "first": A, "second": B})
    assert out["score"]["value"] >= 0
    assert set(out["data"]["subjects"]) == {"first", "second"}
    assert out["data"]["subjects"]["first"]["name"] == "Person A"


def test_transit_inherits_natal_place():
    out = api.build({"kind": "transit", "first": A, "transit": {"date": "2026-09-25", "time": "12:00"}, "include": ["data"]})
    t = out["data"]["subjects"]["transit"]
    assert t["tz"] == "America/New_York" and t["local_datetime"].startswith("2026-09-25T12:00")


def test_options_passthrough():
    out = api.build({"kind": "natal", "first": A, "options": {"style": "classic", "theme": "classic", "language": "FR", "wheel_only": True, "points": ["Sun", "Moon", "Saturn"]}, "include": ["data"]})
    s = out["data"]["settings"]
    assert s["style"] == "classic" and s["language"] == "FR" and s["wheel_only"] is True
    assert s["points"] == ["Sun", "Moon", "Saturn"]


def test_unknown_time_defaults_to_noon():
    out = api.build({"kind": "natal", "first": {**A, "time": ""}, "include": ["data"]})
    assert "T12:00" in out["data"]["subjects"]["natal"]["local_datetime"]


@pytest.mark.parametrize("body", [
    {"kind": "horoscope", "first": A},
    {"kind": "synastry", "first": A},
    {"kind": "solar_return", "first": A, "year": 1500},
    {"kind": "natal", "first": {**A, "tz": "Nowhere/Zone"}},
])
def test_bad_requests(body):
    with pytest.raises(StudioError):
        api.build(body)
