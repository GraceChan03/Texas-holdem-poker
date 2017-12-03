from django.conf.urls import url, include
from . import views, views_account, views_game
from django.contrib.auth import views as auth_views
from .forms import *

urlpatterns = [
    url(r'^register$', views_account.register, name='register'),
    url(r'^login$', auth_views.LoginView.as_view(template_name='login.html', redirect_authenticated_user=True),
        name='login'),
    url(r'^logout$', auth_views.logout_then_login, name='logout'),
    url(r'^oauth/', include('social_django.urls', namespace='social')),  # facebook login
    url(r'^activate/(?P<user_name>.+)/(?P<token>.+)$', views_account.activate, name='activate'),
    url(r'^get_profile_image/(?P<id>.+)$', views.get_profile_image, name='get_profile_image'),

    url(r'^$', views.home, name='homepage'),

    url(r'^profile/(?P<user_name>.+)$', views.profile, name='profile'),

    url(r'^edit_profile$', views.edit_profile, name='edit_profile'),
    url(r'^change_password$', views.change_password, name='change_password'),
    url(r'^forget_password$', views.forget_password, name='forget_password'),
    url(r'^password_reset/(?P<user_name>.+)/(?P<token>.+)$', views.password_reset, name='password_reset'),
    # url(r'^reset_password/(?P<user_name>.+)/(?P<token>.+)$', views.reset_password, name='reset_password'),
    # url(r'^reset_password_submit/(?P<user_name>.+)$', views.reset_password_submit, name='reset_password_submit'),

    url(r'^add_friend/(?P<user_name>.+)$', views.add_friend, name='add_friend'),
    url(r'^friend_requests$', views.friend_requests, name='friend_requests'),
    url(r'^check_friend_requests$', views.check_friend_requests, name='check_friend_requests'),
    url(r'^disable_notification$', views.disable_notification, name='disable_notification'),
    url(r'^confirm_request/(?P<user_name>.+)/(?P<sent_time>.+)$', views.confirm_request, name='confirm_request'),
    url(r'^decline_request/(?P<user_name>.+)/(?P<sent_time>.+)$', views.decline_request, name='decline_request'),
    # url(r'^delete_friend/(?P<user_name>.+)$', views.delete_friend, name='delete_friend'),

    url(r'^new_game$', views_game.new_game, name='new_game'),
    url(r'^email_invite$', views.email_invite, name='email_invite'),
    url(r'^dashboard$', views_game.dashboard, name='dashboard'),
    url(r'^myfriends$', views_game.myfriends, name='myfriends'),
    url(r'^scoreboard$', views_game.scoreboard, name='scoreboard'),
    # should with (?P<user_name>.+)$, but for static page testing I just move it
    url(r'^search_friend$', views_game.search_friend, name='search_friend'),
    # url(r'^get_coupon/(?P<user_name>.+)$', views.get_coupon, name='get_coupon'),
    # should with game id
    url(r'^game_join$', views_game.game_join, name='game_join'),
    url(r'^game_ongoing/(?P<game_no>.+)$', views_game.game_ongoing, name='game_ongoing'),
    url(r'^exit_room/(?P<game_no>.+)/(?P<id>.+)$', views_game.exit_room, name='exit_room'),
    url(r'^game_result$', views_game.game_result, name='game_result'),

]
