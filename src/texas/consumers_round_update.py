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


# Start a new game round
def start_new_round(game, channel_layer):

    # 1. Set minimum bet
    half_min = 1
    new_game_round = GameRound(game=game, min_bet=half_min)

    # 2. Save a new round into db
    # TODO: if full
    # game.init_fund_dict()
    game.save()
    new_game_round.start()
    new_game_round.save()

    # 3. Send a new ws for [NEW-GAME]
    new_game(game, new_game_round)

    # 4. Get player order
    player_order = new_game_round.player_order
    player_order_list_round = eval(player_order)

    # 5. Check the length to see who is the next user
    if len(player_order_list_round) >= 3:
        next_user_id = player_order_list_round[2]
    elif len(player_order_list_round) == 2:
        next_user_id = player_order_list_round[0]
    else:
        # Stop the game
        # Actually can pause the game and wait for the user to enter
        log.debug('player number less than 2')
        return

    # 6. Find out next user
    try:
        next_user = User.objects.get(id=next_user_id)
    except User.DoesNotExist:
        log.debug('next player does not exist. player id=%s', next_user_id)
        return

    # 7. Send a new ws for [PLAYER-ACTION]
    player_action(game, new_game_round, next_user, channel_layer)


# Send cards separately to users to init the game  round
def new_game(game, game_round):
    # Init
    members = get_channel_layer().group_channels('bet-' + game.game_no)

    # -------- Send a new ws for [NEW-GAME] ---------
    player_order = game_round.player_order
    player_order_list_round = eval(player_order)

    # Send all the cards
    new_game_dict = {}
    new_game_dict['message_type'] = "round-update"
    new_game_dict['event'] = "new-game"
    new_game_dict['round_id'] = game_round.id
    dealer = player_order_list_round[-1]
    new_game_dict['dealer_id'] = dealer
    new_game_dict['player_order'] = player_order
    player_funds = eval(game_round.player_fund_dict)
    new_game_dict['player_funds'] = json.dumps(player_funds)

    # --------new/send cards separately--------
    if game_round.player_cards and game_round.player_cards != '':
        player_dict = eval(game_round.player_cards)
    else:
        player_dict = {}
    for player in player_dict:
        cards = []
        for card in player_dict[player]:
            cards.append(deuces.Card.int_to_str(int(card)))
        player_dict[player] = cards

    for i in xrange(len(members)):
        ch = members[i]
        user = player_order_list_round[i]
        player_cards = player_dict[user]
        new_game_dict['player_cards'] = player_cards

        Channel(ch).send({"text": json.dumps(new_game_dict)})


def player_action(game, game_round, next_user, channel_layer):
    player = {}
    player['userid'] = next_user.id
    player['username'] = next_user.username
    if game_round.player_fund_dict and game_round.player_fund_dict != '':
        player_funds_dict = eval(game_round.player_fund_dict)
    else:
        player_funds_dict = {}
    player_money = player_funds_dict[next_user.id]
    player['money'] = player_money
    if game_round.player_bet_dict and game_round.player_bet_dict != '':
        prev_bet_dict = eval(game_round.player_bet_dict)
    else:
        prev_bet_dict = {}

    prev_bet = prev_bet_dict[next_user.id]

    player_action_dict = {}
    player_action_dict['message_type'] = "round-update"
    player_action_dict['event'] = "player-action"
    player_action_dict['round_id'] = game_round.id
    player_action_dict['player'] = player
    player_action_dict['action'] = "bet"
    player_action_dict['min_bet'] = game_round.min_bet
    player_action_dict['max_bet'] = player['money'] + prev_bet
    player_action_dict['pot'] = game_round.pot

    # Tell everyone it's whose turn
    Group('bet-' + game.game_no, channel_layer=channel_layer).send({"text": json.dumps(player_action_dict)})


