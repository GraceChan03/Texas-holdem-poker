# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import auth
from django.urls import reverse

from .forms import *
from .models import *
from .util import send_email
from mimetypes import guess_type
from datetime import datetime


@login_required(login_url='login')
# guess this should be dashboard?
def home(request):
    # connect social network user with a profile
    try:
        UserInfo.objects.get(user=request.user)
    except:
        user_info = UserInfo.objects.create(user=request.user, balance=1000, activation=True)
        user_info.save()
    context = {}
    context['searchForm'] = SearchUser()
    # context['post_form'] = PostForm()
    return render(request, "homepage.html", context)


def get_profile_image(request, id):
    user = get_object_or_404(User, id=id)
    image = user.userinfo.profile_photo_src
    return HttpResponse(image, guess_type(image.name))


@login_required(login_url='login')
def profile(request, user_name):
    if User.objects.get(username=user_name):
        context = {}
        context['searchForm'] = SearchUser()
        user = User.objects.get(username=user_name)
        userinfo = UserInfo.objects.get(user=user)
        context['profile_user'] = user
        context['profile'] = userinfo
        if user_name != request.user.username:
            if user in UserInfo.objects.get(user=request.user).friends.all():
                context['isfriend'] = True
        return render(request, 'profile.html', context)
    else:
        return redirect("/")


@login_required(login_url='login')
def edit_profile(request):
    # display form if this is a GET request
    context = {}
    context['searchForm'] = SearchUser()
    instance = UserInfo.objects.get(user=request.user)
    # instance2 = User.objects.get(id = request.user.id);
    if request.method == 'GET':
        context['form'] = EditProfileForm(instance=instance)
        context['userform'] = EditUser(instance=request.user)
        context['userinfo'] = instance
        return render(request, 'editprofile.html', context)

    form = EditProfileForm(request.POST, request.FILES, instance=instance)
    userform = EditUser(request.POST, instance=request.user)
    context['form'] = form
    context['userform'] = userform
    if not form.is_valid():
        return render(request, 'editprofile.html', context)
    if not userform.is_valid():
        return render(request, 'editprofile.html', context)
    form.save()
    userform.save()
    return redirect(reverse("edit_profile"))


@login_required(login_url='login')
def change_password(request):
    # display form if this is a GET request
    context = {}
    context['searchForm'] = SearchUser()
    if request.method == 'GET':
        context['form'] = ChangePasswordForm()
        return render(request, 'change_password.html', context)

    form = ChangePasswordForm(request.POST)
    context['form'] = form
    if not form.is_valid():
        return render(request, "change_password.html", context)
    newpassword = User.objects.get(username=request.user.username)
    newpassword.set_password(form.cleaned_data['newpassword1'])
    newpassword.save()
    user = authenticate(username=request.user.username, password=form.cleaned_data['newpassword1'])
    login(request, user)
    # messages.error(request, 'You sucessfully change your password!')
    return redirect('/')


def password_reset(request, user_name, token):
    if request.user.is_authenticated():
        return redirect("/")
    context = {}
    context['searchForm'] = SearchUser()
    if User.objects.filter(username=user_name):
        user = User.objects.get(username=user_name)
        if default_token_generator.check_token(user, token):
            context['key'] = token
            context['username'] = user.username
    if request.method == 'GET':
        context['form'] = ChangePasswordForm()
        return render(request, 'change_password.html', context)
    form = ChangePasswordForm(request.POST)
    context['form'] = form
    if not form.is_valid():
        # messages.error(request, 'Confirmed password does not match!')
        return redirect("/")
    newpassword = User.objects.get(username=user.username)
    newpassword.set_password(form.cleaned_data['newpassword1'])
    newpassword.save()
    # messages.error(request, 'You sucessfully change your password!')
    return redirect("/")


def forget_password(request):
    if request.user.is_authenticated():
        return redirect("/")
    context = {}
    context['searchForm'] = SearchUser()
    if request.method == 'GET':
        context['form'] = EmailPassword()
        return render(request, 'resetemail.html', context)
    form = EmailPassword(request.POST)
    context['form'] = form
    if not form.is_valid():
        return render(request, "resetemail.html", context)
    user = User.objects.get(email=form.cleaned_data['email'])
    key = default_token_generator.make_token(user)
    # send email for reset
    email_body = """
        Welcome to CMU Texas Hold'em. Please click the link below to reset your password:

        http://%s%s
        """ % (request.get_host(), reverse("password_reset", args=(user.username, key,)))
    send_mail(subject="Change your password",
              message=email_body,
              from_email="admin <no-replay>@cmutexas.com",
              recipient_list=[form.cleaned_data['email']])
    # messages.error(request, 'A reset link was sent to your email')
    return redirect('/')


@login_required(login_url='login')
def add_friend(request, user_name):
    user = request.user
    if User.objects.filter(username=user_name):
        friend = User.objects.get(username=user_name)
        friend_request = FriendshipRequests(from_user=user, to_user=friend)
        friend_request.save()
        return redirect('/profile/' + user_name)
    else:
        return HttpResponseRedirect('/')


@login_required(login_url='login')
def friend_requests(request):
    context = {}
    context['searchForm'] = SearchUser()
    requests = FriendshipRequests.objects.filter(to_user=request.user).order_by('-sent_time')
    context['requests'] = requests
    return render(request, 'friend_requests.html', context)


@login_required(login_url='login')
def check_friend_requests(request):
    frequest = FriendshipRequests.objects.filter(to_user=request.user, is_notified=False)
    if frequest:
        notification = frequest.count()
    else:
        notification = 0
    return HttpResponse(notification)

