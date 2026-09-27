"""
Built-in chart reading: turns ChartResult.data into a structured, plain-language interpretation.

No network and no AI: the reading is assembled from the meanings library in ``meanings.py``
plus tarot correspondences from ``tarot.py`` (Golden Dawn mapping, as used by Asteria).

    reading = chart.interpret()          # JSON-ready dict: title, intro, sections → items
    print(chart.reading_markdown())       # the same reading as Markdown
"""
from __future__ import annotations

from typing import Any, Optional

from . import meanings as M
from .tarot import cards_for

BIG_THREE = ("Sun", "Moon", "Ascendant")
SKIP_IN_LIST = {"Descendant", "Imum_Coeli"}  # mirrors of the Ascendant and Midheaven
TIME_SENSITIVE = {"Ascendant", "Medium_Coeli", "Descendant", "Imum_Coeli", "Vertex", "Pars_Fortunae"}
NO_TIME_NOTE = ("The birth time is unknown, so the chart is cast for noon. The Rising sign, Midheaven and houses "
                "change every few minutes, so they are left out of this reading.")
PERSONAL = ("Sun", "Moon", "Mercury", "Venus", "Mars")
SLOW = ("Jupiter", "Saturn", "Uranus", "Neptune", "Pluto")
KIND_WEIGHT = {"luminary": 3.0, "personal": 2.2, "angle": 2.0, "social": 1.6, "outer": 1.0, "point": 0.6}
ASPECT_WEIGHT = {"conjunction": 1.3, "opposition": 1.15, "square": 1.15, "trine": 1.0, "sextile": 0.85}
TITLES = {
    "natal": "Your natal chart reading",
    "synastry": "Your synastry reading",
    "transit": "Your transit reading",
    "composite": "Your composite chart reading",
    "solar_return": "Your Solar Return reading",
    "lunar_return": "Your Lunar Return reading",
}


# ─── helpers ────────────────────────────────────────────────────────────────


def label(name: str) -> str:
    return M.POINTS.get(name, (name.replace("_", " "),))[0]


def _info(name: str) -> tuple[str, str, str, str]:
    return M.POINTS.get(name, (label(name), "this part of your chart", name.lower(), "point"))


def _points(data: dict, role: str) -> dict[str, dict]:
    return {p["name"]: p for p in data["subjects"].get(role, {}).get("points", [])}


def _known(data: dict, role: str) -> bool:
    return bool(data["subjects"].get(role, {}).get("time_known", True))


def _moon_caution(pts: dict[str, dict]) -> str:
    m = pts.get("Moon")
    if m and (m["degree"] < 7 or m["degree"] > 23):
        return (f" The Moon moves about 13° a day and sits near the edge of {m['sign']}, so with another birth time it "
                f"could fall in the neighbouring sign.")
    return ""


def _cusps(data: dict, role: str) -> list[float]:
    return [h["longitude"] for h in data["subjects"].get(role, {}).get("houses", [])]


def house_of(longitude: float, cusps: list[float]) -> Optional[int]:
    """House (1–12) that an ecliptic longitude falls in, given 12 cusp longitudes."""
    if len(cusps) != 12:
        return None
    for i in range(12):
        start, end = cusps[i], cusps[(i + 1) % 12]
        span = (end - start) % 360
        if (longitude - start) % 360 < span:
            return i + 1
    return None


def _deg(p: dict) -> str:
    d = p["degree"]
    return f"{int(d)}°{int((d % 1) * 60):02d}′ {p['sign']}"


def _house_line(house: Optional[int]) -> str:
    if not house:
        return ""
    title, area = M.HOUSES[house]
    return f" In the {M.ordinal(house)} house of {title.lower()}, it plays out through {area}."


def _item(id_: str, title: str, text: str, *, subtitle: str = "", tarot: Optional[list] = None,
          link: Optional[str] = None, tone: Optional[str] = None) -> dict:
    out: dict[str, Any] = {"id": id_, "title": title, "text": text.strip()}
    if subtitle:
        out["subtitle"] = subtitle
    if tarot:
        out["tarot"] = tarot
    if link:
        out["link"] = link
    if tone:
        out["tone"] = tone
    return out


def _section(id_: str, title: str, items: list[dict], intro: str = "") -> Optional[dict]:
    if not items:
        return None
    s: dict[str, Any] = {"id": id_, "title": title, "items": items}
    if intro:
        s["intro"] = intro
    return s


# ─── placements ─────────────────────────────────────────────────────────────


