import requests
import foursquare

from jsonfield import JSONField

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User


class Country(models.Model):
    name = models.CharField(max_length=100, unique=True, null=True, blank=True)


class City(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    country = models.ForeignKey(Country)


class Checkin(models.Model):
    checkin_id = models.CharField(max_length=42, primary_key=True, unique=True)
    venue_name = models.CharField(max_length=100)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    city = models.ForeignKey(City)
    user = models.ForeignKey(User)
    data = JSONField()

    @classmethod
    def import_checkins(cls, user):
        sa = user.social_auth.get(provider='foursquare')
        client = foursquare.Foursquare(access_token=sa.tokens['access_token'])
        
        limit = 250
        for offset in xrange(0, 999999, limit):
            data = client.users.checkins(
                params={'limit': limit, 'offset': offset})

            items = data['checkins']['items']
            if items:
                cls._import_items(items, user)
            else:
                return

    @classmethod
    def _import_items(cls, checkins, user):
        for checkin in checkins:
            if not 'venue' in checkin or 'location' not in checkin['venue']:
                continue

            location = checkin['venue']['location']

            country, _ = Country.objects.get_or_create(
                name=location.get('country'))

            city, created = City.objects.get_or_create(
                name=location.get('city'), country=country)

            if created and city.name:
                # get lat & lng of the city
                address = ', '.join([city.name, city.country.name])
                params = {'address': address, 'sensor': 'false'}
                response = requests.get(settings.GOOGLE_GEOCODE_API_URL,
                                        params=params)

                # TODO find city coordinates?
                city_location = response.json['results'][0]['geometry']['location']
                city.lat = city_location['lat']
                city.lng = city_location['lng']
                city.save()

            cls.objects.create(
                checkin_id=checkin['id'], data=checkin, city=city, user=user,
                lat=location['lat'], lng=location['lng'],
                venue_name=checkin['venue']['name'])

