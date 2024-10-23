from django import forms

from mailmaster.models import NewsLetter, Client


class NewsLetterForm(forms.ModelForm):
    class Meta:
        model = NewsLetter
        fields = (
            "start_date",
            "end_date",
            "period",
            "message",
        )

    # def clean_email(self):
    #     cleaned_data = self.cleaned_data.get('email')
    #
    #     if cleaned_data is None:
    #         return None
    #
    #     if 'sky.pro' not in cleaned_data:
    #         raise forms.ValidationError('Почта должна относиться к учебному заведению')
    #     return cleaned_data


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = "__all__"
