import random
import secrets
import string


from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, UpdateView

from config.settings import EMAIL_HOST_USER
from users.forms import PasswordResetForm, UserProfileForm, UserRegisterForm
from users.models import User


class UserCreateView(CreateView):
    model = User
    form_class = UserRegisterForm
    # чтобы обойти ошибку TemplateDoesNotExist at /users/register/
    template_name = "users/register.html"
    success_url = reverse_lazy("users:login")

    def form_valid(self, form):
        #  сохраняем пользователя
        user = form.save()
        user.is_active = False
        token = secrets.token_hex(16)
        user.token = token
        user.save()
        host = self.request.get_host()
        url = f"http://{host}/users/email-confirm/{token}/"
        send_mail(
            subject="Подтверждение почты",
            message=f"Привет, перейди по ссылке для подтверждения почты {url}",
            from_email=EMAIL_HOST_USER,
            recipient_list=[user.email],
        )
        return super().form_valid(form)


def email_verification(request, token):
    user = get_object_or_404(User, token=token)
    user.is_active = True
    user.save()
    return redirect(reverse("users:login"))


class ProfileView(UpdateView):
    model = User
    form_class = UserProfileForm
    success_url = reverse_lazy("users:profile")

    def get_object(self, queryset=None):
        return self.request.user


class PasswordResetView(View):
    template_name = "users/password_reset.html"
    success_url = reverse_lazy("users:login")

    def get(self, request):
        form = PasswordResetForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            user = get_object_or_404(User, email=email)

            # Генерация нового пароля
            new_password = self.generate_random_password()

            # Обновление пароля пользователя с автоматическим хешированием через set_password
            user.set_password(new_password)
            user.save()

            # Отправка email с новым паролем
            send_mail(
                subject="Сброс пароля",
                message=f"Ваш новый пароль: {new_password}",
                from_email=EMAIL_HOST_USER,
                recipient_list=[user.email],
            )
            return redirect(self.success_url)
        return render(request, self.template_name, {"form": form})

    def generate_random_password(self, length=16):
        characters = string.ascii_letters + string.digits + string.punctuation
        return "".join(random.choice(characters) for _ in range(length))
