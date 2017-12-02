# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from datetime import date
from django.contrib import auth
from django.urls import reverse

from texas.forms import *
from texas.models import *
from haikunator import Haikunator

import logging

log = logging.getLogger(__name__)

@login_required(login_url='login')
def new_game(request):
    context = {}
    context['searchForm'] = SearchUser()
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
        new_game = Game(creator=request.user, player_num=no_players, entry_funds=entry_funds, game_no=game_no, player_order=request.user.id
        )
        new_game.save()
        new_game.players.add(request.user)
        # new socket here?
        return render(request, 'game_init_success.html',{"game_no": game_no, "entry_funds": entry_funds, "players": no_players})

@login_required(login_url='login')
def game_join(request):
    context = {}
    context['searchForm'] = SearchUser()
    if request.method == 'GET':
        context['join_room_form'] = JoinRoomForm()
        return render(request, 'game_join.html', context)

    form = JoinRoomForm(request.POST, username=request.user.username)
    context['join_room_form'] = form
    if not form.is_valid():
        return render(request, 'game_join.html', context)
    game_no = form.cleaned_data['room_number']
    game = Game.objects.get(game_no=game_no)
    game.player_order = game.player_order + ',' + str(request.user.id)
    game.save()

    if not game.players.filter(username=request.user.username):
        game.players.add(request.user)
    return redirect("/game_ongoing/" + game_no)

@login_required(login_url='login')
def game_ongoing(request, game_no):
    context = {}
    context['searchForm'] = SearchUser()
    # Update the user's balance for entry funds
    game = Game.objects.get(game_no=game_no)
    if request.user.userinfo.balance < game.entry_funds:
        # TODO 进入游戏fund不够时不会提示，需要改html，或者弄form
        log.debug('user %s fund insufficient', request.user.id)
        # Make the user not able to enter
        return render(request, 'new_game.html', context)
    # decrease fund
    request.user.userinfo.balance -= game.entry_funds
    request.user.userinfo.save()

    context['game_no'] = game_no
    context['login_user'] = request.user
    players = game.players.all()
    context['players'] = players
    return render(request, 'game_ongoing.html', context)

@login_required(login_url='login')
def exit_room(request, game_no, id):
    player = get_object_or_404(User, id=id)
    game = get_object_or_404(Game, game_no=game_no)
    game.players.remove(player)

# @login_required(login_url='login')
def dashboard(request):
    context = {}
    context['searchForm'] = SearchUser()
    user = request.user
    # edit here
    return render(request, 'dashboard.html', context)
# @login_required(login_url='login')
def myfriends(request):
    context = {}
    context['searchForm'] = SearchUser()
    user = request.user
    # edit here
    return render(request, 'myfriends.html', context)

# @login_required(login_url='login')
def scoreboard(request):
    context = {}
    context['searchForm'] = SearchUser()
    user = request.user
    # edit here
    return render(request, 'scoreboard.html', context)

# @login_required(login_url='login')
def search_friend(request):
    context = {}
    if request.method == 'GET':
        context['searchForm'] = SearchUser()
        return render(request, 'search_friend.html', context)

    form = SearchUser(request.POST)
    context['searchForm'] = form
    if not form.is_valid():
        return render(request, "search_friend.html", context)
    keyword = form.cleaned_data['keyword']
    keyword = keyword.strip()
    if keyword == '':
        users = User.objects.all()
        context['users'] = users
        return render(request, 'search_friend.html', context)
    users = User.objects.filter(username__icontains=keyword)
    context['users'] = users
    # edit here
    return render(request, 'search_friend.html', context)

# @login_required(login_url='login')
def game_result(request):
    context = {}
    context['searchForm'] = SearchUser()
    user = request.user
    # edit here
    return render(request, 'game_result.html', context)