def placement_text(p: dict, house: Optional[int] = None, *, with_house: bool = True) -> str:
    name, sign = p["name"], p["sign"]
    s = M.SIGNS.get(sign)
    lab, domain, _, kind = _info(name)
    if s is None:
        return f"{lab} is in {sign}."
    house = house if house is not None else p.get("house")

    if name == "Sun":
        text = M.SUN[sign]
    elif name == "Moon":
        text = M.MOON[sign]
    elif name == "Ascendant":
        text = M.RISING[sign]
    elif "North_Lunar_Node" in name:
        text = (f"Your North Node in {sign} calls you toward {s['gift']}. Growth comes when you lean into this, "
                f"even when it feels unfamiliar.")
    elif "South_Lunar_Node" in name:
        text = (f"Your South Node in {sign} is familiar ground: {s['gift']} come easily, but beware the old pull "
                f"toward {s['edge']}.")
    elif name == "Medium_Coeli":
        text = (f"Your Midheaven in {sign} points to a calling pursued {s['style']}, and a public path built on "
                f"{s['gift']}.")
    elif kind == "angle":
        text = f"Your {lab} in {sign} shows {domain}, which works {s['style']}."
    else:
        text = (f"{lab} shows {domain}. In {sign} it works {s['style']}. Its gift is {s['gift']}, and its growth "
                f"edge is {s['edge']}.")
        if name == "Saturn":
            text += (" Saturn marks the lesson that turns into mastery with time. Every Saturn placement "
                     "rewards patience.")

    if with_house and kind != "angle":
        text += _house_line(house)
    if p.get("retrograde") and kind not in ("angle",) and "Node" not in name:
        text += (f" {lab} was retrograde, which turns its energy inward. You rethink and develop this part of life "
                 f"in your own way and on your own timetable.")
    return text


def placement_item(p: dict, *, prefix: str = "", house: Optional[int] = None, with_house: bool = True) -> dict:
    name = p["name"]
    lab = label(name)
    h = house if house is not None else p.get("house")
    kind = _info(name)[3]
    sub = _deg(p) + (f" · {M.ordinal(h)} house" if h and kind != "angle" and with_house else "") + (" · retrograde" if p.get("retrograde") and kind != "angle" else "")
    link = f"/signs/{p['sign'].lower()}" if name == "Saturn" else None
    return _item(
        f"{prefix}{name}",
        f"{lab} in {p['sign']}",
        placement_text(p, h, with_house=with_house),
        subtitle=sub,
        tarot=cards_for(name, p["sign"], p["degree"]),
        link=link,
    )


# ─── aspects ────────────────────────────────────────────────────────────────


def _aspect_rank(a: dict) -> float:
    k1 = KIND_WEIGHT.get(_info(a["p1"])[3], 0.5)
    k2 = KIND_WEIGHT.get(_info(a["p2"])[3], 0.5)
    return k1 * k2 * ASPECT_WEIGHT.get(a["aspect"], 0.6) / (a["orb"] + 0.6)


def _aspect_ok(a: dict, same_chart: bool) -> bool:
    if a["aspect"] not in M.ASPECTS:
        return False
    k1, k2 = _info(a["p1"])[3], _info(a["p2"])[3]
    if same_chart:
        if k1 == "angle" and k2 == "angle":
            return False
        if "Node" in a["p1"] and "Node" in a["p2"]:
            return False
    return True


def top_aspects(aspects: list[dict], n: int, *, same_chart: bool = True, prefer: Optional[set] = None) -> list[dict]:
    pool = [a for a in aspects if _aspect_ok(a, same_chart)]
    if prefer:
        pool.sort(key=lambda a: (a["p2"] in prefer or a["p1"] in prefer, _aspect_rank(a)), reverse=True)
    else:
        pool.sort(key=_aspect_rank, reverse=True)
    return pool[:n]


def aspect_text(a: dict, who1: str = "your", who2: str = "your") -> str:
    name, verb, template, tone = M.ASPECTS[a["aspect"]]
    _, _, s1, _ = _info(a["p1"])
    _, _, s2, _ = _info(a["p2"])
    first = f"{who1} {s1} ({label(a['p1'])})"
    body = template.format(a=first[0].upper() + first[1:], b=f"{who2} {s2} ({label(a['p2'])})")
    return body


