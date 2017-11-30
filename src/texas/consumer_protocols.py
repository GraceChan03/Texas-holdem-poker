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


# Send cards separately to users to init the game  round
def send_cards(game_no, game_round_id):
    # Init
    new_game_round = GameRound.objects.get(id=game_round_id)
    game = Game.objects.get(game_no=game_no)
    members = get_channel_layer().group_channels('bet-' + game_no)

    # -------- Send a new ws for [NEW-GAME] ---------
    player_order = new_game_round.player_order
    player_order_list_round = eval(player_order)

    # Send all the cards
    new_game_dict = {}
    new_game_dict['message_type'] = "round-update"
    new_game_dict['event'] = "new-game"
    new_game_dict['round_id'] = new_game_round.id
    dealer = player_order_list_round[-1]
    new_game_dict['dealer_id'] = dealer
    new_game_dict['player_order'] = player_order
    new_game_dict['player_funds'] = new_game_round.player_fund_dict

    # --------new/send cards separately--------
    player_dict = json.loads(new_game_round.player_cards)
    for player in player_dict:
        cards = []
        for card in player_dict[player]:
            cards.append(deuces.Card.int_to_str(int(card)))
        player_dict[player] = cards

    for i in xrange(game.player_num):
        ch = members[i]
        user = str(player_order_list_round[i])
        player_cards = player_dict[user]
        new_game_dict['player_cards'] = player_cards

        Channel(ch).send({"text": json.dumps(new_game_dict)})
