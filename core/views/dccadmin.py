from allauth.account.models import EmailConfirmationHMAC, EmailAddress
# from rest_framework import status
# from rest_framework.response import Response
# from django_rest_framework.views import APIView

from django.core import serializers
from django.contrib.auth.decorators import (
    permission_required, user_passes_test, login_required
)
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import Group
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.utils.translation import gettext
from django.views import generic
from django.utils import timezone

from core.models.user import User
from core.models.util import DCC


def in_admin_group(user):
    if user.is_staff  or user.is_superuser:
        return True
    else:
        return user.groups.filter(name='dcc_admins').exists()


class IsAdminTestMixin(UserPassesTestMixin):
    def test_func(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return True
        else:
            return self.request.user.groups.filter(
                name='dcc_admins').exists()


class AdminIndexView(IsAdminTestMixin, generic.ListView):
    permission_required = 'core.access_admin_dash'
    template_name = 'core_admin/base.html'
    model = DCC

    def get_queryset(self):
        return DCC.objects.filter().first()

    def get_context_data(self, *args, **kwargs):
        user_tz = timezone.get_current_timezone()
        today = timezone.now()
        last_week = timezone.now() - timezone.timedelta(days=15)

        context = super(
            AdminIndexView, self).get_context_data(*args, **kwargs)
        context["users"] = User.objects.all()

        # print(User.objects.filter(emailaddress__verified="true"))

        return context

"""
class ResendVerifyEmail(APIView):

    def post(self, request):
        data = request.data
        email = data['email']
        try:
            email_address = EmailAddress.objects.get(email=email)
            emac = EmailConfirmationHMAC(email_address=email_address)
            emac.send(request, signup=True)

            return Response(
                {'msg': 'The verification email has been sent'}, 
                status=status.HTTP_201_CREATED
            )
        except EmailAddress.DoesNotExist:
            return Response({
                'msg': 'No such user, register first'
            })

"""

def resend_verification_email(request):
    user_id = request.POST["user"]
    email_sent = False

    try:
        user_obj = User.objects.get(id=user_id)
        email_to_verify = None
        msg = gettext(f"User {user_obj.username} has verified primary email!")

        if not user_obj.emailaddress_set.filter(verified=False).exists():
            msg = gettext('User has no email that needs verification')
        else:
            email_to_verify = user_obj.emailaddress_set.filter(
                verified=False).first()
            # resp = email_to_verify.send_confirmation(request, signup=False)
            # print(resp)
            emac = EmailConfirmationHMAC(email_address=email_to_verify)
            emac.send(request, signup=True)
            email_sent = True
            msg = gettext('The verification email has been sent')
            messages.success(request, msg)

    except User.DoesNotExist:
        msg = gettext(f"User with id - {user_id} does not exist!")
        messages.warning(request, msg)

    return redirect('core:dcc_admin')
