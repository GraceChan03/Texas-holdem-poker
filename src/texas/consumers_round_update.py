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
    new_game_dict['player_funds'] = game_round.player_fund_dict

    # --------new/send cards separately--------
    player_dict = json.loads(game_round.player_cards)
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


def player_action(game, game_round, next_user, channel_layer):
    player = {}
    player['userid'] = next_user.id
    player['username'] = next_user.username
    player_funds_dict = json.loads(game_round.player_fund_dict)
    player_money = player_funds_dict[str(next_user.id)]
    player['money'] = player_money
    prev_bet_dict = json.loads(game_round.player_bet_dict)
    prev_bet = prev_bet_dict[str(next_user.id)]

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
    funds = json.loads(game_round.player_fund_dict)

    # ----------------Update the previous user's fund
    prev_player_update_dict = {
        "message_type": "round-update",
        "event": "fund-update",
        "round_id": game_round.id,
        "prev_player":
            {
                "userid": user.id,
                "fund": funds[str(user.id)],
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
    dealer_string = str(game_round.dealer_cards)
    cards = []
    for card in dealer_string.split(','):
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
    player_active_dict = json.loads(game_round.player_active_dict)
    player_cards = json.loads(game_round.player_cards)

    for player in player_active_dict:
        # If active, add the user and the card to the result
        if player_active_dict[player]:
            cards_str = eval(player_cards[player])
            user_cards = {player:cards_str}
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

    # Tell client to add a card
    Group('bet-' + game.game_no, channel_layer=channel_layer).send(
        {"text": json.dumps(end_round_message)})