def aspect_item(a: dict, title: str, text: str) -> dict:
    tone = M.ASPECTS[a["aspect"]][3]
    move = (a.get("movement") or "").lower()
    sub = f"{M.ASPECTS[a['aspect']][0]} · orb {a['orb']:.1f}°" + (f" · {move}" if move and move != "static" else "")
    return _item(f"{a['p1']}-{a['aspect']}-{a['p2']}-{a.get('p2_owner', '')}", title, text, subtitle=sub, tone=tone)


# ─── balance ────────────────────────────────────────────────────────────────


def balance_items(data: dict, subject: str = "your chart") -> list[dict]:
    items = []
    el = data.get("elements") or {}
    q = data.get("qualities") or {}
    if el:
        top = max(el, key=el.get)
        low = min(el, key=el.get)
        text = M.ELEMENT_STRONG[top]
        if el[low] < 12:
            text += " " + M.ELEMENT_WEAK[low]
        items.append(_item("elements", f"Element balance: {top.capitalize()} leads", text.replace("your chart", subject),
                           subtitle=" · ".join(f"{k.capitalize()} {v}%" for k, v in el.items())))
    if q:
        top = max(q, key=q.get)
        items.append(_item("qualities", f"Modality: {top.capitalize()}", M.QUALITY_STRONG[top],
                           subtitle=" · ".join(f"{k.capitalize()} {v}%" for k, v in q.items())))
    return items


def chart_ruler_item(pts: dict[str, dict]) -> Optional[dict]:
    asc = pts.get("Ascendant")
    if not asc:
        return None
    ruler = M.SIGNS[asc["sign"]]["ruler"].split(" and ")[0]
    rp = pts.get(ruler)
    if not rp:
        return None
    h = rp.get("house")
    where = f" in the {M.ordinal(h)} house of {M.HOUSES[h][0].lower()}" if h else ""
    text = (f"With {asc['sign']} rising, {ruler} rules your chart. Its placement in {rp['sign']}{where} shows "
            f"where your life force most wants to go, through {M.HOUSES[h][1] if h else _info(ruler)[1]}.")
    return _item("chart-ruler", f"Chart ruler: {ruler} in {rp['sign']}", text, subtitle=_deg(rp),
                 tarot=cards_for(ruler, rp["sign"], rp["degree"]))


# ─── chart types ────────────────────────────────────────────────────────────


def _natal_like(data: dict, role: str, composite: bool = False) -> list[Optional[dict]]:
    pts = _points(data, role)
    known = _known(data, role)
    note = None
    if not known:
        pts = {n: p for n, p in pts.items() if n not in TIME_SENSITIVE}
        note = _section("note", "About this reading", [_item("no-time", "Birth time unknown", NO_TIME_NOTE + _moon_caution(pts))])
    big = [placement_item(pts[n], with_house=known) for n in BIG_THREE if n in pts]
    ruler = chart_ruler_item(pts) if known else None
    if ruler:
        big.append(ruler)
    rest = [placement_item(p, with_house=known) for n, p in pts.items() if n not in BIG_THREE and n not in SKIP_IN_LIST]
    asp = [
        aspect_item(a, f"{label(a['p1'])} {M.ASPECTS[a['aspect']][0].lower()} {label(a['p2'])}", aspect_text(a))
        for a in top_aspects([a for a in data.get("aspects", []) if a["p1"] in pts and a["p2"] in pts], 8)
    ]
    subject = "the relationship" if composite else "your chart"
    sections = [
        note,
        _section("big-three", "The Big Three", big,
                 "Your Sun, Moon and Rising sign are the heart of the chart: who you are, what you need, and how you meet the world."
                 if not composite else "The composite Sun, Moon and Rising describe the relationship's purpose, emotional needs and public face."),
        _section("placements", "Planets and points", rest,
                 "Each planet is a part of the psyche. Its sign shows how it acts, and its house shows where in life it plays out."),
        _section("aspects", "Key aspects", asp,
                 "Aspects are the conversations between planets. These are the strongest in the chart, ranked by closeness and importance."),
        _section("balance", "Elements and modalities", balance_items(data, subject)),
    ]
    mp = data["subjects"].get(role, {}).get("moon_phase")
    if mp and mp.get("name") in M.MOON_PHASE and not composite:
        sections.append(_section("moon-phase", "Your birth Moon phase", [
            _item("moon-phase", f"{mp.get('emoji', '')} {mp['name']}".strip(), M.MOON_PHASE[mp["name"]],
                  subtitle=f"Sun–Moon angle {mp.get('sun_moon_angle', 0):.0f}°")
        ]))
    return sections


