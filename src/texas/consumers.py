import json
import logging
from channels import Group
from channels.sessions import channel_session
from texas.models import *
from django.contrib.auth.models import User
from django.core import serializers
import deuces

log = logging.getLogger(__name__)


@channel_session
def ws_connect(message):
    # Extract the room from the message. This expects message.path to be of the
    # form /chat/{label}/, and finds a Room if the message path is applicable,
    # and if the Room exists. Otherwise, bails (meaning this is a some othersort
    # of websocket). So, this is effectively a version of _get_object_or_404.
    try:
        path = message['path'].strip('/').split('/')
        prefix = path[0]
        userid = path[1]
        game_no = path[-1]
        if prefix != 'bet':
            log.debug('invalid ws path=%s', message['path'])
            return
        game = Game.objects.get(game_no=game_no)
    except ValueError:
        log.debug('invalid ws path=%s', message['path'])
        return
    except Game.DoesNotExist:
        log.debug('ws room does not exist label=%s', game_no)
        return

    # Need to be explicit about the channel layer so that testability works
    message.reply_channel.send({"accept": True})
    Group('bet-' + game_no, channel_layer=message.channel_layer).add(message.reply_channel)
    message.channel_session['bet'] = game.game_no
    message.channel_session['userid'] = userid
    # add the user info to channel
    try:
       user = User.objects.get(id=userid)
    except User.DoesNotExist:
        log.debug('no userid=%s', userid)
    
    data = {"photo_src": str(user.userinfo.profile_photo_src),
            "username": user.username,
            "userid": user.id,
            "message_type": "game-update",
            "event": "player-add"}
    Group('bet-' + game_no, channel_layer=message.channel_layer).send({"text": json.dumps(data)})

    # when the players' number match the set player num
    if game.players.count() == game.player_num:
        new_game_round = GameRound(game=game)
        # Start a new round
        new_game_round.start()
        # Do this if this is the first round
        new_game_round.set_player_entry_funds_dict()
        new_game_round.save()

        # -------- Send a new ws for [NEW-GAME] ---------
        new_game_dict = {}
        new_game_dict['message_type'] = "round-update"
        new_game_dict['event'] = "new-game"
        new_game_dict['round_id'] = new_game_round.id
        player_order = new_game_round.player_order
        new_game_dict['player_order'] = player_order
        new_game_dict['player_funds'] = new_game_round.player_fund_dict

        dealer_string = str(new_game_round.dealer_cards)
        dealer_pretty_string = ''
        for card in dealer_string.split(','):
            dealer_pretty_string += deuces.Card.int_to_str(int(card)) + ','

        new_game_dict['dealer_cards'] = dealer_pretty_string[:-1]

        player_dict = json.loads(new_game_round.player_cards)
        for player in player_dict:
            cards = []
            for card in player_dict[player]:
                cards.append(deuces.Card.int_to_str(int(card)))
            player_dict[player] = cards
        new_game_dict['player_cards'] = player_dict

        # Send cards to everyone
        Group('bet-' + game_no, channel_layer=message.channel_layer).send({"text": json.dumps(new_game_dict)})
        # message.channel_session['round_id'] = new_game_round.id

        # ----------- Send a new ws for [PLAYER-ACTION] ----------
        next_user_id = eval(player_order)[0]
        player = {}
        player['userid'] = next_user_id
        try:
            next_user = User.objects.get(id=next_user_id)
        except User.DoesNotExist:
            log.debug('next player does not exist. player id=%s', next_user_id)
            return
        player['username'] = next_user.username
        player_funds_dict = json.loads(new_game_round.player_fund_dict)
        player_money = player_funds_dict[str(next_user_id)]
        player['money'] = player_money

        player_action_dict = {}
        player_action_dict['message_type'] = "round-update"
        player_action_dict['event'] = "player-action"
        player_action_dict['round_id'] = new_game_round.id
        player_action_dict['player'] = player
        player_action_dict['action'] = "bet"
        player_action_dict['min_bet'] = new_game_round.min_bet
        player_action_dict['max_bet'] = player['money']

        # Tell everyone it's whose turn
        Group('bet-' + game_no, channel_layer=message.channel_layer).send({"text": json.dumps(player_action_dict)})


