from django.shortcuts import render
from django.db.models import Count

from social_auth.models import UserSocialAuth

from . import models


def home(request):
    user = request.user
    context = {}
    
    if user.is_authenticated():
        if not models.Checkin.objects.filter(user=user).exists():
            models.Checkin.import_checkins(user)

        checkins = models.Checkin.objects.filter(user=user)

        context['checkin_count'] = checkins.count()

        city_id = request.GET.get('city')
        if city_id:
            city = models.City.objects.get(pk=city_id)
            checkins = checkins.filter(city=city)
            context['city'] = city

        context['checkins'] = checkins.distinct('venue_name')

        cities = models.City.objects.annotate(
            checkin_count=Count('checkin')).order_by('-checkin_count')

        context['cities'] = cities

    return render(request, 'home.html', context)
