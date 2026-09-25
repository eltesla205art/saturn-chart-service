"""Synastry bi-wheel + relationship score. Run: python examples/02_synastry_and_score.py"""
from saturnstudio import Person, Studio

a = Person("Andre", "1990-05-15", "14:30", lat=28.0836, lon=-80.6081, tz="America/New_York", place="Melbourne, FL, USA")
b = Person("Jordan", "1992-11-03", "08:05", lat=40.7128, lon=-74.006, tz="America/New_York", place="New York, NY, USA")

studio = Studio(theme="classic", style="classic")
syn = studio.synastry(a, b)
syn.save_svg("synastry.svg")
print(f"Relationship score: {syn.score['value']} ({syn.score['description']})")
for item in syn.score["breakdown"]:
    print(f"  +{item['points']}  {item['description']}")

studio.composite(a, b).save_svg("composite.svg")