def _synastry(data: dict) -> list[Optional[dict]]:
    a_blk, b_blk = data["subjects"]["first"], data["subjects"]["second"]
    a_name, b_name = a_blk.get("name") or "Person A", b_blk.get("name") or "Person B"
    sections: list[Optional[dict]] = []

    sc = data.get("relationship_score")
    if sc:
        lines = [f"+{b['points']} {b['description']}" for b in sc.get("breakdown", [])[:8]]
        text = (f"This pairing scores {sc['value']} ({sc['description']}) on Ciro Discepolo's synastry scale. "
                "The score counts classic bonds between Suns, Moons and Ascendants. It is a conversation starter, "
                "not a verdict.")
        if sc.get("destiny_sign"):
            text += " Your Suns share a modality, which tradition calls a destiny sign."
        sections.append(_section("score", "Relationship score", [
            _item("score", f"{sc['value']} · {sc['description']}", text + ("\n\n" + "\n".join(lines) if lines else ""))
        ]))

    people = []
    for nm, role in ((a_name, "first"), (b_name, "second")):
        pts = _points(data, role)
        bits = []
        for n in BIG_THREE:
            if n in pts and (n != "Ascendant" or _known(data, role)):
                s = M.SIGNS[pts[n]["sign"]]
                bits.append(f"{label(n)} in {pts[n]['sign']}: {s['gift']}.")
        if bits:
            people.append(_item(f"who-{role}", nm, " ".join(bits),
                                tarot=[c for n in ("Sun",) if n in pts for c in cards_for(n, pts[n]["sign"], pts[n]["degree"])]))
    sections.append(_section("people", "The two of you", people))

    overlays = []
    for (nm, role), (other, orole) in (((a_name, "first"), (b_name, "second")), ((b_name, "second"), (a_name, "first"))):
        pts, cusps = _points(data, role), _cusps(data, orole)
        if not _known(data, orole):
            continue
        for n in PERSONAL + ("Saturn",):
            if n not in pts:
                continue
            h = house_of(pts[n]["longitude"], cusps)
            if not h:
                continue
            title, area = M.HOUSES[h]
            overlays.append(_item(
                f"overlay-{role}-{n}", f"{nm}'s {label(n)} in {other}'s {M.ordinal(h)} house",
                f"{nm}'s {label(n)} ({_info(n)[2]}) falls in {other}'s house of {title.lower()}, which covers {area}. "
                f"{other} is likely to feel {nm}'s presence most in this area of life.",
                subtitle=f"{_deg(pts[n])} · {title}",
            ))
    sections.append(_section("overlays", "House overlays", overlays,
                             "Where each person's planets land in the other's chart shows which areas of life you stir up in each other."))

    asp = []
    unknown = {r for r in ("first", "second") if not _known(data, r)}
    names_unknown = {data["subjects"][r].get("name") for r in unknown}
    pool = [a for a in data.get("aspects", [])
            if not ((a["p1"] in TIME_SENSITIVE and a.get("p1_owner") in names_unknown)
                    or (a["p2"] in TIME_SENSITIVE and a.get("p2_owner") in names_unknown))]
    for a in top_aspects(pool, 10, same_chart=False):
        w1 = f"{a.get('p1_owner') or a_name}'s"
        w2 = f"{a.get('p2_owner') or b_name}'s"
        asp.append(aspect_item(a, f"{w1} {label(a['p1'])} {M.ASPECTS[a['aspect']][0].lower()} {w2} {label(a['p2'])}",
                               aspect_text(a, w1, w2)))
    sections.append(_section("aspects", "Key connections", asp,
                             "Inter-aspects show how your planets talk to each other. Harmonious links flow easily, and challenging ones spark growth and chemistry."))
    return sections


