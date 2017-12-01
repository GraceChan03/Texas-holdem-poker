import logging

from channels import Group
from channels.sessions import channel_session

from texas import consumer_round_update, consumer_game_update
from texas.models import *

log = logging.getLogger(__name__)


@channel_session
def ws_connect(message):
    # A. Extract the room from the message.
    # This expects message.path to be of the form /bet/{label}/,
    # and finds a Room if the message path is applicable, and if the Room exists.
    # Otherwise, bails (meaning this is a some othersort of websocket).
    # So, this is effectively a version of _get_object_or_404.
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

    # Serve the channel details to the channel_session
    message.channel_session['bet'] = game.game_no
    message.channel_session['userid'] = userid

    # add the connecting user info to channel
    try:
        user = User.objects.get(id=userid)
    except User.DoesNotExist:
        log.debug('no userid=%s', userid)

    # Send a ws for [PLAYER-ADD]
    consumer_game_update.player_add(game, user, message.channel_layer)

    # When the game is full, start a new game_round
    if game.is_full():
        consumer_round_update.start_new_round(game, message.channel_layer)


@channel_session
def ws_receive(message):
    # Parse the [BET] socket

    # A. Look up the room from the channel session, bailing if it doesn't exist
    try:
        game_no = message.channel_session['bet']
        game = Game.objects.get(game_no=game_no)
    except KeyError:
        log.debug('no game room number in channel_session')
        return
    except Game.DoesNotExist:
        log.debug('received game room number, but room does not exist. game number=%s', game_no)
        return

    # B. Look up the user from the channel session, bailing if it doesn't exist
    try:
        userid = message.channel_session['userid']
        user = User.objects.get(id=userid)
    except KeyError:
        log.debug('no player id in channel_session')
        return
    except User.DoesNotExist:
        log.debug('received player id, but player does not exist. player id=%s', userid)
        return

    # C. Parse out a message from the content text, bailing if it doesn't
    # conform to the expected message format.
    try:
        data = json.loads(message['text'])  # !!! change to specific html label
    except ValueError:
        log.debug("ws message isn't json text=%s", message['text'])
        return

    # D. Check the keys conform or not
    if set(data.keys()) != set(('message_type', 'bet', 'round_id')):  # !!! change to specific html label
        log.debug("ws message unexpected format data=%s", data)
        return

    if data:
        log.debug('bet room=%s message_type=%s bet=%s',
                  game.game_no, data['message_type'], data['bet'])

        # 1. Check message type is bet or not
        message_type = data['message_type']
        if message_type != 'bet':
            log.debug("ws message_type isn't bet message_type=%s", message_type)
            return

        # 2. Read data json details
        bet = data['bet']
        round_id = data['round_id']
        game_round = GameRound.objects.get(id=round_id)

        # 3. Get init data
        min_bet = game_round.min_bet
        op = ""
        # 4. Perform different operation
        # FOLD
        if bet == -1:
            # a. modify db
            op = "folds"
            game_round.set_player_inactive(userid)
            game_round.save()
            # b. check if one active users
            active_user = game_round.only_active_user()
            if active_user:
                # b1. set winner
                winner_id = active_user
                winner = User.objects.get(id=winner_id).username

                # b2. Send a new WS for [SHOW-Result-CARD]
                consumer_round_update.game_over(game, game_round, winner, message.channel_layer)

                return
        # CHECK
        elif bet == 0:
            # don't need to change pot, min_bet, max_player
            # check if eligible for check?
            user_prev_bet = int(game_round.get_player_prev_bet(userid))
            if user_prev_bet != min_bet:
                log.debug("user %s previous bet: %s; global_min_bet: %s; not conformed", userid, user_prev_bet, min_bet)
                return
            else:
                op = "checks"
        # BET
        else:
            op = "bets"
            # a. change pot and min_bet
            game_round.set_player_prev_bet(userid, bet)
            # b. change max_player
            if min_bet < bet:
                # change min_bet
                min_bet = bet
                game_round.current_max_player = userid
            game_round.save()

        # 5. Update the previous user's fund
        consumer_round_update.fund_update(game, game_round, user, op, min_bet, message.channel_layer)

        # 6. Find out next approach (in the same approach, or go back to the first user?):
        # A. Is this the last one of the player order?
        # If yes: go to the first one
        # If no: go the the next one
        player_order = eval(game_round.player_order)
        if int(userid) == int(player_order[-1]):
            next_index = 0
        else:
            next_index = player_order.index(int(userid)) + 1
        next_user_id = player_order[next_index]

        # B. Is this the first player with max bet?
        # B1. If no, let next player bet (ws [PLAYER-ACTION])
        # B2. If yes, check if we should go to next approach, add-dealer-card
        if next_user_id != game_round.current_max_player:
            # Send a new ws for [PLAYER-ACTION]
            try:
                next_user = User.objects.get(id=next_user_id)
            except User.DoesNotExist:
                log.debug('next player does not exist. player id=%s', next_user_id)
                return
            consumer_round_update.player_action(game, game_round, next_user, message.channel_layer)
        else:
            # This is the first player with max bet.
            next_user_id = player_order[0]

            # Reset the max to the first user(in case everyone checks in the following game)
            game_round.current_max_player = next_user_id
            game_round.save()

            # Is this the final approach?
            # If yes, show result
            # If no, send dealer card and let the small blind bet first.
            if game_round.current_approach == 5:
                # Send a new ws for [SHOW-Result-CARD]
                winner_id = game_round.get_winner()
                winner = User.objects.get(id=winner_id).username
                consumer_round_update.game_over(game, game_round, winner, message.channel_layer)
                return
            else:
                # end of current approach, add dealer card
                game_round.increment_current_approach_by_1()
                game_round.save()
                # a new ws for [ADD-DEALER-CARD]
                consumer_round_update.add_dealer_card(game, game_round, message.channel_layer)

                # Send a new ws for [PLAYER-ACTION] to small blind
                try:
                    next_user = User.objects.get(id=next_user_id)
                except User.DoesNotExist:
                    log.debug('next player does not exist. player id=%s', next_user_id)
                    return
                # If next one is not the max player, go to player-action
                # Else go to next approach, add-dealer-card
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
