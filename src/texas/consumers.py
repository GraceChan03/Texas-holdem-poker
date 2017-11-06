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

    if game.players.count() == game.player_num:
        new_game_round = GameRound(game=game)
        new_game_round.start()
        new_game_round.save()
        new_game_dict = {}
        new_game_dict['message_type'] = "round-update"
        new_game_dict['event'] = "new-game"
        new_game_dict['round_id'] = new_game_round.id
        player_order = new_game_round.player_order
        new_game_dict['player_order'] = player_order

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

        # Game update
        next_user_id = eval(player_order)[0]
        player = {}
        player['userid'] = next_user_id
        try:
            user = User.objects.get(id=next_user_id)
        except User.DoesNotExist:
            log.debug('player does not exist. player id=%s', next_user_id)
            return
        player['username'] = user.username
        player['money'] = game.entry_funds

        player_action_dict = {}
        player_action_dict['message_type'] = "round-update"
        player_action_dict['event'] = "player-action"
        player_action_dict['round_id'] = new_game_round.id
        player_action_dict['player'] = player
        player_action_dict['action'] = "bet"
        player_action_dict['min_bet'] = 0.0
        player_action_dict['max_bet'] = player['money']

        # Tell everyone it's whose turn
        Group('bet-' + game_no, channel_layer=message.channel_layer).send({"text": json.dumps(player_action_dict)})


@channel_session
def ws_receive(message):
    # Look up the room from the channel session, bailing if it doesn't exist
    try:
        game_no = message.channel_session['bet']
        player_id = message.channel_session['user_id']
        game = Game.objects.get(game_no=game_no)
    except KeyError:
        log.debug('no game room number in channel_session')
        return
    except Game.DoesNotExist:
        log.debug('received game room number, but room does not exist. game number=%s', game_no)
        return

    try:
        user_id = message.channel_session['user_id']
        user = User.objects.get(id=user_id)
    except KeyError:
        log.debug('no player id in channel_session')
        return
    except Game.DoesNotExist:
        log.debug('received player id, but player does not exist. player id=%s', user_id)
        return
    # Parse out a message from the content text, bailing if it doesn't
    # conform to the expected message format.

    try:
        data = json.loads(message['text'])   #!!! change to specific html label
    except ValueError:
        log.debug("ws message isn't json text=%s", message['text'])
        return

    # if set(data.keys()) != set(('handle', 'message')):    #!!! change to specific html label
    #     log.debug("ws message unexpected format data=%s", data)
    #     return

    if data:
        log.debug('bet room=%s data=%s',
                  game.game_no, data)
        m = game.messages.create(**data)

        # See above for the note about Group
        Group('bet-' + game_no, channel_layer=message.channel_layer).send({'text': json.dumps(m.as_dict())})


@channel_session
def ws_disconnect(message):
    try:
        game_no = message.channel_session['bet']
        Group('bet-' + game_no, channel_layer=message.channel_layer).discard(message.reply_channel)
    except (KeyError, Game.DoesNotExist):
        pass
