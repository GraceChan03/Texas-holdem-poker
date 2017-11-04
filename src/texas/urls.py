from django.conf.urls import url
from . import views, views_account, views_game
from .forms import *

urlpatterns = [
    url(r'^register$', views_account.register, name='register'),
    url(r'^login$', views_account.login, name='login'),
    url(r'^logout$', views_account.logout, name='logout'),
    url(r'^activate/(?P<user_name>.+)/(?P<token>.+)$', views_account.activate, name='activate'),

    url(r'^$', views.home, name='homepage'),

    url(r'^profile/(?P<user_name>.+)$', views.profile, name='profile'),

    url(r'^change_email$', views.change_email, name='change_email'),

    url(r'^account_setting$', views.account_setting),
    url(r'^edit_profile$', views.edit_profile, name='edit_profile'),
    url(r'^change_password$', views.change_password, name='edit_profile'),
    url(r'^upload_profileimg$', views.upload_profile_photo, name='upload_profileimg'),
    url(r'^upload_bgimg$', views.upload_profile_background, name='upload_profilebg'),
    url(r'^forget_password$', views.forget_password, name='forget_password'),
    url(r'^reset_password/(?P<user_name>.+)/(?P<token>.+)$', views.reset_password, name='reset_password'),
    url(r'^reset_password_submit/(?P<user_name>.+)$', views.reset_password_submit, name='reset_password_submit'),

    url(r'^add_friend/(?P<user_name>.+)$', views.add_friend, name='add_friend'),
    url(r'^delete_friend/(?P<user_name>.+)$', views.delete_friend, name='delete_friend'),

    url(r'^new_game$', views_game.new_game, name='new_game'),
    url(r'^dashboard$', views_game.dashboard, name='dashboard'),
    url(r'^myfriends$', views_game.myfriends, name='myfriends'),
    url(r'^scoreboard$', views_game.scoreboard, name='scoreboard'),
    # should with (?P<user_name>.+)$, but for static page testing I just move it
    url(r'^search_friend$', views_game.search_friend, name='search_friend'),
    # url(r'^get_coupon/(?P<user_name>.+)$', views.get_coupon, name='get_coupon'),
    # should with game id
    url(r'^game_join$', views_game.game_join, name='game_join'),
    url(r'^game_ongoing$', views_game.game_ongoing, name='game_ongoing'),
    url(r'^game_result$', views_game.game_result, name='game_result'),
    url(r'^about$', views.about, name='about'),
]
