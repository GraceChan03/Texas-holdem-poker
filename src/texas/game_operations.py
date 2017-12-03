import logging

from texas.models import *

log = logging.getLogger(__name__)


def remove_user_from_gameround(game, game_round, user):
    # 1. update his game fund from round fund as he is to exit
    if game_round.player_fund_dict and game.player_fund_dict != '':
        round_funds = eval(game_round.player_fund_dict)
    else:
        round_funds = {}
    round_balance = round_funds[user.id]
    if game.player_fund_dict and game.player_fund_dict != '':
        game_funds = eval(game.player_fund_dict)
    else:
        game_funds = {}
    game_funds[str(user.id)] = round_balance
    game.player_fund_dict = str(game_funds)

    # 2. Set this person inactive from this game round
    game_round.set_player_inactive(user.id)

    game_round.save()
    game.save()


def remove_user_from_game(game, user):
    # 1. Modify player order
    player_order = game.player_order.split(",")
    game.player_order = str(player_order.remove(str(user.id)))
    # 2. Remove the relationship
    game.players.remove(user)
    # 3. Give back and update this person's balance
    if game.player_fund_dict and game.player_fund_dict != '':
        funds = eval(game.player_fund_dict)
    else:
        funds = {}
    round_balance = funds[user.id]
    user.userinfo.balance += round_balance

    game.save()
    user.userinfo.save()


