import json
import logging

from channels import Group
from channels.sessions import channel_session

from texas import consumers_round_update, consumers_game_update, game_operations
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
    consumers_game_update.player_add(game, user, message.channel_layer)


    # TODO: if full and game ongoing, set the new user inactive in the current active gameround

    # When the game is full, start a new game_round
    if game.is_full():
        consumers_round_update.start_new_round(game, message.channel_layer)


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
        userid = int(userid)

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
                consumers_round_update.fund_update(game, game_round, user, op, min_bet, message.channel_layer)

                # b3. Send a new WS for [SHOW-Result-CARD]
                consumers_round_update.game_over_then_start_new_game(game, game_round, winner, message.channel_layer)

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
        # TODO [Function] Allin
        # ALLIN
        elif bet == -2:
            # don't need to change pot, min_bet, max_player
            # check if eligible for check?
            user_prev_bet = int(game_round.get_player_prev_bet(userid))
            if user_prev_bet != min_bet:
                log.debug("user %s previous bet: %s; global_min_bet: %s; not conformed", userid, user_prev_bet, min_bet)
                return
            else:
                op = "allin"

        # BET
        else:
            op = "bets"
            # a. change pot and min_bet
            game_round.set_player_prev_bet(int(userid), bet)
            # b. change max_player
            if min_bet < bet:
                # change min_bet
                min_bet = bet
                game_round.current_max_player = userid
            game_round.save()

        # 5. Update the previous user's fund
        consumers_round_update.fund_update(game, game_round, user, op, min_bet, message.channel_layer)

        # 6. Find out next approach (in the same approach, or go back to the first user?):
        consumers_round_update.next_approach(game, game_round, user, message.channel_layer)


@channel_session
def ws_disconnect(message):
    try:
        game_no = message.channel_session['bet']
        userid = message.channel_session['userid']
        game = Game.objects.get(game_no=game_no)
        user = User.objects.get(id=userid)

    except KeyError:
        log.debug('Key not exist in channel')
        return
    except Game.DoesNotExist:
        log.debug('ws room does not exist label=%s', game_no)
        return
    except User.DoesNotExist:
        log.debug('user does not exist label=%s', userid)
        return

    Group('bet-' + game_no, channel_layer=message.channel_layer).discard(message.reply_channel)

    # A. Send a new ws for [PLAYER-ACTION] to all the other users----------
    player_remove_dict = {}
    player_remove_dict["message_type"] = "game-update"
    player_remove_dict["event"] = "player-remove"
    player_remove_dict["player_id"] = user.id
    Group('bet-' + game.game_no, channel_layer=message.channel_layer).send({"text": json.dumps(player_remove_dict)})

    # B. If this person is in a game_round, (i.e. active gameround exists)
    try:
        game_round = GameRound.objects.get(game=game, is_active=True)
        if game_round:
            game_operations.remove_user_from_gameround(game, game_round, user)
            min_bet = game_round.min_bet
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
            consumers_round_update.fund_update(game, game_round, user, op, min_bet, message.channel_layer)

            # C. Remove this person from game, including update funds
            game_operations.remove_user_from_game(game, user)

            # b3. Send a new WS for [SHOW-Result-CARD]
            consumers_round_update.game_over_then_start_new_game(game, game_round, winner, message.channel_layer)

            return

        # C. Remove this person from game, including update funds
        game_operations.remove_user_from_game(game, user)
        consumers_round_update.next_approach(game, game_round, user, message.channel_layer)
    except GameRound.DoesNotExist:
        log.debug('ws game round does not exist label=%s', game.game_no)

        # C. Remove this person from game, including update funds
        game_operations.remove_user_from_game(game, user)
