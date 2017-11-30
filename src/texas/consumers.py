import json
import logging
from channels import Group, Channel
from channels.sessions import channel_session
from texas.models import *
from django.contrib.auth.models import User
from django.core import serializers
from channels.asgi import get_channel_layer
import deuces

from texas import consumer_round_update, consumer_game_update

log = logging.getLogger(__name__)


@channel_session
def ws_connect(message):
    # Extract the room from the message. This expects message.path to be of the
    # form /bet/{label}/, and finds a Room if the message path is applicable,
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
    members = get_channel_layer().group_channels('bet-' + game_no)

    message.channel_session['bet'] = game.game_no
    message.channel_session['userid'] = userid

    # add the user info to channel
    try:
        user = User.objects.get(id=userid)
    except User.DoesNotExist:
        log.debug('no userid=%s', userid)

    # -----------------Send a ws for adding a new player---------------
    consumer_game_update.player_add(game, user, message.channel_layer)

    # When the game is full, start a new game_round
    if game.is_full():

        # Set minimum bet
        half_min = 1
        new_game_round = GameRound(game=game, min_bet=2*half_min)
        # Start a new round
        new_game_round.start()
        new_game_round.save()

        # -------- Send a new ws for [NEW-GAME] ---------
        consumer_round_update.new_game(game, new_game_round)

        # ----------- Send a new ws for [PLAYER-ACTION] ----------
        player_order = new_game_round.player_order
        player_order_list_round = eval(player_order)

        if len(player_order_list_round) >= 3:
            next_user_id = player_order_list_round[2]
        else:
            next_user_id = player_order_list_round[0]

        try:
            next_user = User.objects.get(id=next_user_id)
        except User.DoesNotExist:
            log.debug('next player does not exist. player id=%s', next_user_id)
            return
        consumer_round_update.player_action(game, new_game_round, next_user, message.channel_layer)



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
        data = json.loads(message['text'])  # !!! change to specific html label
    except ValueError:
        log.debug("ws message isn't json text=%s", message['text'])
        return

    if set(data.keys()) != set(('message_type', 'bet', 'round_id')):  # !!! change to specific html label
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
        op = ""
        # Fold
        if bet == -1:
            op = "folds"
            game_round.set_player_inactive(userid)
            game_round.save()
            # check if one active users
            active_user = game_round.only_active_user()
            if active_user:
                # set winner
                # -----------Send a new ws for [SHOW-Result-CARD] ---------
                winner_id = active_user
                winner = User.objects.get(id=winner_id).username

                consumer_round_update.game_over(game, game_round, winner, message.channel_layer)

                return

        # Check
        elif bet == 0:
            op = "checks"
            # don't need to change pot, min_bet
            min_bet = int(game_round.get_player_prev_bet(userid))
        # bet sth
        else:
            op = "bets"
            # change min_bet
            # TODO
            min_bet = bet
            # change pot
            game_round.set_player_prev_bet(userid, bet)
            game_round.save()

        # ----------------Update the previous user's fund
        consumer_round_update.fund_update(game, game_round, user, op, bet, message.channel_layer)

        # Judge if this is the end of the round:
        player_order = eval(game_round.player_order)
        curt_index = player_order.index(int(userid))
        next_index = curt_index + 1
        if next_index == game.player_num:
            next_index = 0
            # This is the end of a round
            #     show result
            if game_round.current_approach == 5:

                #   end of current approach, add dealer card
                # -----------Send a new ws for [SHOW-Result-CARD] ---------
                winner_id = game_round.get_winner()
                winner = User.objects.get(id=winner_id).username
                consumer_round_update.game_over(game, game_round, winner, message.channel_layer)
                return

            else:
                #   end of current approach, add dealer card
                game_round.increment_current_approach_by_1()
                game_round.save()
                # -----------Send a new ws for [ADD-DEALER-CARD] ---------
                consumer_round_update.add_dealer_card(game, game_round, message.channel_layer)

                # ----------- Send a new ws for [PLAYER-ACTION] ----------
                next_user_id = player_order[next_index]

                try:
                    next_user = User.objects.get(id=next_user_id)
                except User.DoesNotExist:
                    log.debug('next player does not exist. player id=%s', next_user_id)
                    return
                consumer_round_update.player_action(game, game_round, next_user, message.channel_layer)

        else:
            #     This is not the end

            # ----------- Send a new ws for [PLAYER-ACTION] ----------
            next_user_id = player_order[next_index]

            try:
                next_user = User.objects.get(id=next_user_id)
            except User.DoesNotExist:
                log.debug('next player does not exist. player id=%s', next_user_id)
                return

            consumer_round_update.player_action(game, game_round, next_user, message.channel_layer)


@channel_session
def ws_disconnect(message):
    try:
        game_no = message.channel_session['bet']
        userid = message.channel_session['userid']
        Group('bet-' + game_no, channel_layer=message.channel_layer).discard(message.reply_channel)

    except (KeyError, Game.DoesNotExist):
        log.debug('ws room does not exist label=%s', game_no)
        return

    # Remove current user from database

    # ----------- Send a new ws for [PLAYER-ACTION] ----------
    consumer_game_update.player_remove(game_no, userid, message.channel_layer)