@channel_session
def ws_receive(message):
    # Look up the room from the channel session, bailing if it doesn't exist
    try:
        game_no = message.channel_session['bet']
        game = Game.objects.get(game_no=game_no)
    except KeyError:
        log.debug('no game room number in channel_session')
        return
    except Game.DoesNotExist:
        log.debug('received game room number, but room does not exist. game number=%s', game_no)
        return

    try:
        userid = message.channel_session['userid']
        user = User.objects.get(id=userid)
    except KeyError:
        log.debug('no player id in channel_session')
        return
    except User.DoesNotExist:
        log.debug('received player id, but player does not exist. player id=%s', userid)
        return

    # Parse out a message from the content text, bailing if it doesn't
    # conform to the expected message format.
    try:
        data = json.loads(message['text'])   #!!! change to specific html label
    except ValueError:
        log.debug("ws message isn't json text=%s", message['text'])
        return

    if set(data.keys()) != set(('message_type', 'bet', 'round_id')):    #!!! change to specific html label
        log.debug("ws message unexpected format data=%s", data)
        return

    if data:
        log.debug('bet room=%s message_type=%s bet=%s',
                  game.game_no, data['message_type'], data['bet'])

        message_type = data['message_type']
        if message_type != 'bet':
            log.debug("ws message_type isn't bet message_type=%s", message_type)
            return

        bet = data['bet']
        round_id = data['round_id']
        game_round = GameRound.objects.get(id=round_id)
        min_bet = game_round.min_bet
        # Fold
        if bet == -1:
            game_round.set_player_inactive(userid)
            game_round.save()
            # check if one active users
            active_user = game_round.only_active_user()
            if active_user:
                # set winner
                # -----------Send a new ws for [SHOW-Result-CARD] ---------
                end_round_message = {}
                end_round_message['message_type'] = "round-update"
                end_round_message['event'] = "game-over"
                winner_id = active_user
                winner = User.objects.get(id=winner_id).username
                end_round_message['winner'] = winner

                # Tell client to add a card
                Group('bet-' + game_no, channel_layer=message.channel_layer).send(
                    {"text": json.dumps(end_round_message)})

        # Check
        elif bet == 0:
        # don't need to change pot, min_bet
            pass
        # bet sth
        else:
            # change min_bet
            # TODO
            min_bet = bet
            # change pot

        # Judge if this is the end of the round:
        player_order = eval(game_round.player_order)
        curt_index = player_order.index(int(userid))
        next_index = curt_index + 1
        if next_index == game.player_num:
            next_index = 0
            # This is the end of a round
            #     show result TODO
            if game_round.current_approach == 5:

                #   end of current approach, add dealer card
                # -----------Send a new ws for [SHOW-Result-CARD] ---------
                end_round_message = {}
                end_round_message['message_type'] = "round-update"
                end_round_message['event'] = "game-over"
                winner_id = game_round.get_winner()
                winner = User.objects.get(id=winner_id).username
                end_round_message['winner'] = winner

                # Tell client to add a card
                Group('bet-' + game_no, channel_layer=message.channel_layer).send(
                    {"text": json.dumps(end_round_message)})


            else:
                #   end of current approach, add dealer card
                game_round.increment_current_approach_by_1()
                game_round.save()
                # -----------Send a new ws for [ADD-DEALER-CARD] ---------
                add_dealer_card_message = {}
                add_dealer_card_message['message_type'] = "round-update"
                add_dealer_card_message['event'] = "add-dealer-card"

                # Tell client to add a card
                Group('bet-' + game_no, channel_layer=message.channel_layer).send(
                    {"text": json.dumps(add_dealer_card_message)})

                # ----------- Send a new ws for [PLAYER-ACTION] ----------
                next_user_id = player_order[next_index]
                player = {}
                player['userid'] = next_user_id
                try:
                    next_user = User.objects.get(id=next_user_id)
                except User.DoesNotExist:
                    log.debug('next player does not exist. player id=%s', next_user_id)
                    return
                player['username'] = next_user.username
                player_funds_dict = json.loads(game_round.player_fund_dict)
                player_money = player_funds_dict[str(next_user_id)]
                player['money'] = player_money

                player_action_dict = {}
                player_action_dict['message_type'] = "round-update"
                player_action_dict['event'] = "player-action"
                player_action_dict['round_id'] = round_id
                player_action_dict['player'] = player
                player_action_dict['action'] = "bet"
                player_action_dict['min_bet'] = min_bet
                player_action_dict['max_bet'] = player['money']

                # Tell everyone it's whose turn
                Group('bet-' + game_no, channel_layer=message.channel_layer).send(
                    {"text": json.dumps(player_action_dict)})

        else:
            #     This is not the end

            # ----------- Send a new ws for [PLAYER-ACTION] ----------
            next_user_id = player_order[next_index]
            player = {}
            player['userid'] = next_user_id
            try:
                next_user = User.objects.get(id=next_user_id)
            except User.DoesNotExist:
                log.debug('next player does not exist. player id=%s', next_user_id)
                return
            player['username'] = next_user.username
            player_funds_dict = json.loads(game_round.player_fund_dict)
            player_money = player_funds_dict[str(next_user_id)]
            player['money'] = player_money

            player_action_dict = {}
            player_action_dict['message_type'] = "round-update"
            player_action_dict['event'] = "player-action"
            player_action_dict['round_id'] = round_id
            player_action_dict['player'] = player
            player_action_dict['action'] = "bet"
            player_action_dict['min_bet'] = min_bet
            player_action_dict['max_bet'] = player['money']

            # Tell everyone it's whose turn
            Group('bet-' + game_no, channel_layer=message.channel_layer).send({"text": json.dumps(player_action_dict)})


@channel_session
def ws_disconnect(message):
    try:
        game_no = message.channel_session['bet']
        Group('bet-' + game_no, channel_layer=message.channel_layer).discard(message.reply_channel)
    except (KeyError, Game.DoesNotExist):
        pass
