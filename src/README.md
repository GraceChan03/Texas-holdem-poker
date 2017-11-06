Please complete all your project development in this directory and 
its subdirectories (which you may create as neeeded).

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
