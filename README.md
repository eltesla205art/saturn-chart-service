<h1 align="center">Saturn Studio</h1>

<p align="center">
  App-ready astrology charts in Python, plus the open-source chart service behind
  <a href="https://whereismysaturn.com/chart-studio">whereismysaturn.com/chart-studio</a>.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12%2B-blue" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/license-AGPL--3.0-blue" alt="License: AGPL-3.0">
  <img src="https://img.shields.io/badge/built%20on-Kerykeion%206-8a2be2" alt="Built on Kerykeion 6">
  <img src="https://img.shields.io/badge/tests-29%20passing-brightgreen" alt="29 tests passing">
</p>

Give Saturn Studio someone's birth details and get back accurate planetary positions, houses, aspects, signs,
elements, qualities and Moon-phase information as clean JSON. It also draws good-looking SVG charts for natal,
synastry, transit, composite, Solar Return and Lunar Return charts, and produces a plain-text report, an AI-friendly
context string, and a relationship score for two people.

Saturn Studio is a thin, opinionated layer over [Kerykeion](https://github.com/g-battaglia/kerykeion) by Giacomo
Battaglia, which does the astronomy (NASA JPL-based ephemeris) and the chart drawing.

## Table of contents

- [Installation](#installation)
- [Quick start](#quick-start)
- [Feature overview](#feature-overview)
- [Chart types](#chart-types)
- [Chart options](#chart-options)
- [Structured data](#structured-data)
- [Reports and AI context](#reports-and-ai-context)
- [Relationship score](#relationship-score)
- [Locations: offline and online](#locations-offline-and-online)
- [HTTP API](#http-api)
- [Examples](#examples)
- [Tests](#tests)
- [Privacy](#privacy)
- [License](#license)

## Installation

```bash
pip install "git+https://github.com/eltesla205art/saturn-chart-service"
```

Requires Python 3.12 or newer. Everything works offline once installed.

## Quick start

```python
from saturnstudio import Person, Studio

me = Person("Andre", "1990-05-15", "14:30",
            lat=28.0836, lon=-80.6081, tz="America/New_York", place="Melbourne, FL, USA")

chart = Studio(style="modern", theme="dark").natal(me)

chart.save_svg("natal.svg")          # the chart image
print(chart.to_json())               # clean, structured data
print(chart.report())                # a readable text report
print(chart.context())               # compact XML for LLM prompts
```

```text
Saturn: 25.24° Capricorn, house 5, retrograde=True
Elements: {'fire': 9, 'earth': 47, 'air': 25, 'water': 19}
Moon phase: Waning Gibbous
```

## Feature overview

| Feature | How |
| --- | --- |
| Planet positions, signs, degrees, houses, retrogrades | `chart.data["subjects"][role]["points"]` |
| House cusps (Placidus, Koch, Whole Sign, Equal, …) | `chart.data["subjects"][role]["houses"]`, `Studio(house_system="W")` |
| Aspects with orbs and applying/separating | `chart.data["aspects"]` |
| Element and quality balance | `chart.data["elements"]`, `chart.data["qualities"]` |
| Moon phase | `chart.data["subjects"]["natal"]["moon_phase"]` |
| SVG charts: modern or classic style | `Studio(style="classic")` |
| Themes | `Studio(theme="dark" \| "classic" \| "black-and-white")` |
| Languages | `Studio(language="ES")`: EN, ES, FR, PT, IT, DE, RU, TR, CN, HI |
| Wheel-only output | `Studio(wheel_only=True)` |
| Choose planets and points | `Studio(points=["Sun", "Moon", "Saturn", "Ascendant"])` |
| Tropical or sidereal zodiac | `Studio(zodiac="sidereal", ayanamsa="LAHIRI")` |
| Text report | `chart.report()` |
| AI context serializer | `chart.context()` |
| Relationship score | `studio.relationship_score(a, b)` or `studio.synastry(a, b).score` |
| Online city lookup | `Person.lookup(..., city="Rome", country="IT")` |

## Chart types

```python
studio = Studio()
studio.natal(me)
studio.synastry(me, partner)            # bi-wheel, includes relationship score
studio.transit(me)                       # transits now, at the birthplace
studio.transit(me, when=Person("Then", "2027-01-01", "09:00", lat=..., lon=..., tz=...))
studio.composite(me, partner)            # midpoint composite
studio.solar_return(me, 2026)            # next Solar Return from 1 Jan 2026
studio.lunar_return(me, 2026, 9)         # next Lunar Return from 1 Sep 2026
studio.build("synastry", me, partner)    # dispatch by name
```

## Chart options

| Option | Default | Values |
| --- | --- | --- |
| `style` | `"modern"` | `"modern"`, `"classic"` |
| `theme` | `"dark"` | `"dark"`, `"classic"`, `"black-and-white"` |
| `language` | `"EN"` | `EN ES FR PT IT DE RU TR CN HI` |
| `wheel_only` | `False` | draw the wheel without the side tables |
| `points` | ten planets, true node, ASC, MC | any of `saturnstudio.POINTS` |
| `zodiac` | `"tropical"` | `"tropical"`, `"sidereal"` |
| `ayanamsa` | `"LAHIRI"` | `LAHIRI RAMAN KRISHNAMURTI FAGAN_BRADLEY` |
| `house_system` | `"P"` | `P` Placidus, `K` Koch, `W` Whole Sign, `A` Equal, `R` Regiomontanus, `C` Campanus, `O` Porphyry |
| `title` | automatic | any string |

Chiron and the asteroids are available, but they are approximate outside the bundled ephemeris range.

## Structured data

`chart.data` is plain JSON-ready Python:

```json
{
  "kind": "natal",
  "settings": {"style": "modern", "theme": "dark", "zodiac": "tropical", "house_system": "Placidus", "...": "..."},
  "subjects": {
    "natal": {
      "name": "Andre", "local_datetime": "1990-05-15T14:30:00-04:00", "utc_datetime": "1990-05-15T18:30:00+00:00",
      "points": [{"name": "Saturn", "sign": "Capricorn", "degree": 25.2448, "longitude": 295.2448,
                  "element": "Earth", "quality": "Cardinal", "house": 5, "retrograde": true, "speed": -0.01733}],
      "houses": [{"house": 1, "sign": "Virgo", "degree": 12.443, "longitude": 162.443}],
      "moon_phase": {"name": "Waning Gibbous", "major_phase": "Last Quarter", "stage": "waning"}
    }
  },
  "aspects": [{"p1": "Sun", "p2": "Moon", "aspect": "trine", "orb": 5.859, "movement": "Separating"}],
  "elements": {"fire": 9, "earth": 47, "air": 25, "water": 19},
  "qualities": {"cardinal": 28, "fixed": 41, "mutable": 31}
}
```

Subject roles by chart type: `natal`; `first`/`second` (synastry); `natal`/`transit`; `composite`; `natal`/`return`.

## Reports and AI context

```python
print(chart.report(max_aspects=10))   # birth data, positions, houses, aspects as text tables
ctx = chart.context()                  # <chart_analysis …> XML, token-efficient for LLMs
```

## Relationship score

```python
score = studio.relationship_score(me, partner)
# {'value': 25, 'description': 'Exceptional', 'destiny_sign': True, 'breakdown': [...]}
```

The score follows Ciro Discepolo's synastry method as implemented in Kerykeion. It is an astrological index, not a
prediction.

## Locations: offline and online

- **Offline (recommended):** pass `lat`, `lon` and an IANA `tz` such as `"America/New_York"`. No network needed.
- **Online:** `Person.lookup(name, date, time, city="London", country="GB")` uses the GeoNames API. Set
  `GEONAMES_USERNAME` (free account at geonames.org) or pass `geonames_username=`.

## HTTP API

This repo is also deployed as a Vercel service at `https://chart.whereismysaturn.com`.

- `POST /api/studio`: any chart type, returning `svg`, `data`, `report`, `context` and `score`. See the docstring in
  `api/studio.py`.
- `POST /api/chart`: a single natal SVG (used by the result page).

## Examples

| File | Shows |
| --- | --- |
| `examples/01_natal.py` | natal SVG, JSON, report |
| `examples/02_synastry_and_score.py` | synastry, relationship score, composite |
| `examples/03_transits_and_returns.py` | transits now, Solar and Lunar Returns |
| `examples/04_options_and_ai_context.py` | wheel-only, classic style, Spanish, sidereal, LLM prompt |
| `examples/05_online_lookup.py` | GeoNames city lookup |

## Tests

```bash
pip install -e ".[dev]"
python -m pytest
```

The 29 tests cover reference positions (Saturn 25°14′ Capricorn for the sample chart), every chart type, return
timing, options, sidereal mode, reports, AI context, the relationship score, the API layer and input validation.

## Privacy

The service uses birth data in memory for one request and never stores or logs it. Requests carry data in the body,
not the URL. Responses are `no-store`, and CORS only admits whereismysaturn.com.

## License

AGPL-3.0, the same as Kerykeion. This repository is the complete corresponding source of the service running at
chart.whereismysaturn.com. See `LICENSE` and `NOTICE`.
