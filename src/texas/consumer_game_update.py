import json
import logging
from channels import Group, Channel
from channels.sessions import channel_session
from texas.models import *
from django.contrib.auth.models import User
from django.core import serializers
from channels.asgi import get_channel_layer
import deuces

log = logging.getLogger(__name__)


def player_add(game, user, channel_layer):
    # -----------------Send a ws for adding a new player---------------
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

    # Add a new player to the game group
    Group('bet-' + game.game_no, channel_layer=channel_layer).send({"text": json.dumps(data)})
