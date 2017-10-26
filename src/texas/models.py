# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Use django Auth Sys
from django.contrib.auth.models import User
from django.db import models

# Create your models here.


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
