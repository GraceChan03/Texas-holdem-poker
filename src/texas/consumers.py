import json
import logging
from channels import Group
from channels.sessions import channel_session
from texas.models import Game

log = logging.getLogger(__name__)


@channel_session
def ws_connect(message):
    # Extract the room from the message. This expects message.path to be of the
    # form /chat/{label}/, and finds a Room if the message path is applicable,
    # and if the Room exists. Otherwise, bails (meaning this is a some othersort
    # of websocket). So, this is effectively a version of _get_object_or_404.
    try:
        prefix, game_no = message['path'].decode('ascii').strip('/').split('/')
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
    Group('bet-' + game_no, channel_layer=message.channel_layer).add(message.reply_channel)

    message.channel_session['bet'] = game.game_no


@channel_session
def ws_receive(message):
    # Look up the room from the channel session, bailing if it doesn't exist
    try:
        game_no = message.channel_session['bet']
        game = Game.objects.get(game_no=game_no)
    except KeyError:
        log.debug('no bet in channel_session')
        return
    except Game.DoesNotExist:
        log.debug('recieved game room number, but room does not exist. room number=%s', game_no)
        return

    # Parse out a chat message from the content text, bailing if it doesn't
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
