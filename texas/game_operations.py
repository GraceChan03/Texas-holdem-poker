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
    player_order = game.player_order.split(',')

    new_player_order = []
    for i in xrange(len(player_order)):
        if int(player_order[i]) != user.id:
            new_player_order.append(int(player_order[i]))

    game.player_order = str(new_player_order)[1:-1]

    game.save()

    # 2. Remove the relationship
    game.players.remove(user)
    # 3. Give back and update this person's balance
    if game.player_fund_dict and game.player_fund_dict != '':
        funds = eval(game.player_fund_dict)
    else:
        funds = {}
    round_balance = funds[user.id]
    user.userinfo.balance += round_balance

    user.userinfo.save()


def winner_history_save(game_round, user):

    # Fetch data from round info

    if game_round.player_cards and game_round.player_cards != '':
        player_cards_dict = eval(game_round.player_cards)
        user_cards = player_cards_dict[user.id]
    else:
        user_cards = ''

    bet = game_round.get_player_prev_bet(user.id)

    # 1. Create
    new_winner_history = WinnerHistory(
        game_round=game_round,
        user=user,
        dealer_cards=game_round.dealer_cards,
        user_cards=user_cards,
        current_approach=game_round.current_approach,
        pot=game_round.pot,
        bet=bet,
    )

    if game_round.current_approach == 5:
        new_winner_history.hand_rank = game_round.process_user_class()[user.id]

    new_winner_history.save()

