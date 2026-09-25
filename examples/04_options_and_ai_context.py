"""Wheel-only, classic style, Spanish labels, sidereal zodiac, and an LLM-ready context string."""
from saturnstudio import Person, Studio

me = Person("Andre", "1990-05-15", "14:30", lat=28.0836, lon=-80.6081, tz="America/New_York", place="Melbourne, FL, USA")
studio = Studio(style="classic", theme="black-and-white", language="ES", wheel_only=True,
                zodiac="sidereal", ayanamsa="LAHIRI", house_system="W")
chart = studio.natal(me)
chart.save_svg("wheel_es_sidereal.svg")

prompt = f"""You are a thoughtful astrologer. Using only the chart data below, describe this person's Saturn placement.

{chart.context()}"""
print(prompt[:1200])