def _transit(data: dict) -> list[Optional[dict]]:
    natal, tr = _points(data, "natal"), _points(data, "transit")
    cusps = _cusps(data, "natal") if _known(data, "natal") else []
    t_blk = data["subjects"].get("transit", {})
    sections: list[Optional[dict]] = []

    slow = []
    for n in SLOW:
        if n not in tr:
            continue
        p = tr[n]
        h = house_of(p["longitude"], cusps)
        title, area = M.HOUSES[h] if h else ("", "")
        force = M.TRANSIT_FORCE.get(n, "is active")
        text = f"Transiting {label(n)} {force}."
        if h:
            text += f" It is moving through your {M.ordinal(h)} house of {title.lower()}, so this season touches {area}."
        if p.get("retrograde"):
            text += f" {label(n)} is retrograde now, which is a time to review rather than push."
        slow.append(_item(f"transit-{n}", f"{label(n)} in your {M.ordinal(h)} house" if h else f"{label(n)} in {p['sign']}",
                          text, subtitle=_deg(p) + (" · retrograde" if p.get("retrograde") else ""),
                          link="/signs/" + p["sign"].lower() if n == "Saturn" else None,
                          tarot=cards_for(n, p["sign"], p["degree"])))
    sections.append(_section("slow", "The long weather", slow,
                             "The slow planets set the tone for months or years. Saturn, the heart of this site, leads the way."))

    natal_name = data["subjects"]["natal"].get("name")
    asp = []
    natal_known = _known(data, "natal")
    pool = []
    for a in data.get("aspects", []):
        # p1 is natal, p2 is transiting (Kerykeion order); swap defensively
        n_pt, t_pt = (a["p1"], a["p2"]) if a.get("p1_owner") == natal_name else (a["p2"], a["p1"])
        if t_pt == "Moon" or (not natal_known and n_pt in TIME_SENSITIVE):
            continue
        pool.append((n_pt, t_pt, a))
    pool = [x for x in pool if _aspect_ok(x[2], False)]
    pool.sort(key=lambda x: (x[1] in SLOW, _aspect_rank(x[2])), reverse=True)
    for n_pt, t_pt, a in pool[:10]:
        name, verb, _, tone = M.ASPECTS[a["aspect"]]
        move = (a.get("movement") or "").lower()
        when = {"applying": "This aspect is still building toward exact.",
                "separating": "This aspect has peaked and is fading."}.get(move, "")
        text = (f"Transiting {label(t_pt)} {M.TRANSIT_FORCE.get(t_pt, 'is active')}. It is forming a {name.lower()} "
                f"to your natal {label(n_pt)}, which shows {_info(n_pt)[1]}. {when}")
        asp.append(aspect_item(a, f"Transiting {label(t_pt)} {name.lower()} natal {label(n_pt)}", text))
    sections.append(_section("aspects", "Active transits", asp,
                             "These are the closest contacts between today's sky and your birth chart, with slow planets first."))
    when = (t_blk.get("local_datetime") or "")[:10]
    if when:
        sections.insert(0, _section("moment", "The moment", [
            _item("moment", f"Transits for {when}", "This reading compares the sky at the chosen moment with your birth chart. "
                  "Fast planets like the Moon and Mercury move on within hours or days, while slow planets describe the chapter you are living in.")
        ]))
    return sections


