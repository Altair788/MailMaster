from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from mailmaster.models import Client, NewsLetter, Message


class Command(BaseCommand):
    help = "Создаёт группу 'Менеджеры' и назначает ей права"

    def handle(self, *args, **kwargs):
        # Создаём или получаем группу «Менеджеры»
        managers_group, created = Group.objects.get_or_create(name='Менеджеры')

        if created:
            self.stdout.write(self.style.SUCCESS("Группа 'Менеджеры' успешно создана."))
        else:
            self.stdout.write(self.style.WARNING("Группа 'Менеджеры' уже существует."))

        # Получаем права для моделей
        client_permissions = Permission.objects.filter(
            content_type=ContentType.objects.get_for_model(Client),
            codename__in=["can_view_client_by_manager"]
        )

        newsletter_permissions = Permission.objects.filter(
            content_type=ContentType.objects.get_for_model(NewsLetter),
            codename__in=["can_view_newsletter_by_manager", "can_change_newsletter_by_manager"]
        )

        message_permissions = Permission.objects.filter(
            content_type=ContentType.objects.get_for_model(Message),
            codename__in=["can_view_message_by_manager"]
        )

        # Назначаем права группе «Менеджеры»
        managers_group.permissions.set(
            list(client_permissions) +
            list(newsletter_permissions) +
            list(message_permissions)
        )
        managers_group.save()

        self.stdout.write(self.style.SUCCESS("Права успешно добавлены группе 'Менеджеры'."))
