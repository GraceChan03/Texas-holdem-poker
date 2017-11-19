# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist
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

@login_required
def profile(request, user_name):
    try:
        context={}
        user = User.objects.get(username=user_name)
        userinfo = UserInfo.objects.get(user=user)
        context['profile_user'] = user
        context['profile'] = userinfo
    except ObjectDoesNotExist:
        # when there is not such id for retrieve
        # messages.error(request, 'The user id does not exist!')
        return redirect(reverse(""))
    return render(request, 'profile.html', context)

@login_required
def edit_profile(request):
    # display form if this is a GET request
    context = {}
    instance = UserInfo.objects.get(user=request.user)
    # instance2 = User.objects.get(id = request.user.id);
    if request.method == 'GET':
        context['form'] = EditProfileForm(instance=instance)
        context['userform'] = EditUser(instance = request.user)
        context['userinfo'] = instance
        return render(request, 'editprofile.html', context)

    form = EditProfileForm(request.POST, request.FILES, instance=instance)
    userform = EditUser(request.POST, instance = request.user)
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
    return redirect(reverse(''))


def password_reset(request, key):
    if request.user.is_authenticated():
        return redirect(reverse(""))
    userinfo = get_object_or_404(UserInfo, activation_key=key)
    user = userinfo.user
    context = {}
    context['key'] = key
    context['username'] = user.username
    if request.method == 'GET':
        context['form'] = ChangePasswordForm()
        return render(request, 'change_password.html', context)
    form = ChangePasswordForm(request.POST)
    context['form'] = form
    if not form.is_valid():
        # messages.error(request, 'Confirmed password does not match!')
        return redirect(reverse(""))
    newpassword = User.objects.get(username=user.username)
    newpassword.set_password(form.cleaned_data['newpassword1'])
    newpassword.save()
    # messages.error(request, 'You sucessfully change your password!')
    return redirect(reverse(""))


def forget_password(request):
    if request.user.is_authenticated():
        return redirect(reverse(""))
    context = {}
    if request.method == 'GET':
        context['form'] = EmailPassword()
        return render(request, 'resetemail.html', context)
    form = EmailPassword(request.POST)
    context['form'] = form
    if not form.is_valid():
        return render(request, "resetemail.html", context)
    user = User.objects.get(email=form.cleaned_data['email'])
    key = UserInfo.objects.get(user=user).activation_key
    # send email for reset
    email_body = """
        Welcome to Grumblr. Please click the link below to reset your password:

        http://%s%s
        """ % (request.get_host(), reverse("password_reset", args=(key,)))
    send_mail(subject="Change your password",
              message=email_body,
              from_email="grumblr <no-replay>@grumblr.com",
              recipient_list=[form.cleaned_data['email']])
    # messages.error(request, 'A reset link was sent to your email')
    return redirect(reverse(''))

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

