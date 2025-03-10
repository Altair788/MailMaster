# Generated by Django 4.2.2 on 2025-01-28 15:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mailmaster", "0014_alter_client_comment_alter_emailsendattempt_response"),
    ]

    operations = [
        migrations.AlterField(
            model_name="newsletter",
            name="status",
            field=models.CharField(
                choices=[
                    ("created", "Создана"),
                    ("active", "Запущена"),
                    ("closed", "Завершена"),
                    ("paused", "Приостановлена"),
                ],
                default="created",
                max_length=10,
                verbose_name="Статус",
            ),
        ),
    ]
