from django import forms
from core.models.common import Genre, Location


class GenreForm(forms.ModelForm):
    class Meta:
        model = Genre
        fields = ['name', 'slug']


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = "__all__"
