from django import forms
from core.models.classifieds import ForumTopic, StudioEvent


class StudioEventForm(forms.ModelForm):
    class Meta:
        model = StudioEvent
        fields = "__all__"


class ForumTopicForm(forms.ModelForm):
    class Meta:
        model = ForumTopic
        fields = "__all__"
