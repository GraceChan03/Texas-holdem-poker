# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from datetime import date
from django.contrib import auth
from django.urls import reverse

from texas.forms import *
from texas.models import *


# @login_required(login_url='login')
# guess this should be dashboard?
def home(request):
    context = {}
    # context['post_form'] = PostForm()
    return render(request, "homepage.html", context)


# @login_required(login_url='login')
def profile(request, user_name):
    context = {}
    # user = get_object_or_404(User, username=user_name)
    if User.objects.filter(username=user_name):
        user = User.objects.get(username=user_name)
        context['user'] = user
        userinfo = UserInfo.objects.get(user=user)
        context['userinfo'] = userinfo
        if userinfo.dob:
            today = date.today()
            born = userinfo.dob
            context['age'] = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        context['friends'] = count_friends(user)
        # keep information about the user logged in
        login_user = User.objects.get(username=request.user)
        context['login_user'] = login_user
        # If the user profile page is not for logged in user,
        # check if the logged in user is following the current user
        if user.id != login_user.id and Friends.objects.filter(user=login_user):
            following = Friends.objects.get(user=login_user).following.all()
            # following
            if following.filter(username=user_name):
                context['follow'] = True
        return render(request, 'profile.html', context)
    else:
        return HttpResponseRedirect('/')



# def send_email(request, user, to_email, label=None):

