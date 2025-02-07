from django.core.management.base import BaseCommand
from mailmaster.tasks import send_mailing


class Command(BaseCommand):
    help = "Запускает отправку всех активных рассылок"

    def handle(self, *args, **kwargs):
        self.stdout.write("Запуск отправки рассылок...")

        # Запускаем задачу Celery для отправки рассылок
        send_mailing.delay()

        self.stdout.write(self.style.SUCCESS("Задача по отправке рассылок успешно запущена!"))
