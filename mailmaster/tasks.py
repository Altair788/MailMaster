import logging
from django.core.mail import send_mail
from django.utils import timezone
from celery import shared_task
from datetime import timedelta

from config import settings
from mailmaster.models import EmailSendAttempt, NewsLetter

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def send_mailing(self):
    try:
        current_datetime = timezone.now()
        logger.info(f"Начало выполнения рассылки. Текущее время: {current_datetime}")

        newsletters = NewsLetter.objects.filter(
            is_active=True,
            status='active',
            start_date__lte=current_datetime,
            end_date__gt=current_datetime  # Добавляем проверку end_date
        )
        logger.info(f"Найдено активных рассылок: {newsletters.count()}")

        for newsletter in newsletters:
            try:
                # Получаем список получателей
                recipient_list = list(newsletter.clients.values_list('email', flat=True))

                if not recipient_list:
                    logger.warning(f"Нет получателей для рассылки {newsletter.id}")
                    continue

                # Отправка письма
                result = send_mail(
                    subject=newsletter.message.title,
                    message=newsletter.message.body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=recipient_list,
                    fail_silently=False,
                )

                # Создание записи о попытке отправки
                EmailSendAttempt.objects.create(
                    newsletter=newsletter,
                    status='success',
                    response=f"Отправлено получателей: {len(recipient_list)}"
                )

                logger.info(f"Рассылка {newsletter.id} успешно отправлена")

                # Обновление даты следующей отправки
                if newsletter.period == 'days':
                    newsletter.start_date += timedelta(days=1)
                elif newsletter.period == 'weeks':
                    newsletter.start_date += timedelta(weeks=1)
                elif newsletter.period == 'months':
                    newsletter.start_date += timedelta(days=30)

                # Проверка, не превысила ли новая дата отправки end_date
                if newsletter.end_date and newsletter.start_date > newsletter.end_date:
                    newsletter.status = 'closed'
                    newsletter.is_active = False
                    logger.info(f"Рассылка {newsletter.id} завершена по достижении end_date")

                newsletter.save()

            except Exception as newsletter_error:
                # Обработка ошибок для конкретной рассылки
                EmailSendAttempt.objects.create(
                    newsletter=newsletter,
                    status='failed',
                    response=str(newsletter_error)
                )
                logger.error(f"Ошибка при отправке рассылки {newsletter.id}: {newsletter_error}")

        # Проверка и закрытие завершенных рассылок
        completed_newsletters = NewsLetter.objects.filter(
            is_active=True,
            status='active',
            end_date__lte=current_datetime
        )
        for completed_newsletter in completed_newsletters:
            completed_newsletter.status = 'closed'
            completed_newsletter.is_active = False
            completed_newsletter.save()
            logger.info(f"Рассылка {completed_newsletter.id} завершена и закрыта")

    except Exception as global_error:
        logger.critical(f"Критическая ошибка в задаче рассылки: {global_error}")
        raise self.retry(exc=global_error, max_retries=3, countdown=60)


@shared_task
def test_email_sending():
    try:
        result = send_mail(
            'Тестовое письмо',
            'Это тестовое сообщение.',
            settings.DEFAULT_FROM_EMAIL,
            ['slobodyanik.ed@gmail.com'],
            fail_silently=False,
        )
        print(f"Письмо отправлено. Результат: {result}")
    except Exception as e:
        print(f"Ошибка отправки: {e}")
