import json
import logging
from channels import Group, Channel
from channels.sessions import channel_session

from texas import game_operations
from texas.models import *
from django.contrib.auth.models import User
from django.core import serializers
from channels.asgi import get_channel_layer
import deuces

log = logging.getLogger(__name__)


def player_add(game, user, channel_layer):
    # 1. Add current player to the end of player_order
    player_order = game.player_order
    if not player_order or player_order == 'None':
        game.player_order = str(user.id)
    else:
        game.player_order = game.player_order + ',' + str(user.id)

    # 2. Add curt user to fund dict
    # When the fund_dict is empty, create a dict
    if game.player_fund_dict == '':
        funds = {}
    else:
        funds = eval(game.player_fund_dict)
    funds[user.id] = game.entry_funds
    game.player_fund_dict = str(funds)

    # Save changes
    game.save()

    # 3. Decrease curt user's fund balance
    user.userinfo.balance -= game.entry_funds
    # Save changes
    user.userinfo.save()

    # 4. Add this user to the game's player
    if not game.players.filter(username=user.username):
        game.players.add(user)

    # 5. Send a ws for adding a new player---------------
    data = {}
    data["message_type"] = "game-update"
    data["event"] = "player-add"
    data["game_no"] = game.game_no
    data["player_num"] = game.player_num
    data["player_id"] = user.id
    players = []

    # Send all the users together to the client
    player_order_list = game.player_order.split(",")
    for pid in player_order_list:
        p = User.objects.get(id=pid)
        info = {}
        info["id"] = pid
        info["name"] = p.username
        info["photo_src"] = str(p.userinfo.profile_photo_src)
        info["money"] = game.entry_funds
        players.append(info)

    data["players"] = players

    # Add a new player to the game group channel
    Group('bet-' + game.game_no, channel_layer=channel_layer).send({"text": json.dumps(data)})


def player_remove(game, user, channel_layer):
    # TODO
    # A. If this person is in a game_round, (i.e. active gameround exists)
    try:
        game_round = GameRound.objects.get(game=game, is_active=True)
        if game_round:
            game_operations.remove_user_from_gameround(game, game_round, user)

    except GameRound.DoesNotExist:
        log.debug('ws game round does not exist label=%s', game.game_no)

    # B. Remove this person from game
    game_operations.remove_user_from_game(game, user)

    # C. Send a new ws for [PLAYER-ACTION] to all the other users----------
    player_remove_dict = {}
    player_remove_dict["message_type"] = "game-update"
    player_remove_dict["event"] = "player-remove"
    player_remove_dict["player_id"] = user.id
    Group('bet-' + game.game_no, channel_layer=channel_layer).send({"text": json.dumps(player_remove_dict)})