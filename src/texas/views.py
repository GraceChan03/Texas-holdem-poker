# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from datetime import date
from django.contrib import auth
from django.urls import reverse

from texas.forms import *
from texas.models import *
from texas.util import send_email
from mimetypes import guess_type


@login_required(login_url='login')
# guess this should be dashboard?
def home(request):
    context = {}
    # context['post_form'] = PostForm()
    return render(request, "homepage.html", context)

def get_profile_image(request, id):
    user = get_object_or_404(User, id=id)
    image = user.userinfo.profile_photo_src
    return HttpResponse(image, guess_type(image.name))

@login_required(login_url='login')
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
        context['friends'] = userinfo.friends.count()
        # keep information about the user logged in
        login_user = User.objects.get(username=request.user)
        context['login_user'] = login_user
        # If the user profile page is not for logged in user,
        # check if the logged in user is following the current user
        if user.id != login_user.id and userinfo.friends.filter(username=request.user):
            context['follow'] = True
        return render(request, 'profile.html', context)
    else:
        return HttpResponseRedirect('/')



@login_required(login_url='login')
def account_setting(request):
    context = {}
    # edit here
    return render(request, 'account_setting.html', context)


@login_required(login_url='login')
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


@login_required(login_url='login')
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


@login_required(login_url='login')
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


@login_required(login_url='login')
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


@login_required(login_url='login')
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


@login_required(login_url='login')
def add_friend(request, user_name):
    user = request.user
    if User.objects.filter(username=user_name):
        friend = User.objects.get(username=user_name)
        user.userinfo.friends.add(friend)
        return redirect('/profile/' + user_name)
    else:
        return HttpResponseRedirect('/')

@login_required(login_url='login')
def delete_friend(request, user_name):
    user = request.user
    # check if the user exists in follow table
    if User.objects.filter(username=user_name):
        deletedfriend = User.objects.get(username=user_name)
        user.friends.remove(deletedfriend)
    return redirect('/profile/' + user_name)



@login_required(login_url='login')
# url not written
def my_friend(request):
    # show all friends list
    return


# @login_required(login_url='login')
def about(request):
    context = {}
    user = request.user
    # edit here
    return render(request, 'about.html', context)

