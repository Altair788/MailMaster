from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

NULLABLE = {"blank": True, "null": True}


class User(AbstractUser):
    username = None

    email = models.EmailField(unique=True, verbose_name="почта")
    token = models.CharField(
        max_length=150, verbose_name="токен", null=True, blank=True
    )

    phone = PhoneNumberField(**NULLABLE, unique=True, verbose_name="номер телефона")
    country = models.CharField(max_length=100, verbose_name="страна", **NULLABLE)
    avatar = models.ImageField(
        upload_to="users/avatars/",
        verbose_name="аватар",
        help_text="Загрузите аватарку",
        **NULLABLE
    )
    company_name = models.TextField(
        verbose_name="Название компании",
        help_text="Введите название компании",
        **NULLABLE
    )
    inn = models.CharField(
        max_length=12,
        verbose_name="ИНН",
        help_text="Введите индивидуальный номер налогоплательщика",
        **NULLABLE
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"
