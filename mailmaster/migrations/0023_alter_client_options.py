# Generated by Django 4.2.2 on 2025-02-07 17:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("mailmaster", "0022_alter_client_options_alter_message_options_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="client",
            options={
                "ordering": ("email",),
                "permissions": [
                    ("can_view_client_by_manager", "can_view_client_by_manager")
                ],
                "verbose_name": "клиент",
                "verbose_name_plural": "клиенты",
            },
        ),
    ]