def register(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect('/')
    context = {}
    # if this is a GET request, just display the registration form
    if request.method == 'GET':
        context['register_form'] = RegistrationForm()
        return render(request, 'register.html', context)

    form = RegistrationForm(request.POST)
    context['register_form'] = form

    if not form.is_valid():
        return render(request, 'register.html', context)

    # after validation, create new user
    new_user = User.objects.create_user(username=form.cleaned_data['username'], \
                                        first_name=form.cleaned_data['first_name'], \
                                        last_name=form.cleaned_data['last_name'], \
                                        email=form.cleaned_data['email'], \
                                        password=form.cleaned_data['password1'])
    new_user.save()
    user_info = UserInfo.objects.create(user=new_user)
    user_info.save()

    to_email = form.cleaned_data['email']
    send_email(request, new_user, to_email)

    context['email'] = to_email
    return render(request, 'activate_notice.html', context)


def activate(request, user_name, token):
    if User.objects.filter(username=user_name):
        user = User.objects.get(username=user_name)
        if default_token_generator.check_token(user, token):
            user_info = UserInfo.objects.get(user=user)
            user_info.activation = True
            user_info.save()
    return redirect('/login')


def login(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect('/')

    context = {}
    if request.method == 'GET':
        context['login_form'] = LoginForm()
        return render(request, 'login.html', context)

    form = LoginForm(request.POST)
    context['login_form'] = form

    if not form.is_valid():
        return render(request, 'login.html', context)

    username = form.cleaned_data['username']
    user = User.objects.get(username=username)
    if not UserInfo.objects.get(user=user).activation:
        context['valid_error'] = "User has not yet complete registration. Please check your email."
        return render(request, 'login.html', context)

    password = form.cleaned_data['password']
    user = auth.authenticate(request, username=username, password=password)
    if user is not None:
        auth.login(request, user)
        return HttpResponseRedirect('/')
    else:
        return render(request, 'login.html', context)



def logout(request):
    auth.logout(request)
    return HttpResponseRedirect('/login')


# @login_required(login_url='login')
def account_setting(request):
    context = {}
    # edit here
    return render(request, 'account_setting.html', context)


# @login_required(login_url='login')
def edit_profile(request):
    context = {}
    # check validation
    form = EditProfileForm(request.POST, user=request.user)
    context['edit_profile_form'] = form

    if not form.is_valid():
        return render(request, 'account_setting.html', context)

    username = form.cleaned_data['username']
    dob = form.cleaned_data['dob']
    bio = form.cleaned_data['bio']
    user = request.user
    edit_user = User.objects.get(id=user.id)
    if username and username != '':
        edit_user.username = username
        edit_user.save()
    edit_userinfo = UserInfo.objects.get(user=user)
    if dob and dob != '':
        edit_userinfo.dob = dob
        edit_userinfo.save()
    if bio and bio != '':
        edit_userinfo.sign = bio
        edit_userinfo.save()
    return HttpResponseRedirect('/account_setting')


# @login_required(login_url='login')
def change_password(request):
    context = {}
    form = ChangePasswordForm(request.POST, user=request.user)
    context['change_password_form'] = form
    if not form.is_valid():
        return render(request, 'account_setting.html', context)

    new_password = form.cleaned_data['new_password1']
    user = request.user
    username = user.username
    edit_user = User.objects.get(id=user.id)
    edit_user.set_password(new_password)
    edit_user.save()

    # log in the user
    edited_user = auth.authenticate(username=username,
                                    password=new_password)
    auth.login(request, edited_user)
    return HttpResponseRedirect('/account_setting')


def forget_password(request):
    context = {}
    if request.user.is_authenticated():
        user = request.user
        if request.method == 'GET':
            context['email'] = User.objects.get(username=user.username).email
            return render(request, 'confirm_reset_password.html', context)
    else:
        if request.method == 'GET':
            context['email_form'] = EmailForm()
            return render(request, 'begin_password_reset.html', context)
        form = EmailForm(request.POST)
        context['email_form'] = form
        if not form.is_valid():
            return render(request, 'begin_password_reset.html', context)
        email = form.cleaned_data['email']
        if not User.objects.filter(email=email):
            context['email_error'] = "The email address does not exist."
            return render(request, 'begin_password_reset.html', context)
        user = User.objects.get(email=email)
    send_email(request, user, user.email, "reset_password")
    context['email'] = user.email
    return render(request, 'reset_email_sent.html', context)


def reset_password(request, user_name, token):
    if User.objects.filter(username=user_name):
        user = User.objects.get(username=user_name)
        if default_token_generator.check_token(user, token):
            context = {}
            context['reset_form'] = ResetPasswordForm()
            context['username'] = user_name
            return render(request, 'reset_email.html', context)
    return HttpResponseRedirect('/')


def reset_password_submit(request, user_name):
    # if the request is from bad guys, what will happen?
    context = {}
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        context['reset_form'] = form
        if not form.is_valid():
            return render(request, 'reset_email.html', context)
        # reset password
        if User.objects.filter(username=user_name):
            user = User.objects.get(username=user_name)
            new_password = form.cleaned_data['password1']
            user.set_password(new_password)
            user.save()
            if request.user.is_authenticated():
                auth.logout(request)
    return HttpResponseRedirect('/')


# @login_required(login_url='login')
def upload_profile_photo(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'account_setting.html', context)

    form = UploadProfilePhotoForm(request.POST, request.FILES)
    context['upload_photo_form'] = form
    if not form.is_valid():
        return render(request, 'account_setting.html', context)

    # handle_uploaded_file(request.FILES['image'])
    userinfo = UserInfo.objects.get(user=request.user)
    userinfo.profile_photo_src = request.FILES['image']
    userinfo.save()

    return HttpResponseRedirect('/account_setting')


# @login_required(login_url='login')
def upload_profile_background(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'account_setting.html', context)
    form = UploadProfileBackgroundForm(request.POST, request.FILES)
    context['upload_bg_form'] = form
    if not form.is_valid():
        return render(request, 'account_setting.html', context)
    userinfo = UserInfo.objects.get(user=request.user)
    userinfo.card_background_src = request.FILES['bgimage']
    userinfo.save()
    return HttpResponseRedirect('/account_setting')


# @login_required(login_url='login')
def change_email(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'account_setting.html', context)
    form = EmailForm(request.POST)
    context['email_form'] = form
    if not form.is_valid():
        return render(request, 'account_setting.html', context)
    new_email = form.cleaned_data['email']
    user = request.user
    edit_user = User.objects.get(id=user.id)
    if new_email and new_email != '':
        edit_user.email = new_email
        edit_user.save()
    send_email(request, request.user, new_email)
    auth.logout(request)
    context['email'] = new_email
    return render(request, 'activate_notice.html', context)


# @login_required(login_url='login')
def add_friend(request, user_name):
    user = request.user
    if User.objects.filter(username=user_name):
        friend = User.objects.get(username=user_name)
        # user has followed some other users
        if Friends.objects.filter(user=user):
            new_friend = Friends.objects.get(user=user)
        else:
            new_friend = Friends(user=user)
            new_friend.save()
        new_friend.friends.add(friend)
        new_friend.save()
        return redirect('/profile/' + user_name)
    else:
        return HttpResponseRedirect('/')

# @login_required(login_url='login')
def delete_friend(request, user_name):
    user = request.user
    # check if the user exists in follow table
    if Friends.objects.filter(user=user) and User.objects.filter(username=user_name):
        friends = Friends.objects.get(user=user).following
        deletedfriend = User.objects.get(username=user_name)
        friends.remove(deletedfriend)
    return redirect('/profile/' + user_name)

validate_email = {
    "subject": "CMU-Texas: Verify your email address",
    "message": """
Thank you for registering for CMU-Texas. Please click the link bellow to verify your email address and finish the registration of your account:
http://%s%s
    """
}

reset_password_email = {
    "subject": "CMU-Texas: Reset password",
    "message": """
You are using your registered email to reset your password. Please click the link bellow to verify your email address:
http://%s%s
    """
}

def send_email(request, user, to_email, label=None):
    token = default_token_generator.make_token(user)
    username = user.username
    if label and label == "reset_password":
        subject = reset_password_email.get("subject")
        message = reset_password_email.get("message") % (request.get_host(), reverse('reset_password', args=(username, token)))
    else:
        subject = validate_email.get("subject")
        message = validate_email.get("message") % (request.get_host(), reverse('activate', args=(username, token)))
    from_email = "team318@cmu.edu"
    try:
        send_mail(subject, message, from_email, [to_email])
    except BadHeaderError:
        return HttpResponse('Invalid header found.')


def count_friends(user):
    if Friends.objects.filter(user=user):
        friends = Friends.objects.get(user=user).friends.all()
        if friends:
            return friends.count()
    return 0

# @login_required(login_url='login')
# url not written
def my_friend(request):
    # show all friends list
    return

# @login_required(login_url='login')
def new_game(request):
    context = {}
    user = request.user
    # edit here
    return render(request, 'new_game.html', context)

# @login_required(login_url='login')
def dashboard(request):
    context = {}
    user = request.user
    # edit here
    return render(request, 'dashboard.html', context)
# @login_required(login_url='login')
def myfriends(request):
    context = {}
    user = request.user
    # edit here
    return render(request, 'myfriends.html', context)

# @login_required(login_url='login')
def scoreboard(request):
    context = {}
    user = request.user
    # edit here
    return render(request, 'scoreboard.html', context)

# @login_required(login_url='login')
def search_friend(request):
    context = {}
    user = request.user
    # edit here
    return render(request, 'search_friend.html', context)

# @login_required(login_url='login')
def game_join(request):
    context = {}
    user = request.user
    # edit here
    return render(request, 'game_join.html', context)

# @login_required(login_url='login')
def game_init_success(request):
    context = {}
    user = request.user
    # edit here
    return render(request, 'game_init_success.html', context)

# @login_required(login_url='login')
def game_ongoing(request):
    context = {}
    user = request.user
    # edit here
    return render(request, 'game_ongoing.html', context)

# @login_required(login_url='login')
def game_result(request):
    context = {}
    user = request.user
    # edit here
    return render(request, 'game_result.html', context)

# @login_required(login_url='login')
def about(request):
    context = {}
    user = request.user
    # edit here
    return render(request, 'about.html', context)

