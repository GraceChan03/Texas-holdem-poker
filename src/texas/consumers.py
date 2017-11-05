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
        username = path[1]
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
    # This may be a FIXME?
    message.reply_channel.send({"accept": True})
    Group('bet-' + game_no, channel_layer=message.channel_layer).add(message.reply_channel)
    message.channel_session['bet'] = game.game_no
    # add the user info to channel
    try:
       user = User.objects.get(username=username)
    except User.DoesNotExist:
        log.debug('no username=%s', username)
        return

    data = {"photo_src": str(user.userinfo.profile_photo_src), "username": user.username}
    Group('bet-' + game_no, channel_layer=message.channel_layer).send({"text": json.dumps(data)})

    if game.players.count() == game.player_num:
        new_game_round = GameRound(game=game)
        new_game_round.start()
        new_game_round.save()
        new_game_dict = {}
        new_game_dict['message_type'] = "round-update"
        new_game_dict['round_id'] = new_game_round.id

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

        Group('bet-' + game_no, channel_layer=message.channel_layer).send({"text": json.dumps(new_game_dict)})


@channel_session
def ws_receive(message):
    # Look up the room from the channel session, bailing if it doesn't exist
    try:
        game_no = message.channel_session['room_id']
        game = Game.objects.get(game_no=game_no)
    except KeyError:
        log.debug('no game room number in channel_session')
        return
    except Game.DoesNotExist:
        log.debug('recieved game room number, but room does not exist. room number=%s', game_no)
        return


    # Parse out a message from the content text, bailing if it doesn't
    # conform to the expected message format.
    try:
        data = json.loads(message['text'])   #!!! change to specific html label
    except ValueError:
        log.debug("ws message isn't json text=%s", message['text'])
        return

    if set(data.keys()) != set(('handle', 'message')):    #!!! change to specific html label
        log.debug("ws message unexpected format data=%s", data)
        return

    if data:
        log.debug('bet room=%s handle=%s message=%s',
                  game.game_no, data['handle'], data['message'])
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
