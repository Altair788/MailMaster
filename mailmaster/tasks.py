from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone

from config import settings
from mailmaster.models import EmailSendAttempt, NewsLetter


@shared_task
def send_mailing():
    current_datetime = timezone.now()
    print(f"Текущее время: {current_datetime}")

    newsletters = NewsLetter.objects.filter(is_active=True, status='active')
    print(f"Найдено активных рассылок: {newsletters.count()}")

    for newsletter in newsletters:
        print(f"Обработка рассылки: {newsletter.message.title}")
        print(newsletter.start_date)
        print(newsletter.end_date)
        if newsletter.start_date <= current_datetime <= newsletter.end_date:
            last_attempt = EmailSendAttempt.objects.filter(newsletter=newsletter).order_by('-last_attempt_time').first()
            print(f"Последняя попытка отправки: {last_attempt}")

            if (newsletter.period == 'once' and last_attempt) or \
               (last_attempt and (current_datetime - last_attempt.last_attempt_time).days <
                (1 if newsletter.period == 'days' else 7 if newsletter.period == 'weeks' else 30)):
                print("Пропускаем рассылку.")
                continue

            recipient_list = list(newsletter.clients.values_list('email', flat=True))
            print(f"Список получателей: {recipient_list}")

            if recipient_list:
                try:
                    send_mail(
                        subject=newsletter.message.title,
                        message=newsletter.message.body,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=recipient_list,
                        fail_silently=False,
                    )
                    EmailSendAttempt.objects.create(newsletter=newsletter, status='success')
                    print("Рассылка успешно отправлена.")
                except Exception as e:
                    EmailSendAttempt.objects.create(newsletter=newsletter, status='failed', response=str(e))
                    print(f"Ошибка при отправке рассылки: {e}")