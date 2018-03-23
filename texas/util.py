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