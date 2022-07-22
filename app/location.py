from geopy.geocoders import Nominatim
from app import app


def get_city_country(latitude, longitude):

    geolocator = Nominatim(user_agent="SmartIrrigation", scheme='https')

    lat_long = "% s, % s" % (str(latitude), str(longitude))
    location = geolocator.reverse(lat_long, timeout=3)

    return location.raw