def _return(data: dict, lunar: bool) -> list[Optional[dict]]:
    ret = _points(data, "return")
    blk = data["subjects"].get("return", {})
    when = (blk.get("local_datetime") or "")[:10]
    label_ret = "Lunar Return" if lunar else "Solar Return"
    span = "month" if lunar else "year"
    intro = (f"Your {label_ret} is the moment the {'Moon' if lunar else 'Sun'} returns to its exact birth position"
             f"{' (' + when + ')' if when else ''}. Its chart sets the tone for the {span} ahead.")
    themes = []
    if not _known(data, "natal"):
        themes.append(_item("no-time", "Birth time unknown",
                            f"Without a birth time the natal {'Moon' if lunar else 'Sun'} position is approximate, so the "
                            f"return moment{' can shift by many hours' if lunar else ' can shift by several hours'}. "
                            "Treat the return's houses and Rising sign as tentative."))
    if "Ascendant" in ret:
        s = M.SIGNS[ret["Ascendant"]["sign"]]
        themes.append(_item("ret-asc", f"{span.capitalize()} rising: {ret['Ascendant']['sign']}",
                            f"You meet this {span} {s['style']}. Lean into {s['gift']}, and watch for {s['edge']}.",
                            subtitle=_deg(ret["Ascendant"]), tarot=cards_for("Ascendant", ret["Ascendant"]["sign"], ret["Ascendant"]["degree"])))
    lead = ("Moon", "Sun") if lunar else ("Sun", "Moon")
    for n in lead:
        if n not in ret:
            continue
        p = ret[n]
        h = p.get("house")
        if not h:
            continue
        title, area = M.HOUSES[h]
        if n == lead[0]:
            tail = f"The {span}'s main stage is {area}."
        elif n == "Moon":
            tail = f"Your feelings this {span} gather around {area}."
        else:
            tail = f"Your sense of purpose this {span} turns toward {area}."
        text = f"The {label(n)} falls in the {M.ordinal(h)} house of {title.lower()}. {tail}"
        themes.append(_item(f"ret-{n}", f"{label(n)} in the {M.ordinal(h)} house", text,
                            subtitle=f"{_deg(p)} · {title}", tarot=cards_for(n, p["sign"], p["degree"])))
    if "Medium_Coeli" in ret:
        s = M.SIGNS[ret["Medium_Coeli"]["sign"]]
        themes.append(_item("ret-mc", f"Goals: Midheaven in {ret['Medium_Coeli']['sign']}",
                            f"Your ambitions this {span} move {s['style']}, and success comes through {s['gift']}.",
                            subtitle=_deg(ret["Medium_Coeli"])))
    planets = []
    for n in ("Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"):
        if n in ret and ret[n].get("house"):
            p, h = ret[n], ret[n]["house"]
            title, area = M.HOUSES[h]
            planets.append(_item(f"ret-p-{n}", f"{label(n)} in the {M.ordinal(h)} house",
                                 f"{label(n)}, which shows {_info(n)[1]}, is busy this {span} around {area}."
                                 + (" It is retrograde, so revisit before you push forward." if p.get("retrograde") else ""),
                                 subtitle=_deg(p)))
    natal_name = data["subjects"]["natal"].get("name")
    asp = []
    for a in top_aspects(data.get("aspects", []), 6, same_chart=False):
        n_pt, r_pt = (a["p1"], a["p2"]) if a.get("p1_owner") == natal_name else (a["p2"], a["p1"])
        if n_pt == r_pt and a["aspect"] == "conjunction" and n_pt == ("Moon" if lunar else "Sun"):
            continue  # the return itself
        name = M.ASPECTS[a["aspect"]][0]
        asp.append(aspect_item(a, f"Return {label(r_pt)} {name.lower()} natal {label(n_pt)}",
                               M.ASPECTS[a["aspect"]][2].format(
                                   a=f"This {span}'s {_info(r_pt)[2]} ({label(r_pt)})",
                                   b=f"your natal {_info(n_pt)[2]} ({label(n_pt)})")))
    return [
        _section("themes", f"Themes of the {span}", themes, intro),
        _section("planets", "Where the planets are busy", planets),
        _section("aspects", "Return to natal contacts", asp),
    ]


# ─── public API ─────────────────────────────────────────────────────────────


def interpret(data: dict) -> dict:
    """Build the built-in reading for any chart kind from ``ChartResult.data``."""
    kind = data.get("kind", "natal")
    if kind == "natal":
        sections = _natal_like(data, "natal")
        intro = "A map of the sky at your birth. Start with the Big Three, then explore each planet, the aspects between them, and your elemental balance."
    elif kind == "composite":
        sections = _natal_like(data, "composite", composite=True)
        intro = "A composite chart blends two birth charts into one, making the chart of the relationship itself. Read \"you\" as \"the two of you together\"."
    elif kind == "synastry":
        sections = _synastry(data)
        intro = "Synastry lays one chart over another to show how two people meet: where you flow, where you spark, and where you grow each other."
    elif kind == "transit":
        sections = _transit(data)
        intro = "Transits compare the moving sky with your birth chart. They describe timing and seasons, not fixed fate."
    elif kind in ("solar_return", "lunar_return"):
        sections = _return(data, kind == "lunar_return")
        intro = "A return chart is a personal new beginning, cast for the exact moment a planet comes home to its birth position."
    else:
        sections, intro = [], ""
    return {
        "kind": kind,
        "title": TITLES.get(kind, "Your chart reading"),
        "intro": intro,
        "sections": [s for s in sections if s],
        "disclaimer": M.DISCLAIMER,
        "credits": "Tarot correspondences: Golden Dawn system as used by Asteria (AGPL-3.0). Rider-Waite-Smith art, public domain.",
    }


def to_markdown(reading: dict) -> str:
    out = [f"# {reading['title']}", "", reading.get("intro", ""), ""]
    for s in reading["sections"]:
        out += [f"## {s['title']}", ""]
        if s.get("intro"):
            out += [f"_{s['intro']}_", ""]
        for it in s["items"]:
            head = f"### {it['title']}" + (f" — {it['subtitle']}" if it.get("subtitle") else "")
            out += [head, "", it["text"], ""]
            if it.get("tarot"):
                out += ["Tarot: " + ", ".join(f"{c['name']} ({c['keywords']})" for c in it["tarot"]), ""]
    out += ["---", reading["disclaimer"]]
    return "\n".join(out).strip() + "\n"
