from django.utils import timezone
from django.core.mail import send_mail
from .models import NewsLetter, EmailSendAttempt
from django.conf import settings


def send_mailing():
    print("Запуск функции send_mailing")
    current_datetime = timezone.now()

    # Получаем все активные рассылки, которые нужно отправить
    newsletters = NewsLetter.objects.filter(
        start_date__lte=current_datetime,  # Началась или начнется сейчас
        end_date__gte=current_datetime,  # Заканчивается позже текущего времени
        is_active=True,
        status='active'
    )

    print(f"Найдено рассылок: {newsletters.count()}")

    for newsletter in newsletters:
        # Проверяем последнюю попытку рассылки
        last_attempt = EmailSendAttempt.objects.filter(newsletter=newsletter).order_by('-last_attempt_time').first()

        # Если это единоразовая рассылка и она уже отправлялась, пропускаем её
        if newsletter.period == 'once' and last_attempt:
            continue

        # Если последняя попытка не найдена, или прошло достаточно времени с последней попытки
        if last_attempt:
            time_since_last_attempt = current_datetime - last_attempt.last_attempt_time

            # Пропускаем, если еще не прошло достаточно времени для повторной отправки
            if (newsletter.period == 'days' and time_since_last_attempt.days < 1) or \
                    (newsletter.period == 'weeks' and time_since_last_attempt.days < 7) or \
                    (newsletter.period == 'months' and time_since_last_attempt.days < 30):
                continue

        # Отправляем письма клиентам
        recipient_list = [client.email for client in newsletter.clients.all()]

        try:
            send_mail(
                subject=newsletter.title,
                message=newsletter.message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list,
                fail_silently=False,
            )
            # Записываем успешную попытку
            EmailSendAttempt.objects.create(
                newsletter=newsletter,
                status='success',
                response='Email sent successfully'
            )
        except Exception as e:
            # Записываем неудачную попытку
            EmailSendAttempt.objects.create(
                newsletter=newsletter,
                status='failed',
                response=str(e)
            )