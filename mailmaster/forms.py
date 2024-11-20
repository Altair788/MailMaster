from django import forms

from mailmaster.models import Client, Message, NewsLetter


class NewsLetterForm(forms.ModelForm):
    class Meta:
        model = NewsLetter
        fields = (
            "start_date",
            "end_date",
            "period",
            "clients",
            "message",
        )
        widgets = {
            "start_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = "__all__"


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = "__all__"
