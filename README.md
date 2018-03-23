This is an online texas holdem poker game implementing using Django.

### Project Name: webapps
### App Name: texas

##### Requirements
```
pip install django
pip install channels
pip install psycopg2
pip install postgres
pip install twisted
pip install pyopenssl
pip install --upgrade pyopenssl
pip install -U asgi_redis
pip install pillow
pip install haikunator
pip install deuces
```
windows
```
pip install pypiwin32
```

### Techniques Used:
1. Django Channels native websocket API to update the server side
2. Use JQuery to update the client side
2. Deployed postgresQL on AWS EC2 docker DB as backend database.
3. Deployed Redis DB on AWS EC2 docker as websocket broker.

### Communication Protocol
##### Received
```json
{ 
    "message_type": "bet",
    "bet": 50
}
```
##### Sent
```json
{ 
    "message_type": "round-update",
    "event": "player-action",
    "player": {
        "id": 1,
        "username": "graceee",
        "money": 50
    },
    "action": "bet",
    "min_bet": 1,
    "max_bet": 50
}

```

### Reference 
1. [Is it possible to list channels stored in a Group?](https://stackoverflow.com/questions/39442112/is-it-possible-to-list-channels-stored-in-a-group)

2. [How to fix daphne](https://github.com/django/channels/issues/230)

3. [How to fix supervisor](https://github.com/django/channels/issues/408)

4. [How to deploy](http://channels.readthedocs.io/en/1.1.8/deploying.html)

5. [How to deploy in Chinese](https://code.ziqiangxuetang.com/django/django-static-files.html)

6. [Free Domain](http://www.freenom.com/zh/freeandpaiddomains.html)

7. [How to deploy channels](http://channels.readthedocs.io/en/latest/deploying.html)

8. [How to user supersord](http://liyangliang.me/posts/2015/06/using-supervisor/)

9. [How to log in supervisor](http://supervisord.org/logging.html)

10. [How to deploy channels with nginx](http://masnun.rocks/2016/11/02/deploying-django-channels-using-daphne/)

11. [Duplicate key in python](https://stackoverflow.com/questions/14902299/json-loads-allows-duplicate-keys-in-a-dictionary-overwriting-the-first-value)