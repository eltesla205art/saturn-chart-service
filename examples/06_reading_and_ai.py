"""Built-in chart reading (offline) and an optional Claude deep reading."""
import os

from saturnstudio import Person, Studio
from saturnstudio.ai import anonymized, deep_reading

me = Person("Andre", "1990-05-15", "14:30", lat=28.0836, lon=-80.6081, tz="America/New_York")
chart = Studio().natal(me)

# 1. Built-in reading: no network, no AI. A dict for apps, or Markdown for people.
reading = chart.interpret()
for section in reading["sections"]:
    print(f"{section['title']}: {len(section['items'])} items")
print(chart.reading_markdown()[:900], "…\n")

# Each placement carries its tarot correspondences (Golden Dawn system, as in Asteria)
sun = reading["sections"][0]["items"][0]
print(sun["title"], "→", ", ".join(c["name"] for c in sun["tarot"]))

# 2. What an AI model would see: positions only, no name, place or birth date
print(list(anonymized(chart.data)["charts"]["Natal"]["points"][:2]))

# 3. Optional deep reading with Claude (needs ANTHROPIC_API_KEY)
if os.environ.get("ANTHROPIC_API_KEY"):
    print(deep_reading(chart, language="EN"))
else:
    print("Set ANTHROPIC_API_KEY to try the Claude deep reading.")
