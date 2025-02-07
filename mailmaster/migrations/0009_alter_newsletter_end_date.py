# Generated by Django 4.2.2 on 2024-11-22 13:11

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("mailmaster", "0008_alter_newsletter_end_date"),
    ]

    operations = [
        migrations.AlterField(
            model_name="newsletter",
            name="end_date",
            field=models.DateTimeField(
                default=django.utils.timezone.now,
                verbose_name="Дата и время отправки следующей рассылки",
            ),
        ),
    ]
