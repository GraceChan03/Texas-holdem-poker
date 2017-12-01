import os
import channels.asgi
import sys

path = '/home/ZNYAZO/my-first-blog'  # use your own username here
if path not in sys.path:
    sys.path.append(path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webapps.settings")
channel_layer = channels.asgi.get_channel_layer()