# Proposal

(This proposal is the same as the one was approved, except for some formatting)

An online Texas Hold’em Poker entertainment platform with extra features. The rules can be found at [Texas hold 'em - Wikipedia](https://en.wikipedia.org/wiki/Texas_hold_%27em).

#### Basic functions:
1. Account: The users may be able to create their account, login and start a game.
2. Game: 
 - Several users input a certain room id and they will be in the same game. Different games can process concurrently.
 - Each user may have an initial credit for each game, and after each round of game, the credit will be updated. After all the users agreed to exit the game, a scoreboard will be posted.

#### Possible extra features (to be discussed):
1. Credits: Redeeming coupons, recharging credits, etc.
2. Social: Searching for a user, making friends, starting a game with a friend, etc.
3. Ingame chatting (Game): Texting, sending images, Voice2Text, voice mail, etc
4. Account: Changing avatar, changing passwords, Facebook Login, etc.
5. Dashboard: Scoreboards, matching players of similar levels, etc.
Dashboard: Checking personal history, comparing to global MAX, MEDIAN, MEAN, etc
6. Matching players (Game): Human VS machine; matching different rooms according to initial credit(i.e. 100 credits/ 200 credits); matching different rooms according to the preferred number of players(i.e. 4P rooms/10P rooms); ...

# Functionality

Check product backlog at [PDF version](product_backlog.pdf) or [Google Sheet](https://docs.google.com/a/andrew.cmu.edu/spreadsheets/d/1uMEWvXBT5bNIX06gBb_KE99MrlW8SU37tavY0iCz6rQ/edit?usp=sharing)

# Data models

```
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Use django Auth Sys
from django.contrib.auth.models import User
from django.db import models


# Account, Social
# class User

class UserInfo(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    avatar = models.ImageField(default='default/kitty.jpeg', upload_to='avatars', null=True, blank=True)

    age = models.IntegerField(default=0, null=True)
    bio = models.CharField(default="", max_length=420, null=True)

    friends = models.ManyToManyField("self")

    balance = models.IntegerField(default=0, null=True)

    def __unicode__(self):
        return self.user_id


class Chat(models.Model):
    from_user = models.ForeignKey(User)
    to_user = models.ForeignKey(User)
    message = models.CharField(max_length=140)
    time = models.DateTimeField(auto_now_add=True)


# Game
class Room(models.Model):
    # The user who creates the room
    creator = models.ForeignKey(User)
    # The code for the others to enter
    room_no = models.CharField()
    # The number of the players to enter
    player_num = models.IntegerField()
    players = models.ManyToManyField(User)


class Game(models.Model):
    # Game info
    room = models.ForeignKey(Room)
    game_id = models.IntegerField()

    # Cards are stored as string and parsed one by one
    # Dealer
    dealer_cards = models.CharField()

    # Player info
    player_cards = models.CharField()


# Store the users' bets in a game
class PlayerHistory(models.Model):
    time = models.DateTimeField(auto_now_add=True)
    game = models.ForeignKey(Game)
    user = models.ForeignKey(User)
    operation = models.CharField()
    amount = models.IntegerField()


# Credits
# Check this db for redeeming the coupon
class Coupon(models.Model):
    coupon_id = models.CharField()
    amount = models.FloatField()
    is_active = models.BooleanField(default=True)
    expire_date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.coupon_id


class BalanceHistory(models.Model):
    user = models.ForeignKey(
        UserInfo,
        on_delete=models.CASCADE,
        primary_key=True,
    )

    time = models.DateTimeField(auto_now_add=True)
    amt = models.IntegerField(default=0, null=True)
    # Whether this is an modification by coupon or google pay
    type = models.CharField()
    # coupon = models.ForeignKey(Coupon)

```

# Wireframes
![Account Changepassword](/specification/wireframe/account_changepassword.png)

![Account Changeprofile](/specification/wireframe/account_changeprofile.png)

![Account Login](/specification/wireframe/account_login.png)

![Account Register](/specification/wireframe/account_register.png)

![Credits Coupon](/specification/wireframe/credits_coupon.png)

![Credits Google Pay Added](/specification/wireframe/credits_google_pay_added.png)

![Dashboard Scoreboard](/specification/wireframe/dashboard_scoreboard.png)

![Dashboard Userhistory](/specification/wireframe/dashboard_userhistory.png)

![Game Init](/specification/wireframe/game_init.png)

![Game Init Succeed](/specification/wireframe/game_init_succeed.png)

![Game Join](/specification/wireframe/game_join.png)

![Game Ongoing](/specification/wireframe/game_ongoing.png)

![Game Result](/specification/wireframe/game_result.png)

![Game Win](/specification/wireframe/game_win.png)

![Social Invitefriends](/specification/wireframe/social_invitefriends.png)

![Social Makingfriends](/specification/wireframe/social_makingfriends.png)

![Social Searchinguser](/specification/wireframe/social_searchinguser.png)
