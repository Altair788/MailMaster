# Generated by Django 4.2.2 on 2025-02-06 19:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mailmaster", "0018_alter_newsletter_clients"),
    ]

    operations = [
        migrations.AlterField(
            model_name="newsletter",
            name="status",
            field=models.CharField(
                choices=[
                    ("created", "Создана"),
                    ("active", "Запущена"),
                    ("sent_today", "Отправлена"),
                    ("closed", "Завершена"),
                    ("paused", "Приостановлена"),
                ],
                default="created",
                max_length=10,
                verbose_name="Статус",
            ),
        ),
    ]
