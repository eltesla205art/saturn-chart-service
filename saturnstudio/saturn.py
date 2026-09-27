"""
Saturn Finder: where Saturn was at birth, where it is on any date, and your whole Saturn cycle.

    from saturnstudio import Person
    from saturnstudio.saturn import saturn_finder

    me = Person("Andre", "1990-05-15", "14:30", lat=28.0836, lon=-80.6081, tz="America/New_York")
    report = saturn_finder(me)                       # at = now
    report = saturn_finder(me, at=Person("On", "2029-03-01", "12:00", lat=..., lon=..., tz=...))

The report is JSON-ready:
    birth      Saturn's sign, degree, house, retrograde, dignity and aspects in the natal chart
    at         Saturn on the chosen date: sign, degree, motion, the natal house it is crossing,
               the natal points it is touching, and when it changes sign
    cycle      exact dates of every Saturn square, opposition and return (with retrograde passes)
    reasoning  plain-language "because" statements linking each placement to its meaning

Houses: with a birth time, the natal houses are used. Without one, "solar houses" count from the
Sun sign (the Sun's sign is the 1st house), the method used by newspaper horoscopes.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import libephemeris as le

from . import meanings as M
from .core import DEFAULT_POINTS, Person, Studio
from .interpret import house_of, label

SIGN_ORDER = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
              "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
SIDM = {"LAHIRI": "SIDM_LAHIRI", "RAMAN": "SIDM_RAMAN", "KRISHNAMURTI": "SIDM_KRISHNAMURTI",
        "FAGAN_BRADLEY": "SIDM_FAGAN_BRADLEY"}
HARD = {"conjunction", "square", "opposition"}

DIGNITY = {
    "Capricorn": ("domicile", "Capricorn is Saturn's own sign, so its patience and structure come naturally to you."),
    "Aquarius": ("domicile", "Aquarius is one of Saturn's own signs, so its discipline serves your ideals and your community."),
    "Libra": ("exaltation", "Saturn is exalted in Libra, where its sense of justice and fair commitment shines."),
    "Cancer": ("detriment", "In Cancer, opposite its home, Saturn has to learn to hold feelings and family with gentle structure."),
    "Leo": ("detriment", "In Leo, opposite its home, Saturn has to learn to let the heart shine without fear of judgement."),
    "Aries": ("fall", "In Aries, Saturn's sign of fall, patience is the hard-won skill that turns raw courage into leadership."),
}

SATURN_IN_HOUSE = {
    1: "Saturn in the 1st house gives a serious, self-possessed presence. You may have grown up fast, and with time you become someone others lean on. The lesson is to be yourself without waiting for permission.",
    2: "Saturn in the 2nd house builds money, security and self-worth slowly and carefully. Early caution can mature into real financial wisdom and a steady sense of your own value.",
    3: "Saturn in the 3rd house makes you take words and learning seriously. You may once have doubted your voice, but practice makes you a clear, trusted communicator.",
    4: "Saturn in the 4th house often means home and family carried early responsibility or reserve. Your lifelong work is building the inner foundation and the home you needed, and it grows stronger with age.",
    5: "Saturn in the 5th house means joy, romance and creativity are never careless for you. With time and practice, your creative work gains real mastery and play becomes a discipline you love.",
    6: "Saturn in the 6th house devotes you to work, craft and routine. Watch for overwork and worry. Steady habits and a well-ordered day are where your health and skill grow.",
    7: "Saturn in the 7th house makes partnership a serious teacher. You may commit later, or choose steadier partners, and relationships built slowly and fairly are the ones that last.",
    8: "Saturn in the 8th house handles intimacy, trust and shared resources with caution. Facing fears around control and loss turns into deep resilience and wise stewardship.",
    9: "Saturn in the 9th house seeks a philosophy that holds up. Belief is earned rather than borrowed, and study, travel and teaching become lifelong disciplines.",
    10: "Saturn in the 10th house puts career and reputation at the centre. Success tends to come step by step and later in life, and it lasts. You are built for authority.",
    11: "Saturn in the 11th house makes you choose friends and communities carefully and stay loyal. Your hopes are long-term plans, and you may become a pillar of your group.",
    12: "Saturn in the 12th house works behind the scenes, in solitude, spiritual practice or quiet service. Old fears can surface, and reflection turns them into inner strength.",
}

TRANSIT_HOUSE = {
    1: "a season to redefine yourself: new responsibilities, a more serious image and care for your body and health",
    2: "a season to build financial stability, budget wisely and get clear about what you truly value",
    3: "a season of study, writing and communication, when your words carry weight and local ties matter",
    4: "a season of foundations: home, family and roots, sometimes a move or renovation, always inner rebuilding",
    5: "a season to commit to creative work, romance and joy, when fun asks for real intention",
    6: "a season to restructure routines, work habits and health, improving your systems without overworking",
    7: "a season when relationships and contracts are tested and formalised, and solid bonds deepen",
    8: "a season of shared finances, debts, intimacy and trust, and of deep psychological housekeeping",
    9: "a season to earn a qualification, travel with purpose or rebuild your philosophy of life",
    10: "a season of career peak or restructuring, when responsibility and recognition come to what you have built well",
    11: "a season to sort friendships, networks and long-term goals, investing in fewer, truer allies",
    12: "a season of closing chapters, rest and reflection, quietly preparing for a new cycle",
}

EVENTS = {
    90: ("Waxing Saturn square", "A crisis in action: what began at the last return meets resistance and has to prove itself. Effort now builds real strength."),
    180: ("Saturn opposition", "Culmination: you see the results of your efforts, and other people mirror your structures back to you. Adjust, balance and commit."),
    270: ("Waning Saturn square", "A crisis in consciousness: release outdated commitments and beliefs, and clear the ground for the next return."),
    0: ("Saturn return", ""),
}
RETURN_TEXT = {
    1: "Your first Saturn return, the classic coming-of-age. Structures that don't fit your true self fall away, and you step into adult authority.",
    2: "Your second Saturn return, a mastery review. You harvest what you have built and choose the legacy you want.",
    3: "Your third Saturn return: elderhood and wisdom, simplifying life to what truly matters.",
}


# ─── ephemeris helpers ──────────────────────────────────────────────────────


def _jd(dt: datetime) -> float:
    dt = dt.astimezone(timezone.utc)
    return le.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60 + dt.second / 3600)


def _date(jd: float) -> datetime:
    y, m, d, h = le.revjul(jd)
    return datetime(y, m, d, tzinfo=timezone.utc) + timedelta(hours=h)


class _Sky:
    """Apparent geocentric Saturn, tropical or sidereal."""

    def __init__(self, zodiac: str = "tropical", ayanamsa: str = "LAHIRI") -> None:
        self.sidereal = zodiac == "sidereal"
        self.mode = getattr(le, SIDM.get(ayanamsa, "SIDM_LAHIRI"))

    def trop(self, jd: float) -> tuple[float, float]:
        r = le.calc_ut(jd, le.SATURN, le.FLG_SPEED)[0]
        return r[0] % 360, r[3]

    def lon(self, jd: float) -> float:
        lon, _ = self.trop(jd)
        if self.sidereal:
            le.set_sid_mode(self.mode)
            lon = (lon - le.get_ayanamsa_ut(jd)) % 360
        return lon


def _wrap(x: float) -> float:
    return (x + 180) % 360 - 180


def _bisect(f, a: float, b: float, iters: int = 30) -> float:
    fa = f(a)
    for _ in range(iters):
        m = (a + b) / 2
        fm = f(m)
        if (fa < 0) == (fm < 0):
            a, fa = m, fm
        else:
            b = m
    return (a + b) / 2


def cycle_events(natal_lon: float, birth_jd: float, years: int = 95, step: float = 10.0) -> list[dict]:
    """Exact dates when transiting Saturn is 90°, 180°, 270° and 0° from its natal (tropical) position."""
    sky = _Sky()
    end = birth_jd + years * 365.25
    targets = {a: (natal_lon + a) % 360 for a in (90, 180, 270, 0)}
    hits: list[tuple[int, float]] = []
    jd, prev = birth_jd + 30, None
    while jd <= end:
        lon = sky.trop(jd)[0]
        cur = {a: _wrap(lon - t) for a, t in targets.items()}
        if prev:
            for a in targets:
                p, c = prev[a], cur[a]
                if (p < 0) != (c < 0) and abs(p) < 20 and abs(c) < 20:
                    t = _bisect(lambda x, a=a: _wrap(sky.trop(x)[0] - targets[a]), jd - step, jd)
                    if (t - birth_jd) / 365.25 > 5:  # skip retrograde wobbles over the natal point just after birth
                        hits.append((a, t))
        prev = cur
        jd += step
    # group passes (1 or 3 when retrograde) into events
    events: list[dict] = []
    for a, t in sorted(hits, key=lambda h: h[1]):
        if events and events[-1]["angle"] == a and t - events[-1]["_last"] < 400:
            events[-1]["passes"].append(t)
            events[-1]["_last"] = t
        else:
            events.append({"angle": a, "passes": [t], "_last": t})
    out, returns = [], 0
    for e in events:
        name, text = EVENTS[e["angle"]]
        if e["angle"] == 0:
            returns += 1
            name = f"Saturn return #{returns}"
            text = RETURN_TEXT.get(returns, "Another Saturn return: a full cycle completed.")
        first, last = e["passes"][0], e["passes"][-1]
        out.append({
            "event": name,
            "angle": e["angle"],
            "dates": [_date(p).date().isoformat() for p in e["passes"]],
            "age": round((first - birth_jd) / 365.25, 1),
            "meaning": text,
            "_first": first,
            "_last": last,
        })
    return out


def _next_ingress(sky: _Sky, jd: float, direction: int = 1, limit_days: int = 1500) -> Optional[dict]:
    start_sign = int(sky.lon(jd) // 30)
    step, t = 5.0 * direction, jd
    for _ in range(int(limit_days / 5)):
        t2 = t + step
        if int(sky.lon(t2) // 30) != start_sign:
            a, b = (t, t2) if direction > 0 else (t2, t)
            for _ in range(30):
                m = (a + b) / 2
                if (int(sky.lon(m) // 30) != start_sign) == (direction > 0):
                    b = m
                else:
                    a = m
            when = b if direction > 0 else a
            before = SIGN_ORDER[int(sky.lon(when - 0.01) // 30)]
            after = SIGN_ORDER[int(sky.lon(when + 0.01) // 30)]
            return {"date": _date(when).date().isoformat(), "sign": after, "from": before}
        t = t2
    return None


# ─── main API ───────────────────────────────────────────────────────────────


def _sign_idx(sign: str) -> int:
    return SIGN_ORDER.index(sign)


def _solar_house(sign: str, sun_sign: str) -> int:
    return (_sign_idx(sign) - _sign_idx(sun_sign)) % 12 + 1


def _deg(lon: float) -> str:
    d = lon % 30
    return f"{int(d)}°{int((d % 1) * 60):02d}′ {SIGN_ORDER[int(lon // 30) % 12]}"


def _aspect_text(asp: str, target: str, transit: bool) -> str:
    name = M.ASPECTS[asp][0].lower()
    lab, domain = label(target), M.POINTS.get(target, (target, "this part of you"))[1]
    who = "Saturn" if transit else "Your Saturn"
    if asp in HARD:
        body = (f"{domain[0].upper() + domain[1:]} is being tested and restructured. Pressure here is a call to mature, "
                f"set clear limits and build something that lasts.") if transit else \
               (f"{domain[0].upper() + domain[1:]} learns through effort and responsibility. It can feel heavy early on, "
                f"but it becomes one of your most reliable strengths with age.")
    else:
        body = (f"{domain[0].upper() + domain[1:]} gains structure and support. It is a good window to commit, plan and build.") if transit else \
               (f"{domain[0].upper() + domain[1:]} is steadied by Saturn's patience, giving you staying power and good judgement here.")
    return f"{who} {name} your {'natal ' if transit else ''}{lab}: {body[0].lower() + body[1:]}"


def saturn_finder(person: Person, at: Optional[Person] = None, *, zodiac: str = "tropical",
                  ayanamsa: str = "LAHIRI", house_system: str = "P", years: int = 95) -> dict:
    """Saturn at birth, on a chosen date (default: now at the birthplace) and across the whole life cycle."""
    studio = Studio(zodiac=zodiac, ayanamsa=ayanamsa, house_system=house_system, draw=False,
                    points=list(DEFAULT_POINTS))
    if at is None:
        at = Person.now(float(person.lat), float(person.lon), str(person.tz), name="Today", place=person.place)
    tr = studio.transit(person, when=at)
    natal_blk, t_blk = tr.data["subjects"]["natal"], tr.data["subjects"]["transit"]
    npts = {p["name"]: p for p in natal_blk["points"]}
    tpts = {p["name"]: p for p in t_blk["points"]}
    known = person.time_known
    sun_sign = npts["Sun"]["sign"]
    house_mode = "natal" if known else "solar"
    cusps = [h["longitude"] for h in natal_blk["houses"]] if known else []

    def house_for(sign: str, lon: float) -> int:
        return house_of(lon, cusps) if known else _solar_house(sign, sun_sign)

    ns, ts = npts["Saturn"], tpts["Saturn"]
    n_house = house_for(ns["sign"], ns["longitude"])
    t_house = house_for(ts["sign"], ts["longitude"])

    natal = studio.natal(person)
    n_aspects = [a for a in natal.data["aspects"] if "Saturn" in (a["p1"], a["p2"]) and a["aspect"] in M.ASPECTS]
    n_aspects.sort(key=lambda a: a["orb"])
    natal_name = natal_blk.get("name")
    t_aspects = []
    for a in tr.data["aspects"]:
        n_pt, t_pt = (a["p1"], a["p2"]) if a.get("p1_owner") == natal_name else (a["p2"], a["p1"])
        if t_pt != "Saturn" or a["aspect"] not in M.ASPECTS:
            continue
        if not known and n_pt in {"Ascendant", "Medium_Coeli", "Descendant", "Imum_Coeli"}:
            continue
        t_aspects.append({"target": n_pt, "aspect": a["aspect"], "orb": a["orb"], "movement": a.get("movement")})
    t_aspects.sort(key=lambda a: a["orb"])

    # cycle (tropical difference; identical in any zodiac)
    birth_dt = datetime.fromisoformat(natal_blk["utc_datetime"])
    at_dt = datetime.fromisoformat(t_blk["utc_datetime"])
    birth_jd, at_jd = _jd(birth_dt), _jd(at_dt)
    sky_t = _Sky()
    natal_trop = sky_t.trop(birth_jd)[0]
    events = cycle_events(natal_trop, birth_jd, years=years)
    current = None
    for e in events:
        if e["_first"] - 100 <= at_jd <= e["_last"] + 100:  # about ±3° of orb
            e["status"] = "now"
            current = e
        elif e["_last"] < at_jd:
            e["status"] = "past"
        else:
            e["status"] = "upcoming"
    nxt = next((e for e in events if e["status"] == "upcoming"), None)
    phase = (sky_t.trop(at_jd)[0] - natal_trop) % 360
    for e in events:
        e.pop("_first"), e.pop("_last")

    sky = _Sky(zodiac, ayanamsa)
    speed = sky_t.trop(at_jd)[1]
    age = (at_jd - birth_jd) / 365.25

    title_n, area_n = M.HOUSES[n_house]
    title_t, area_t = M.HOUSES[t_house]
    house_word = "house" if known else "solar house"
    dig = DIGNITY.get(ns["sign"])

    birth = {
        "sign": ns["sign"], "degree": ns["degree"], "longitude": ns["longitude"], "position": _deg(ns["longitude"]),
        "retrograde": ns["retrograde"], "house": n_house, "house_title": title_n, "house_mode": house_mode,
        "dignity": dig[0] if dig else "peregrine", "sun_sign": sun_sign,
        "aspects": [{"target": (a["p2"] if a["p1"] == "Saturn" else a["p1"]), "aspect": a["aspect"], "orb": a["orb"]} for a in n_aspects],
        "date": natal_blk["local_datetime"],
    }
    at_out = {
        "date": t_blk["local_datetime"], "sign": ts["sign"], "degree": ts["degree"], "longitude": ts["longitude"],
        "position": _deg(ts["longitude"]), "retrograde": speed < 0, "speed": round(speed, 4),
        "house": t_house, "house_title": title_t, "house_mode": house_mode, "aspects": t_aspects,
        "entered_sign": _next_ingress(sky, at_jd, -1), "next_sign": _next_ingress(sky, at_jd, 1),
        "age": round(age, 1), "phase_degrees": round(phase, 1),
        "cycle_number": int(age // 29.46) + 1,
    }

    # reasoning
    why: list[dict] = []
    why.append({
        "topic": "birth-sign",
        "claim": f"At your birth, Saturn was at {birth['position']}{' (retrograde)' if ns['retrograde'] else ''}.",
        "because": "Saturn's sign shows how you meet responsibility, limits and time. "
                   + (dig[1] if dig else f"In {ns['sign']}, Saturn works {M.SIGNS[ns['sign']]['style']}."),
        "link": f"/signs/{ns['sign'].lower()}",
    })
    why.append({
        "topic": "birth-house",
        "claim": f"It sits in your {M.ordinal(n_house)} {house_word}: {title_n.lower()}.",
        "because": SATURN_IN_HOUSE[n_house] + ("" if known else
                   f" Without a birth time, this counts houses from your Sun sign ({sun_sign} = 1st house)."),
    })
    if ns["retrograde"]:
        why.append({"topic": "birth-retrograde", "claim": "Saturn was retrograde when you were born.",
                    "because": "Retrograde Saturn turns its lessons inward. You often build your own rules rather than "
                               "accepting others', and your authority matures from the inside out."})
    for a in n_aspects[:4]:
        tgt = a["p2"] if a["p1"] == "Saturn" else a["p1"]
        why.append({"topic": "birth-aspect", "claim": f"Saturn {M.ASPECTS[a['aspect']][0].lower()} {label(tgt)} (orb {a['orb']:.1f}°).",
                    "because": _aspect_text(a["aspect"], tgt, transit=False)})
    why.append({
        "topic": "now-house",
        "claim": f"On {at_out['date'][:10]}, Saturn is at {at_out['position']}{' (retrograde)' if at_out['retrograde'] else ''}, "
                 f"crossing your {M.ordinal(t_house)} {house_word} of {title_t.lower()}.",
        "because": f"Saturn takes about 2½ years to cross a house. This is {TRANSIT_HOUSE[t_house]}.",
    })
    for a in t_aspects[:4]:
        move = (a.get("movement") or "").lower()
        why.append({"topic": "now-aspect",
                    "claim": f"Saturn {M.ASPECTS[a['aspect']][0].lower()} your natal {label(a['target'])} (orb {a['orb']:.1f}°"
                             + (f", {move}" if move in ("applying", "separating") else "") + ").",
                    "because": _aspect_text(a["aspect"], a["target"], transit=True)})
    if current:
        why.append({"topic": "cycle-now", "claim": f"You are in your {current['event']} ({', '.join(current['dates'])}).",
                    "because": current["meaning"]})
    elif nxt:
        why.append({"topic": "cycle-next", "claim": f"Your next Saturn milestone is the {nxt['event']} around age {nxt['age']:.0f} ({nxt['dates'][0]}).",
                    "because": nxt["meaning"]})

    return {
        "birth": birth,
        "at": at_out,
        "cycle": {"events": events, "current": current["event"] if current else None,
                  "next": nxt, "phase_degrees": round(phase, 1)},
        "reasoning": why,
        "settings": {"zodiac": zodiac, "ayanamsa": ayanamsa if zodiac == "sidereal" else None,
                     "house_system": tr.data["settings"]["house_system"], "time_known": known},
        "disclaimer": M.DISCLAIMER,
    }
