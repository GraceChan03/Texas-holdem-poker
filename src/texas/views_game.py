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

@login_required(login_url='login')
def game_join(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'game_join.html')
    # edit here
    game_no = request.POST['room_number']
    if not Game.objects.filter(game_no=game_no):
        return render(request, 'game_join.html', {'room_no_error': 'The room number does not exist'})
    # before add user into game room, check if he/she has sufficient balance
    game = Game.objects.get(game_no=game_no)
    if not game.players.filter(username=request.user.username) and \
                    game.player_num == game.players.count():
        return render(request, 'game_join.html', {'room_full_error': 'The room is full'})
    if not game.players.filter(username=request.user.username):
        game.players.add(request.user)
    return redirect("/game_ongoing/" + game_no)

@login_required(login_url='login')
def game_ongoing(request, game_no):
    context = {}
    # edit here
    context['game_no'] = game_no
    context['login_user'] = request.user
    players = Game.objects.get(game_no=game_no).players.all()
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
def game_result(request):
    context = {}
    user = request.user
    # edit here
    return render(request, 'game_result.html', context)