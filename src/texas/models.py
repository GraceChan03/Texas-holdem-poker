# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Use django Auth Sys
from django.contrib.auth.models import User
from django.db import models
import uuid

# Create your models here.


# Account, Social
# class User

class UserInfo(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    activation = models.BooleanField(default=False)
    profile_photo_src = models.ImageField(default='static/media/default/miao.png', \
                                          upload_to='static/media/upload/', null=True, blank=True)
    card_background_src = models.ImageField(default='static/media/default/cardtop_alt1.jpg', \
                                            upload_to='static/media/upload/', null=True, blank=True)
    dob = models.DateField(null=True)
    sign = models.CharField(max_length=100, null=True)

    balance = models.IntegerField(default=0, null=True)
    friends = models.ManyToManyField(User, related_name='friends')

    def __unicode__(self):
        return self.user_id


class Chat(models.Model):
    from_user = models.ForeignKey(User,related_name="from_user")
    to_user = models.ForeignKey(User,related_name="to_user")
    message = models.CharField(max_length=140)
    time = models.DateTimeField(auto_now_add=True)


# Game
class Game(models.Model):
    # The user who creates the game room
    creator = models.ForeignKey(User,related_name="creator")
    # The code for the others to enter
    game_no = models.CharField(max_length=200, unique=True)
    # The number of the players to enter
    player_num = models.IntegerField()
    # The least fund that a player should have to join the game
    entry_funds = models.IntegerField()
    players = models.ManyToManyField(User,related_name="players")



class GameRound(models.Model):
    # Game Round info
    game = models.ForeignKey(Game)
    game_round_id = models.IntegerField()

    # Cards are stored as string and parsed one by one
    # Dealer
    dealer_cards = models.CharField(max_length=200)

    # Player info
    player_cards = models.CharField(max_length=200)


# Store the users' bets in a game
class PlayerHistory(models.Model):
    time = models.DateTimeField(auto_now_add=True)
    game = models.ForeignKey(GameRound)
    user = models.ForeignKey(User)
    operation = models.CharField(max_length=200)
    amount = models.IntegerField()


# Credits
# Check this db for redeeming the coupon
class Coupon(models.Model):
    coupon_id = models.CharField(max_length=200)
    amount = models.FloatField()
    is_active = models.BooleanField(default=True)
    expire_date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.coupon_id


class BalanceHistory(models.Model):
    user = models.OneToOneField(
        UserInfo,
        on_delete=models.CASCADE,
        primary_key=True,
    )

    time = models.DateTimeField(auto_now_add=True)
    amt = models.IntegerField(default=0, null=True)
    # Whether this is an modification by coupon or google pay
    type = models.CharField(max_length=200)
    # coupon = models.ForeignKey(Coupon)
