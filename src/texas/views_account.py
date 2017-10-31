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
from texas.util import send_email

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