def fund_update(game, game_round, user, op, bet, channel_layer):
    # ---------------get fund-------------
    if game_round.player_fund_dict and game_round.player_fund_dict != '':
        funds = eval(game_round.player_fund_dict)
    else:
        funds = {}

    # ----------------Update the previous user's fund
    prev_player_update_dict = {
        "message_type": "round-update",
        "event": "fund-update",
        "round_id": game_round.id,
        "prev_player":
            {
                "userid": user.id,
                "fund": funds[user.id],
                "op": op,
                "bet": bet
            }
    }
    Group('bet-' + game.game_no, channel_layer=channel_layer).send(
        {"text": json.dumps(prev_player_update_dict)})


def add_dealer_card(game, game_round, channel_layer):
    # -----------Send a new ws for [ADD-DEALER-CARD] ---------
    add_dealer_card_message = {}
    add_dealer_card_message['message_type'] = "round-update"
    add_dealer_card_message['event'] = "add-dealer-card"

    # Deal cards
    dealer_cards = eval(game_round.dealer_cards)
    cards = []
    for card in dealer_cards:
        cards.append(deuces.Card.int_to_str(int(card)))

    if game_round.current_approach == 3:
        add_dealer_card_message['dealer_cards'] = cards[:3]
    elif game_round.current_approach == 4:
        add_dealer_card_message['dealer_cards'] = cards[3]
    elif game_round.current_approach == 5:
        add_dealer_card_message['dealer_cards'] = cards[4]

    # Tell client to add a card
    Group('bet-' + game.game_no, channel_layer=channel_layer).send(
        {"text": json.dumps(add_dealer_card_message)})


def showdown(game, game_round, channel_layer):
    showdown_message = {}
    showdown_message['message_type'] = "round-update"
    showdown_message['event'] = "showdown"
    cards = []
    if game_round.player_active_dict and game_round.player_active_dict != '':
        player_active_dict = eval(game_round.player_active_dict)
    else:
        player_active_dict = {}
    if game_round.player_cards and game_round.player_cards != '':
        player_cards = eval(game_round.player_cards)
    else:
        player_cards = {}

    for player in player_active_dict:
        # If active, add the user and the card to the result
        if player_active_dict[player]:
            # Parse the cards
            curt_player_cards = player_cards[player]
            player_cards_parsed = []
            for card in curt_player_cards:
                player_cards_parsed.append(deuces.Card.int_to_str(int(card)))
            user_cards = {}
            user_cards['id'] = player
            user_cards['card'] = player_cards_parsed
            cards.append(user_cards)
    showdown_message['cards'] = json.dumps(cards)
    # Tell client the active users
    Group('bet-' + game.game_no, channel_layer=channel_layer).send(
        {"text": json.dumps(showdown_message)})


def game_over(game, game_round, winner, channel_layer):
    end_round_message = {}
    end_round_message['message_type'] = "round-update"
    end_round_message['event'] = "game-over"
    end_round_message['winner'] = winner

    # Tell client the game is over
    Group('bet-' + game.game_no, channel_layer=channel_layer).send(
        {"text": json.dumps(end_round_message)})

    # Make the game_round inactive
    game_round.is_active = False
    game_round.save()


def game_over_then_start_new_game(game, game_round, winner, channel_layer):
    # Update winner's round balance
    # ---------------get fund-------------
    if game_round.player_fund_dict and game_round.player_fund_dict != '':
        round_funds = eval(game_round.player_fund_dict)
    else:
        round_funds = {}
    round_funds[winner.id] += game_round.pot
    game_round.player_fund_dict = str(round_funds)
    game_round.save()

        # Update all user's game balance
    game.player_fund_dict = game_round.player_fund_dict
    game.save()
    game_over(game, game_round, winner.username, channel_layer)

    start_new_round(game, channel_layer)


def fold_action(game, game_round, user, min_bet, channel_layer):
    # a. modify db
    op = "folds"
    game_round.set_player_inactive(user.id)
    game_round.save()
    # b. check if one active users
    active_user = game_round.only_active_user()
    if active_user:
        # b1. set winner
        winner_id = active_user
        winner = User.objects.get(id=winner_id)

        # b2. Update the previous user's fund
        # TODO [Handle] maybe don't return here, and if not return, don't send this websocket
        fund_update(game, game_round, user, op, min_bet, channel_layer)

        # b3. Send a new WS for [SHOW-Result-CARD]
        game_over_then_start_new_game(game, game_round, winner, channel_layer)

        return
