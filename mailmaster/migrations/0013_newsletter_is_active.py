# Generated by Django 4.2.2 on 2024-11-22 13:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "mailmaster",
            "0012_alter_newsletter_options_remove_newsletter_is_active_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="newsletter",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
    ]
