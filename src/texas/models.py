# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Use django Auth Sys
from django.contrib.auth.models import User
from django.core.validators import validate_comma_separated_integer_list
from django.db import models
import json
import deuces

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
    # Game Start Time
    create_time = models.DateTimeField(auto_now_add=True, null=True)
    # Game Modified Time
    modified_time = models.DateTimeField(auto_now=True, null=True)
    # The user who creates the game room
    creator = models.ForeignKey(User,related_name="creator")
    # The code for the others to enter
    game_no = models.CharField(max_length=200, unique=True)
    # The number of the players to enter
    player_num = models.IntegerField()
    # The least fund that a player should have to join the game
    entry_funds = models.IntegerField()
    players = models.ManyToManyField(User,related_name="players")
    is_active = models.BooleanField(default=True)
    # sit order
    player_order = models.CharField(max_length=200, default='')
    # player fund
    player_fund_dict = models.CharField(max_length=200, default='')

    # when the players' number match the set player num,
    # the game is full
    def is_full(self):
        if self.players.count() == self.player_num:
            return True
        else:
            return False

    # When the fund_dict is empty, add the entry fund to everyone
    # def init_fund_dict(self):
    #     if self.player_fund_dict == '':
    #         player_fund_dict = {}
    #         for player in self.players.all():
    #             player_fund_dict[player.id] = self.entry_funds
    #         self.player_fund_dict = json.dumps(player_fund_dict)


