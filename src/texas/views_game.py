# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from datetime import date
from django.contrib import auth
from django.urls import reverse

from texas.forms import *
from texas.models import *
from haikunator import Haikunator

@login_required(login_url='login')
def new_game(request):
    context = {}
    user = request.user
    # edit here

    if request.method == 'GET':
        return render(request, 'new_game.html', context)
    else:
        # new a game
        # validate input ???
        entry_funds = request.POST['entry_funds']
        no_players = request.POST['no_players']
        haikunator = Haikunator()
        game_no = haikunator.haikunate()
        new_game = Game(creator=request.user, player_num=no_players, entry_funds=entry_funds, game_no=game_no)
        new_game.save()
        new_game.players.add(request.user)
        # new socket here?
        return render(request, 'game_init_success.html',{"game_no": game_no, "entry_funds": entry_funds, "players": no_players})


# @login_required(login_url='login')
def dashboard(request):
    context = {}
    user = request.user
    # edit here
    return render(request, 'dashboard.html', context)
# @login_required(login_url='login')
def myfriends(request):
    context = {}
    user = request.user
    # edit here
    return render(request, 'myfriends.html', context)

# @login_required(login_url='login')
def scoreboard(request):
    context = {}
    user = request.user
    # edit here
    return render(request, 'scoreboard.html', context)

# @login_required(login_url='login')
def search_friend(request):
    context = {}
    user = request.user
    # edit here
    return render(request, 'search_friend.html', context)

# @login_required(login_url='login')
def game_join(request):
    context = {}
    user = request.user
    # edit here
    return render(request, 'game_join.html', context)


# @login_required(login_url='login')
def game_ongoing(request):
    context = {}
    user = request.user
    # edit here
    return render(request, 'game_ongoing.html', context)

# @login_required(login_url='login')
def game_result(request):
    context = {}
    user = request.user
    # edit here
    return render(request, 'game_result.html', context)