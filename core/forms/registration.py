from allauth.account.forms import SignupForm

from django import forms
from django.contrib.auth.forms import UserCreationForm
from core.models.user import EmailSubscribers, User, UserProfile, Studio


class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name',
            'password1', 'password2', 'email'
        ]


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        # fields = ["email"]
        fields = [
            'first_name', 'last_name', 'email',
        ]


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        # fields = "__all__"
        # exclude = ["user", "type"]
        fields = [
            "avatar", "bio", "profile_photo", "cover_photo",
            "phone", "organization", "display_name", "full_name",
            "alt_phone", "timezone", "receive_promo_emails",
            "receive_other_emails", "address", "resume", "dob",
            "city", "province", "country", "postal_code", "website",
            "facebook", "instagram", "twitter", "tiktok", "youtube",
            "genres", "interests", "alt_name", "organization", "type",
            "linkedin"
        ]


class DCCCustomSignupForm(SignupForm):
    first_name = forms.CharField(max_length=100) 
    last_name = forms.CharField(max_length=100)

    def save(self, request):
        user = super(DCCCustomSignupForm, self).save(request)

        return user


class EmailSubscriberForm(forms.ModelForm):
    class Meta:
        model = EmailSubscribers
        fields = "__all__"


class StudioForm(forms.ModelForm):
    class Meta:
        model = Studio
        fields = "__all__"
