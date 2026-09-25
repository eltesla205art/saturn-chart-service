"""Natal chart: SVG + JSON + report. Run: python examples/01_natal.py"""
from saturnstudio import Person, Studio

me = Person("Andre", "1990-05-15", "14:30", lat=28.0836, lon=-80.6081, tz="America/New_York", place="Melbourne, FL, USA")
chart = Studio(style="modern", theme="dark").natal(me)

chart.save_svg("andre_natal.svg")
with open("andre_natal.json", "w") as f:
    f.write(chart.to_json())

saturn = next(p for p in chart.data["subjects"]["natal"]["points"] if p["name"] == "Saturn")
print(f"Saturn: {saturn['degree']:.2f}° {saturn['sign']}, house {saturn['house']}, retrograde={saturn['retrograde']}")
print("Elements:", chart.data["elements"])
print("Moon phase:", chart.data["subjects"]["natal"]["moon_phase"]["name"])
print(chart.report(max_aspects=8))
