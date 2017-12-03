# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from datetime import date
from django.contrib import auth
from django.urls import reverse

from .forms import *
from .models import *
from .util import send_email
from mimetypes import guess_type
from datetime import datetime
from texas.db_man import find_ranking

@login_required(login_url='login')
def show_scoreboard(request):
    context = {}
    context['searchForm'] = SearchUser()
    form = ScoreboardForm()
    ranking_type = 'rich'
    if request.method == 'POST':
        form = ScoreboardForm(request.POST)
        ranking_type = form.data['ranking_type']
    print ranking_type
    context['rankings'] = find_ranking(ranking_type)
    context['scoreboard_form'] = form
    context['ranking_type'] = ranking_type
    if not form.is_valid():
        return render(request, 'scoreboard.html', context)
    return render(request, 'scoreboard.html', context)
