import logging

from django.core.mail import send_mail
from django.db.models import Q
from django.utils import timezone
from celery import shared_task
from datetime import timedelta

from config import settings
from mailmaster.models import EmailSendAttempt, NewsLetter
from mailmaster.utils import check_sends

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def send_mailing(self):
    try:
        # Получаем текущее время в UTC
        current_datetime_utc = timezone.now()
        #  логирование
        current_datetime = timezone.localtime(timezone.now())
        logger.info(
            f"Начало выполнения рассылки. Текущее время UTC: {current_datetime_utc}\n"
            f"Текущее время: {current_datetime}"
        )

        #  для отладки кода
        all_newsletters = NewsLetter.objects.all()
        logger.info(f"Всего рассылок в базе: {all_newsletters.count()}")

        for newsletter in all_newsletters:
            newsletter.update_status_based_on_time()
            logger.info(
                f"ID: {newsletter.id}, is_active: {newsletter.is_active},"
                f" status: {newsletter.status}, start_date: {newsletter.start_date},"
                f" end_date: {newsletter.end_date}"
            )

        #  фильтруем активные рассылки
        newsletters = NewsLetter.objects.filter(
            Q(end_date__isnull=True)
            | Q(end_date__gte=current_datetime_utc),  # позиционный аргумент
            is_active=True,  # именованный аргумент
            status__in=["created", "active", "sent_today"],  # именованный аргумент
            start_date__lte=current_datetime_utc,  # именованный аргумент
        )
        for newsletter in newsletters:
            newsletter.update_status_based_on_time()

        # Отбор активных рассылок:
        # 1. Рассылки со статусами 'active', 'created' или 'sent_today'
        # 2. Рассылки, у которых флаг sent_today установлен в True (независимо от статуса)
        #
        # Это обеспечивает включение:
        # - Всех созданных и активных рассылок
        # - Рассылок, отправленных сегодня (статус 'sent_today')
        # - Рассылок, отправленных сегодня, но статус которых еще не обновился
        active_newsletters = [
            n
            for n in newsletters
            if n.status in ["active", "created", "sent_today"] or n.sent_today is True
        ]

        logger.info(f"Найдено активных рассылок: {len(active_newsletters)}")

        for newsletter in active_newsletters:
            try:
                # Получаем список получателей
                recipient_list = list(
                    newsletter.clients.values_list("email", flat=True)
                )

                if not recipient_list:
                    logger.warning(f"Нет получателей для рассылки {newsletter.id}")
                    continue

                # Отправка письма
                successful_sends_count: int = send_mail(
                    subject=newsletter.message.title,
                    message=newsletter.message.body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=recipient_list,
                    fail_silently=False,
                )

                if successful_sends_count > 0:
                    newsletter.sent_today = True
                    newsletter.save()
                    newsletter.update_status_based_on_time()

                status: str
                response: str
                status, response = check_sends(successful_sends_count, recipient_list)

                # Создание записи о попытке отправки
                EmailSendAttempt.objects.create(
                    newsletter=newsletter, status=status, response=response
                )

                logger.info(f"Рассылка {newsletter.id}: {response}")

                # Обновление даты следующей отправки
                if newsletter.period == "days":
                    newsletter.start_date += timedelta(days=1)
                elif newsletter.period == "weeks":
                    newsletter.start_date += timedelta(weeks=1)
                elif newsletter.period == "months":
                    newsletter.start_date += timedelta(days=30)

                # Проверка, не превысила ли новая дата отправки end_date
                if newsletter.end_date and newsletter.start_date > newsletter.end_date:
                    newsletter.status = "closed"
                    newsletter.is_active = False
                    logger.info(
                        f"Рассылка {newsletter.id} завершена по достижении end_date"
                    )

                newsletter.save()

            except Exception as newsletter_error:
                # Обработка ошибок для конкретной рассылки
                EmailSendAttempt.objects.create(
                    newsletter=newsletter,
                    status="failed",
                    response=str(newsletter_error),
                )
                logger.error(
                    f"Ошибка при отправке рассылки {newsletter.id}: {newsletter_error}"
                )

        #  обновляем статусы всех активных рассылок
        newsletters_to_check = active_newsletters
        for newsletter in newsletters_to_check:
            newsletter.update_status_based_on_time()

        # Проверка и закрытие завершенных рассылок
        completed_newsletters = NewsLetter.objects.filter(
            is_active=False,
            status="closed",
        )
        for completed_newsletter in completed_newsletters:
            logger.info(f"Рассылка {completed_newsletter.id} завершена и закрыта")

    except Exception as global_error:
        logger.critical(f"Критическая ошибка в задаче рассылки: {global_error}")
        raise self.retry(exc=global_error, max_retries=3, countdown=60)


@shared_task
def test_email_sending():
    try:
        result = send_mail(
            "Тестовое письмо",
            "Это тестовое сообщение.",
            settings.DEFAULT_FROM_EMAIL,
            ["slobodyanik.ed@gmail.com"],
            fail_silently=False,
        )
        print(f"Письмо отправлено. Результат: {result}")
    except Exception as e:
        print(f"Ошибка отправки: {e}")

#  TODO: продумать защиту от попадания в блок со стороны почты за частотную рассылку
