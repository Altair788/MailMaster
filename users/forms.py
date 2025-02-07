from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from users.models import User


class UserRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = (
            "email",
            "password1",
            "password2",
        )


class PasswordResetForm(forms.Form):
    email = forms.EmailField(label="Введите вашу почту", max_length=254)


class UserProfileForm(UserChangeForm):
    class Meta:
        model = User
        fields = (
            "email",
            "phone",
            "country",
            "avatar",
            "company_name",
            "inn",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["password"].widget = forms.HiddenInput()
