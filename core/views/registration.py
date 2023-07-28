import json

from django.contrib.auth import (
    authenticate, logout, login, update_session_auth_hash)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils.translation import gettext

from core.forms.registration import UserRegistrationForm

import logging
logger = logging.getLogger(__name__)


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)
            return redirect('/')
        else:
            logger.error("User registration error: %s", repr(form.errors), exc_info=1)
            print(form.errors)
    else:
        if request.user.is_authenticated:
            return redirect('/')
        form = UserRegistrationForm()
    return render(
        request, 'registration/signup_studio.html', 
        {'form': form}
    )


@login_required
def user_password_update(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            msg = gettext("Your password was successfully updated!")
        else:
            msg = gettext("Please correct the error(s) below.")
        
        return JsonResponse({
            'isValid': form.is_valid(),
            'msg': msg,
            'errors': json.dumps(form.errors)
        })
    else:
        return JsonResponse({'isValid': False})
