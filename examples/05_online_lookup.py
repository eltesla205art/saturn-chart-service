"""Online location lookup via GeoNames (needs a free username: https://www.geonames.org/login).

    GEONAMES_USERNAME=yourname python examples/05_online_lookup.py
"""
from saturnstudio import Person, Studio

person = Person.lookup("Ada", "1815-12-10", "13:00", city="London", country="GB")
print(Studio().natal(person).data["subjects"]["natal"]["points"][6])
