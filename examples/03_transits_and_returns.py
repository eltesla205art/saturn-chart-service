"""Transits now, this year's Solar Return and this month's Lunar Return."""
from saturnstudio import Person, Studio

me = Person("Andre", "1990-05-15", "14:30", lat=28.0836, lon=-80.6081, tz="America/New_York", place="Melbourne, FL, USA")
studio = Studio(theme="dark", points=["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Ascendant"])

studio.transit(me).save_svg("transits_now.svg")
sr = studio.solar_return(me, 2026)
print("Solar Return:", sr.data["subjects"]["return"]["local_datetime"])
sr.save_svg("solar_return_2026.svg")
lr = studio.lunar_return(me)
print("Next Lunar Return:", lr.data["subjects"]["return"]["local_datetime"])
