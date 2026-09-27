"""
Tarot correspondences for chart points (Golden Dawn system).

The mapping follows Asteria by Alamahant (AGPL-3.0, https://github.com/alamahant/Asteria):
planets and signs map to Major Arcana; each 10° decan of a sign maps to a numbered
Minor Arcana card. Card numbers use Asteria's order: 0–21 Majors, 22–35 Wands,
36–49 Cups, 50–63 Swords, 64–77 Pentacles (Ace … King).

Decan titles are the traditional Golden Dawn names (19th century, public domain).
Card art (on whereismysaturn.com): the 1909 Rider-Waite-Smith deck by Pamela Colman Smith, public domain.
"""
from __future__ import annotations

from typing import Optional

MAJOR = {
    0: ("The Fool", "fresh starts, freedom, the leap of faith"),
    1: ("The Magician", "skill, will and the power to make ideas real"),
    2: ("The High Priestess", "intuition, mystery, the inner voice"),
    3: ("The Empress", "abundance, beauty, love and fertility"),
    4: ("The Emperor", "structure, leadership and self-command"),
    5: ("The Hierophant", "tradition, teaching and what you hold sacred"),
    6: ("The Lovers", "union, choice and harmony of opposites"),
    7: ("The Chariot", "willpower, protection and forward motion"),
    8: ("Strength", "courage, patience and gentle mastery"),
    9: ("The Hermit", "solitude, wisdom and the inner lamp"),
    10: ("Wheel of Fortune", "cycles, luck and turning points"),
    11: ("Justice", "balance, truth and fair consequence"),
    12: ("The Hanged Man", "surrender, pause and a new point of view"),
    13: ("Death", "endings that clear the way for rebirth"),
    14: ("Temperance", "balance, healing and the middle path"),
    15: ("The Devil", "ambition, attachment and material mastery"),
    16: ("The Tower", "sudden change, breakthrough, truth revealed"),
    17: ("The Star", "hope, renewal and faith in the future"),
    18: ("The Moon", "dreams, the unconscious and hidden tides"),
    19: ("The Sun", "joy, vitality and radiant success"),
    20: ("Judgement", "awakening, calling and rebirth"),
    21: ("The World", "completion, mastery and the long work fulfilled"),
}

PLANET_MAJOR = {
    "Sun": 19, "Moon": 2, "Mercury": 1, "Venus": 3, "Mars": 16, "Jupiter": 10,
    "Saturn": 21, "Uranus": 0, "Neptune": 12, "Pluto": 20,
}

SIGN_MAJOR = {
    "Aries": 4, "Taurus": 5, "Gemini": 6, "Cancer": 7, "Leo": 8, "Virgo": 9,
    "Libra": 11, "Scorpio": 13, "Sagittarius": 14, "Capricorn": 15, "Aquarius": 17, "Pisces": 18,
}

SUITS = {22: "Wands", 36: "Cups", 50: "Swords", 64: "Pentacles"}

# (suit base, first pip) per sign — decans I, II, III use pips first, first+1, first+2.
DECAN_TABLE = {
    "Aries": (22, 2), "Leo": (22, 5), "Sagittarius": (22, 8),
    "Cancer": (36, 2), "Scorpio": (36, 5), "Pisces": (36, 8),
    "Libra": (50, 2), "Aquarius": (50, 5), "Gemini": (50, 8),
    "Capricorn": (64, 2), "Taurus": (64, 5), "Virgo": (64, 8),
}

GOLDEN_DAWN_TITLES = {
    "Wands": {2: "Dominion", 3: "Established Strength", 4: "Perfected Work", 5: "Strife", 6: "Victory",
              7: "Valour", 8: "Swiftness", 9: "Great Strength", 10: "Oppression"},
    "Cups": {2: "Love", 3: "Abundance", 4: "Blended Pleasure", 5: "Loss in Pleasure", 6: "Pleasure",
             7: "Illusionary Success", 8: "Abandoned Success", 9: "Material Happiness", 10: "Perfected Success"},
    "Swords": {2: "Peace Restored", 3: "Sorrow", 4: "Rest from Strife", 5: "Defeat", 6: "Earned Success",
               7: "Unstable Effort", 8: "Shortened Force", 9: "Despair and Cruelty", 10: "Ruin"},
    "Pentacles": {2: "Harmonious Change", 3: "Material Works", 4: "Earthly Power", 5: "Material Trouble",
                  6: "Material Success", 7: "Success Unfulfilled", 8: "Prudence", 9: "Material Gain", 10: "Wealth"},
}

PIP_WORDS = {2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten"}


def card(number: int, role: str) -> dict:
    """A JSON-ready card: number, name, keywords, image file stem and the role it plays."""
    if number in MAJOR:
        name, keywords = MAJOR[number]
        return {"number": number, "name": name, "keywords": keywords, "arcana": "major", "file": f"{number:02d}", "role": role}
    base = max(b for b in SUITS if b <= number)
    suit, pip = SUITS[base], number - base + 1
    title = GOLDEN_DAWN_TITLES[suit].get(pip, "")
    return {
        "number": number,
        "name": f"{PIP_WORDS.get(pip, pip)} of {suit}",
        "keywords": f"Lord of {title}" if title else suit.lower(),
        "arcana": "minor",
        "file": f"{number:02d}",
        "role": role,
    }


def decan_card(sign: str, degree: float) -> Optional[dict]:
    """Minor Arcana card for the decan (0–10°, 10–20°, 20–30°) of a sign."""
    if sign not in DECAN_TABLE:
        return None
    base, first = DECAN_TABLE[sign]
    idx = min(2, max(0, int(degree // 10)))
    return card(base + first + idx - 1, f"decan {idx + 1} of {sign}")


def cards_for(point: str, sign: str, degree: float) -> list[dict]:
    """Planet card (if any), sign card and decan card for a placement."""
    out = []
    if point in PLANET_MAJOR:
        out.append(card(PLANET_MAJOR[point], point))
    if sign in SIGN_MAJOR:
        out.append(card(SIGN_MAJOR[sign], sign))
    d = decan_card(sign, degree)
    if d:
        out.append(d)
    return out