class GameRound(models.Model):
    # Game Round info
    game = models.ForeignKey(Game)

    # Game Round ended or not
    is_active = models.BooleanField(default=True)

    # Game Start Time
    create_time = models.DateTimeField(auto_now_add=True, null=True)

    # Game Modified Time
    modified_time = models.DateTimeField(auto_now=True, null=True)

    # Cards are stored as string and parsed one by one
    # Dealer
    dealer_cards = models.CharField(max_length=200)

    # Player info
    player_cards = models.CharField(max_length=200)

    # bet order
    player_order = models.CharField(max_length=200, default='')

    # player active
    player_active_dict = models.CharField(max_length=200, default='')

    # player fund
    player_fund_dict = models.CharField(max_length=200, default='')

    # player prev bet
    player_bet_dict = models.CharField(max_length=200, default='')

    # Current Approach
    current_approach = models.IntegerField(default=2)

    # Current Max Player
    current_max_player = models.IntegerField(default=-1)

    # Minimum bet
    min_bet = models.IntegerField(default=1)

    # Pot
    pot = models.IntegerField(default=0)

    def get_player_prev_bet(self, player_id):
        if self.player_bet_dict and self.player_bet_dict != '':
            dict = eval(self.player_bet_dict)
        else:
            dict = {}
        return dict[player_id]

    def set_player_prev_bet(self, player_id, curt_bet):
        if self.player_bet_dict and self.player_bet_dict != '':
            dict = eval(self.player_bet_dict)
        else:
            dict = {}
        self.pot = self.pot + int(curt_bet) - int(dict[player_id])
        self.min_bet = curt_bet
        self.less_player_fund(player_id, curt_bet - dict[player_id])
        dict[player_id] = curt_bet
        self.player_bet_dict = str(dict)

    def set_player_prev_bet_dict(self):
        dict = {}
        for player in self.game.players.all():
            dict[player.id] = 0
        self.player_bet_dict = str(dict)

    def increment_current_approach_by_1(self):
        self.current_approach += 1

    def only_active_user(self):
        if self.player_active_dict and self.player_active_dict != '':
            player_active_dict = eval(self.player_active_dict)
        else:
            player_active_dict = {}
        active_cnt = 0
        for player in player_active_dict:
            if player_active_dict[player]:
                active_cnt += 1
                active_user = player

            if active_cnt > 1:
                return None
        if active_cnt == 1:
            return active_user
        else:
            return None

    # Get the rank of all the users' hand, return a dict for indexing
    def process_user_class(self):
        # Save in a dict
        rank_dict = {}
        board = list(eval(self.dealer_cards))
        # create an evaluator
        evaluator = deuces.Evaluator()

        player_cards_dict = json.loads(self.player_cards)
        if self.player_active_dict and self.player_active_dict != '':
            player_active_dict = eval(self.player_active_dict)
        else:
            player_active_dict = {}

        for player in player_cards_dict:
            if player_active_dict[player]:
                hand = player_cards_dict[player]
            # and rank your hand
                rank = evaluator.evaluate(board, hand)
            else:
                rank = -1

            rank_dict[player] = rank

        return rank_dict

    # Return a dict with user rank {1:["id", "id"], 2:["id"]}
    # Does not return folded user
    def process_user_rank(self):
        class_dict = self.process_user_class()
        sorted_class_dict = sorted(class_dict.items(), lambda x, y: cmp(x[1], y[1]), reverse=True)

        best_rank = 7463

        prev_class = best_rank
        rank_dict = {}

        rank = 0

        for item in sorted_class_dict:
            curt_user_id = item[0]
            curt_class = item[1]
            if curt_class == -1:
                return rank_dict
            elif curt_class < prev_class:
                rank += 1
                rank_dict[rank] = [curt_user_id]
            else:
                rank_dict[rank].append(curt_user_id)
        return rank_dict

    # TODO [Function] wrong function just set a position
    def get_winner(self):
        return self.process_user_rank()[1][0]

    def set_player_fund(self, player_id, fund):
        if self.player_fund_dict and self.player_fund_dict != '':
            dict = eval(self.player_fund_dict)
        else:
            dict = {}
        dict[player_id] = fund
        self.player_fund_dict = str(dict)

    def get_player_fund(self, player_id):
        if self.player_fund_dict and self.player_fund_dict != '':
            dict = eval(self.player_fund_dict)
        else:
            dict = {}
        return dict[player_id]

    def less_player_fund(self, player_id, lessfund):
        if self.player_fund_dict and self.player_fund_dict != '':
            dict = eval(self.player_fund_dict)
        else:
            dict = {}
        dict[player_id] = dict[player_id] - lessfund
        self.player_fund_dict = str(dict)

    def add_player_fund(self, player_id, addfund):
        if self.player_fund_dict and self.player_fund_dict != '':
            dict = eval(self.player_fund_dict)
        else:
            dict = {}
        dict[player_id] = dict[player_id] + addfund
        self.player_fund_dict = str(dict)

    def set_player_inactive(self, player_id):
        if self.player_active_dict and self.player_active_dict != '':
            dict = eval(self.player_active_dict)
        else:
            dict = {}
        dict[player_id] = False
        self.player_active_dict = str(dict)

    def set_player_active_dict(self):
        dict = {}
        for player in self.game.players.all():
            dict[player.id] = True
        self.player_active_dict = str(dict)

    def set_player_order(self, prev=0, **kwarg):
        ord = self.game.player_order.split(",")
        order_str = ''
        # for player in self.game.players.all():
        #     ord.append(player.id)
        for i in xrange(prev, len(ord)):
            order_str += (',' + str(ord[i]))
        if prev > 0:
            order_str += (',' + str(ord[i]) for i in xrange(0, prev))
        self.player_order = order_str[1:]

    def start(self, **kwargs):
        if self.player_order == "" or not self.player_order:
            prev = 0
        else:
            prev = int(self.player_order[0] + 1)
            if prev == self.game.player_num:
                prev = 0
        self.set_player_order(prev)
        self.set_player_active_dict()
        self.set_player_prev_bet_dict()
        new_deck = deuces.Deck()
        board = new_deck.draw(5)
        board_str = ''
        for card in board:
            board_str += str(card) + ','
        self.dealer_cards = board_str[:-1]

        player_hands_dict = {}
        num = self.game.player_num

        for player in self.game.players.all():
            player_hands_dict[player.id] = new_deck.draw(2)
        self.player_cards = json.dumps(player_hands_dict)

        self.player_fund_dict = self.game.player_fund_dict

        # ------------Send small blind and big blind -------------
        player_order = self.player_order
        player_order_list_round = eval(player_order)

        self.set_player_prev_bet(player_order_list_round[0], self.min_bet)
        self.set_player_prev_bet(player_order_list_round[1], 2*self.min_bet)
        self.current_max_player = player_order_list_round[1]


# Recording a player's manipulations during a game round
class GameRoundPlayerMan(models.Model):
    round = models.ForeignKey(GameRound)
    player = models.ForeignKey(User)
    hand = models.CharField(max_length=200, validators=[validate_comma_separated_integer_list])
    is_active = models.BooleanField()
    fund = models.IntegerField()
    bet = models.IntegerField()
    time = models.DateTimeField(auto_now_add=True)


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


class FriendshipRequests(models.Model):
    from_user = models.ForeignKey(User, related_name="friend_request_from_user")
    to_user = models.ForeignKey(User, related_name="friend_request_to_user")
    sent_time = models.DateTimeField(auto_now_add=True)
    is_replied = models.BooleanField(default=False)
    replied_time = models.DateTimeField(null=True, blank=True)
    is_accepted = models.BooleanField(default=False)
    is_declined = models.BooleanField(default=False)
    is_notified = models.BooleanField(default=False)
