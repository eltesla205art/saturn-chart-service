"""
saturnstudio — a friendly, app-ready astrology toolkit built on Kerykeion.

    from saturnstudio import Person, Studio

    me = Person("Andre", "1990-05-15", "14:30", lat=28.0836, lon=-80.6081,
                tz="America/New_York", place="Melbourne, FL, USA")
    studio = Studio(style="modern", theme="dark")
    chart = studio.natal(me)

    chart.svg            # full SVG chart (or wheel only with Studio(wheel_only=True))
    chart.data           # clean dict: points, houses, aspects, elements, qualities, moon phase
    chart.to_json()      # JSON string
    chart.report()       # plain-text report
    chart.context()      # AI-friendly XML context for LLM prompts
    chart.interpret()    # built-in plain-language reading (dict) with tarot correspondences
    chart.reading_markdown()

Saturn Finder: saturn_finder(person, at=...) → Saturn at birth, on any date, and your Saturn cycle.

Chart types: natal, synastry, transit, composite, solar_return, lunar_return.
Relationship score: studio.relationship_score(a, b) or studio.synastry(a, b).score

License: AGPL-3.0 (same as Kerykeion).
"""
from .core import (
    AYANAMSAS,
    DEFAULT_POINTS,
    HOUSE_SYSTEMS,
    LANGUAGES,
    POINTS,
    STYLES,
    THEMES,
    ChartResult,
    Person,
    Studio,
    StudioError,
)
from .interpret import interpret, to_markdown
from .saturn import saturn_finder
from .tarot import cards_for

__all__ = [
    "Person",
    "Studio",
    "ChartResult",
    "StudioError",
    "DEFAULT_POINTS",
    "POINTS",
    "THEMES",
    "STYLES",
    "LANGUAGES",
    "AYANAMSAS",
    "HOUSE_SYSTEMS",
    "interpret",
    "to_markdown",
    "cards_for",
    "saturn_finder",
]
__version__ = "1.2.0"
