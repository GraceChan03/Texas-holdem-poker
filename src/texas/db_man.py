from texas.models import *
from django.db.models import Count

def find_ranking(ranking_type):
    if ranking_type == 'rich':
        return UserInfo.objects.all().order_by('-balance')[:5]
    elif ranking_type == 'win':
        return WinnerHistory.objects.all().values('user').annotate(result=Count('user')).order_by('-result')[:5]
    elif ranking_type == 'pot':
        return WinnerHistory.objects.all().order_by('-pot')[:5]
    else:
        return None