@login_required(login_url='login')
def game_inivitation(request):
    context = {}
    context['searchForm'] = SearchUser()
    requests = Chat.objects.filter(to_user=request.user).order_by('-time')
    context['requests'] = requests
    return render(request, 'friend_invite.html', context)

@login_required(login_url='login')
def check_invitation_requests(request):
    invitations = Chat.objects.filter(to_user=request.user, is_notified=False)
    if invitations:
        invitations = invitations.count()
    else:
        invitations = 0
    return HttpResponse(invitations)

@login_required(login_url='login')
def disable_notification(request):
    timestamp = int(request.POST['timestamp'])
    frequest = FriendshipRequests.objects.filter(to_user=request.user, is_notified=False)
    if frequest:
        for f in frequest:
            sent_time = int(f.sent_time.strftime('%s'))
            if sent_time < timestamp:
                fr = FriendshipRequests.objects.get(id=f.id)
                fr.is_notified = True
                fr.save()
        return HttpResponse("notified")
    return HttpResponse("no requests")

@login_required(login_url='login')
def disable_game_notify(request):
    timestamp = int(request.POST['timestamp'])
    invitations = Chat.objects.filter(to_user=request.user, is_notified=False)
    if invitations:
        for f in invitations:
            sent_time = int(f.time.strftime('%s'))
            if sent_time < timestamp:
                fi = Chat.objects.get(id=f.id)
                fi.is_notified = True
                fi.save()
        return HttpResponse("notified")
    return HttpResponse("no requests")

@login_required(login_url='login')
def confirm_request(request, user_name, sent_time):
    user = request.user
    if User.objects.get(username=user_name):
        from_user = User.objects.get(username=user_name)
        if FriendshipRequests.objects.get(from_user=from_user, sent_time=sent_time):
            friendRequest = FriendshipRequests.objects.get(from_user=from_user, sent_time=sent_time)
            UserInfo.objects.get(user=user).friends.add(from_user)
            UserInfo.objects.get(user=from_user).friends.add(user)
            friendRequest.is_accepted = True
            friendRequest.is_replied = True
            friendRequest.replied_time = datetime.now()
            friendRequest.save()
    return redirect(reverse('friend_requests'))


@login_required(login_url='login')
def decline_request(request, user_name, sent_time):
    if User.objects.get(username=user_name):
        from_user = User.objects.get(username=user_name)
        if FriendshipRequests.objects.get(from_user=from_user, sent_time=sent_time):
            friendRequest = FriendshipRequests.objects.get(from_user=from_user, sent_time=sent_time)
            friendRequest.is_declined = True
            friendRequest.is_replied = True
            friendRequest.replied_time = datetime.now()
            friendRequest.save()
    return redirect(reverse('friend_requests'))


def email_invite(request):
    context = {}
    context['searchForm'] = SearchUser()
    if request.method == 'GET':
        return redirect("/")
    form = EmailPassword(request.POST)
    context['form'] = form
    context['email_form'] = EmailPassword()
    context['game_no'] = request.POST['game_no']
    context['entry_funds'] = request.POST['entry_funds']
    context['players'] = request.POST['players']
    if not form.is_valid():
        # should be handled better
        return redirect("/")
    # send email to invite
    email_body = """
        You are invited a opened Texas Hold'em game! Click to join the room!
        http://%s%s
        """ % (request.get_host(), reverse("game_ongoing", args=(request.POST['game_no'],)))
    send_mail(subject="CMU-Texas game invitation",
              message=email_body,
              from_email="admin <no-replay>@cmutexas.com",
              recipient_list=[form.cleaned_data['email']])
    context['email_sent'] = True
    # messages.error(request, 'A reset link was sent to your email')
    return render(request, 'game_init_success.html', context)

@login_required(login_url='login')
def station_invite(request):
    if request.method == 'GET':
        # return to room opened page?
        return redirect("/")
    friends = request.POST['friends']
    friends = str(friends).split("|")
    for f in friends:
        if f == request.user:
            continue
        if User.objects.filter(username=f):
            touser = User.objects.get(username=f)
            newchat = Chat(from_user=request.user,
                           to_user=touser,
                           message=request.POST['game_no'])
            newchat.save()
        return HttpResponse("success")
    return HttpResponse("no user invited")

def get_coupon(request):
    context = {}
    context['couponForm'] = GetCoupon()
    context['searchForm'] = SearchUser()
    if request.method == 'GET':
        return render(request, 'get_coupon.html', context)
    form = GetCoupon(request.POST)
    context['form'] = form
    if not form.is_valid():
        # should be handled better
        context['warnning'] = "Please input valid coupon"
        return render(request, 'get_coupon.html', context)
    if not Coupon.objects.get(coupon_id=form.cleaned_data['coupon_id']):
        context['warnning'] = "Please input valid coupon"
        return render(request, 'get_coupon.html', context)
    coupon = Coupon.objects.get(coupon_id=form.cleaned_data['coupon_id'])
    if coupon.expire_date.replace(tzinfo=None) < datetime.now():
        context['warnning'] = "Your coupon was out of date"
        return render(request, 'get_coupon.html', context)
    if not coupon.is_active:
        context['warnning'] = "Your coupon was already consumed"
        return render(request, 'get_coupon.html', context)
    useInfo = UserInfo.objects.get(user=request.user)
    currentBalance = useInfo.balance
    useInfo.balance = (currentBalance + int(coupon.amount))
    useInfo.save()
    coupon.is_active = False
    coupon.save()
    context['warnning'] = "You successfully consume your coupon"
    return render(request, 'get_coupon.html', context)
