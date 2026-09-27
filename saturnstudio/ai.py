"""
Optional AI "deep reading" with Claude (Anthropic Messages API).

The prompt design is adapted from Asteria by Alamahant (AGPL-3.0, https://github.com/alamahant/Asteria),
which writes one system prompt per chart type. Privacy by design: the model only receives computed
positions, houses and aspects. No names, birth dates, birth times, places or coordinates are sent.

    from saturnstudio.ai import deep_reading
    text = deep_reading(chart, api_key="sk-ant-...", language="EN")

Needs an Anthropic API key (``ANTHROPIC_API_KEY``). Uses only the standard library.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Optional

from .meanings import POINTS as POINT_INFO

API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-5"
LANGUAGE_NAMES = {
    "EN": "English", "ES": "Spanish", "FR": "French", "PT": "Portuguese", "IT": "Italian", "DE": "German",
    "RU": "Russian", "TR": "Turkish", "CN": "Simplified Chinese", "HI": "Hindi",
}

VOICE = (
    "You write for Where Is Saturn?, an astrology site with a warm, grounded and quietly mystical voice, "
    "like an ancient almanac written for a modern reader. Speak directly to the reader as \"you\". "
    "Be specific: tie every claim to a placement, house or aspect in the data, and name it. "
    "Never invent placements that are not in the data. "
    "Astrology describes tendencies and invitations, never fixed fate. Do not predict death, illness, accidents, "
    "disasters, pregnancy, divorce or specific events, and do not give medical, legal, financial or mental-health advice. "
    "Do not frighten; frame difficult placements as growth. "
    "Format: Markdown with a short opening paragraph, then 4–6 sections with '## ' headings, short paragraphs and "
    "a few bullet points where useful, ending with a brief '## Practical guidance' section. "
    "About 700–900 words. Do not output JSON, XML, YAML or code blocks."
)

TASKS = {
    "natal": (
        "Interpret this natal chart. Cover personality and core drives (Sun, Moon, Rising and the chart ruler), "
        "how the mind, heart and will work (Mercury, Venus, Mars), strengths and challenges shown by the major aspects, "
        "life path themes (Midheaven, North Node), and Saturn's placement as the reader's great teacher."
    ),
    "synastry": (
        "Interpret this synastry between Person A and Person B. Explain the strengths, challenges, emotional dynamics, "
        "communication style and long-term potential of the relationship. Pay special attention to the personal planets "
        "(Sun, Moon, Venus, Mars), Saturn contacts (commitment and lessons), outer-planet contacts, and the house "
        "overlays (where each person's planets fall in the other's houses). Offer grounded ways to nurture harmony and "
        "grow together. Address both people fairly."
    ),
    "composite": (
        "Interpret this composite chart as the chart of the relationship itself, a living entity made by two people. "
        "Explain the relationship's purpose, emotional needs, communication, strengths, challenges and long-term potential, "
        "with attention to the Sun, Moon, Venus, Mars, Saturn and the angles. Address the couple as \"you two\"."
    ),
    "transit": (
        "Interpret the transits at the given moment over this natal chart. Start with an overview of the current chapter. "
        "Focus on the outer planets (Jupiter through Pluto, Saturn above all) contacting personal planets and angles, "
        "the natal houses the slow planets are moving through, and whether each aspect is applying (building) or "
        "separating (fading). Mention faster transits only briefly. End with practical guidance for this season."
    ),
    "solar_return": (
        "Interpret this Solar Return chart as a forecast of themes for the year ahead. Read the return Ascendant, "
        "the houses of the return Sun and Moon, the return Midheaven, angular planets, and the contacts between the "
        "return planets and the natal chart. Frame everything as themes and invitations for the year."
    ),
    "lunar_return": (
        "Interpret this Lunar Return chart as the emotional weather for the month ahead. Read the return Ascendant, "
        "the house of the return Moon (the month's emotional focus), the Sun's house, angular planets, and contacts "
        "with the natal chart. Keep it practical and gentle."
    ),
}


class AIError(RuntimeError):
    pass


def _pt(p: dict, with_house: bool) -> dict:
    out: dict[str, Any] = {"point": POINT_INFO.get(p["name"], (p["name"],))[0], "sign": p["sign"], "degree": round(p["degree"], 1)}
    if with_house and p.get("house"):
        out["house"] = p["house"]
    if p.get("retrograde"):
        out["retrograde"] = True
    return out


def anonymized(data: dict, max_aspects: int = 30) -> dict:
    """The chart facts the model sees: positions, houses and aspects, without any identifying details."""
    kind = data.get("kind", "natal")
    roles = list(data["subjects"])
    alias: dict[Optional[str], str] = {}
    labels = {"first": "Person A", "second": "Person B", "natal": "Natal", "transit": "Transits",
              "composite": "Composite", "return": "Return"}
    out: dict[str, Any] = {"chart_type": kind, "zodiac": data["settings"].get("zodiac"),
                           "house_system": data["settings"].get("house_system"), "charts": {}}
    for role in roles:
        blk = data["subjects"][role]
        known = blk.get("time_known", True)
        lab = labels.get(role, role)
        alias[blk.get("name")] = lab
        c: dict[str, Any] = {"points": [_pt(p, known) for p in blk.get("points", [])
                                        if known or p["name"] not in {"Ascendant", "Medium_Coeli", "Descendant", "Imum_Coeli", "Vertex", "Pars_Fortunae"}]}
        if known:
            c["house_cusps"] = [f"{h['house']}: {h['sign']} {h['degree']:.0f}°" for h in blk.get("houses", [])]
        else:
            c["note"] = "birth time unknown: houses and angles omitted"
        if blk.get("moon_phase"):
            c["moon_phase"] = blk["moon_phase"].get("name")
        if role == "transit" and blk.get("local_datetime"):
            c["moment"] = blk["local_datetime"][:10]  # the chosen transit date, not a birth date
        out["charts"][lab] = c
    asp = sorted(data.get("aspects", []), key=lambda a: a["orb"])[:max_aspects]
    out["aspects"] = [
        {
            "a": f"{alias.get(a.get('p1_owner'), '')} {POINT_INFO.get(a['p1'], (a['p1'],))[0]}".strip(),
            "aspect": a["aspect"],
            "b": f"{alias.get(a.get('p2_owner'), '')} {POINT_INFO.get(a['p2'], (a['p2'],))[0]}".strip(),
            "orb": round(a["orb"], 1),
            **({"motion": a["movement"].lower()} if a.get("movement") and a["movement"] != "Static" else {}),
        }
        for a in asp
    ]
    if kind in ("natal", "composite"):
        out["elements_percent"] = data.get("elements")
        out["modalities_percent"] = data.get("qualities")
    if data.get("relationship_score"):
        sc = data["relationship_score"]
        out["relationship_score"] = {"value": sc["value"], "label": sc["description"],
                                     "factors": [b["description"] for b in sc.get("breakdown", [])]}
    return out


def build_prompt(data: dict, language: str = "EN") -> tuple[str, str]:
    kind = data.get("kind", "natal")
    lang = LANGUAGE_NAMES.get(language.upper(), "English")
    system = f"You are an expert astrologer. {TASKS.get(kind, TASKS['natal'])} {VOICE}"
    if lang != "English":
        system += f" IMPORTANT: write your entire response in {lang}."
    facts = json.dumps(anonymized(data), ensure_ascii=False, separators=(",", ":"))
    user = f"Here is the chart data (computed with Kerykeion from the Swiss/JPL ephemeris):\n{facts}\n\nPlease write the reading."
    return system, user


def call_claude(system: str, user: str, *, api_key: Optional[str] = None, model: Optional[str] = None,
                max_tokens: int = 2200, timeout: float = 120.0) -> dict:
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise AIError("AI readings are not configured (ANTHROPIC_API_KEY is missing).")
    body = json.dumps({
        "model": model or os.environ.get("ANTHROPIC_MODEL") or DEFAULT_MODEL,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }).encode()
    req = urllib.request.Request(API_URL, data=body, method="POST", headers={
        "content-type": "application/json",
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read())
    except urllib.error.HTTPError as e:
        status = e.code
        try:  # Anthropic error bodies never contain the key; surface a short reason
            detail = str(json.loads(e.read()).get("error", {}).get("message", ""))[:200]
        except Exception:
            detail = ""
        if "credit balance" in detail.lower():
            raise AIError("AI readings are paused right now (account credit). Please try again later.") from None
        raise AIError({429: "The AI reader is busy. Please try again in a minute.",
                       529: "The AI reader is overloaded. Please try again shortly."}.get(
            status, f"The AI reader returned an error ({status}){': ' + detail if detail else ''}.")) from None
    except (urllib.error.URLError, TimeoutError):
        raise AIError("Couldn't reach the AI reader. Please try again.") from None
    text = "".join(b.get("text", "") for b in resp.get("content", []) if b.get("type") == "text").strip()
    if not text:
        raise AIError("The AI reader returned an empty reading.")
    return {"markdown": text, "model": resp.get("model"), "stop_reason": resp.get("stop_reason"),
            "usage": resp.get("usage")}


def deep_reading(chart: Any, *, api_key: Optional[str] = None, language: str = "EN",
                 model: Optional[str] = None) -> str:
    """Claude-written reading for a ChartResult (or its ``data`` dict). Returns Markdown."""
    data = chart.data if hasattr(chart, "data") else chart
    system, user = build_prompt(data, language)
    return call_claude(system, user, api_key=api_key, model=model)["markdown"]
