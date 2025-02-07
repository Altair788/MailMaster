from django.db import models
from django.utils import timezone

from users.models import User

NULLABLE = {"blank": True, "null": True}


class Client(models.Model):
    """Представляет класс Клиент"""

    name = models.CharField(max_length=250, verbose_name="ФИО")
    email = models.EmailField(unique=True, verbose_name="почта")
    comment = models.TextField(verbose_name="комментарий", blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец", default=1)

    def __str__(self):
        return f"{self.name} ({self.email})"

    class Meta:
        verbose_name = "клиент"
        verbose_name_plural = "клиенты"
        ordering = ("email",)


class NewsLetter(models.Model):
    """Представляет класс Рассылка"""

    PERIOD_CHOICES = [
        ("days", "Ежедневная рассылка"),
        ("weeks", "Еженедельная рассылка"),
        ("months", "Ежемесячная рассылка"),
    ]

    STATUS_CHOICES = [
        ("created", "Создана"),
        ("active", "Запущена"),
        ("sent_today", "Отправлена"),
        ("closed", "Завершена"),
        ("paused", "Приостановлена"),
    ]

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    start_date = models.DateTimeField(verbose_name="Дата начала рассылки")
    end_date = models.DateTimeField(
        verbose_name="Дата окончания рассылки", null=True, blank=True
    )
    period = models.CharField(
        max_length=10, choices=PERIOD_CHOICES, verbose_name="Периодичность"
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="created", verbose_name="Статус"
    )
    sent_today = models.BooleanField(default=False)

    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец", default=1)

    #  позволяет получить в контроллере всех клиентов, связанных с текущей рассылкой (обратная связь через ManyToMany)
    # context['clients'] = self.object.clients.all()
    clients = models.ManyToManyField(Client, verbose_name="Клиенты", related_name='newsletters')

    # позволяет получить в контроллере все рассылки, связанные с текущим сообщением (обратная связь через ForeignKey)
    # context['newsletters'] = NewsLetter.objects.filter(message=self.object)
    message = models.ForeignKey(
        "Message", on_delete=models.CASCADE, verbose_name="Сообщение"
    )

    def update_status_based_on_time(self):
        """
        Автоматически обновляет статус рассылки на основе текущего времени.
        """
        current_time = timezone.now()
        #  TODO: предусмотреть обработку случая, когда время отправки и время
        #   окончания схожи (до минуты) и идет возврат None.
        print(f"Текущее время (UTC): {current_time}")
        print(f"Дата окончания (UTC): {self.end_date}")
        print(f"Текущий статус: {self.status}")

        if self.status == "created" and current_time >= self.start_date:
            # Если статус "Создана" и время начала наступило
            self.status = "active"
            self.save()
        elif (
            self.status in ["active", "sent_today"]
            and self.end_date
            and current_time >= self.end_date
        ):
            # Если статус "Активна" или "Отправлена сегодня" и время окончания прошло
            self.status = "closed"
            self.is_active = False
            print("Статус обновлён на 'closed'")
            self.save()
        elif (
            self.status == "sent_today" and current_time.date() > self.start_date.date()
        ):
            # Если статус "Отправлена сегодня" и наступил новый день
            self.status = "active"
            self.sent_today = False
            self.save()
        elif self.sent_today and self.status != "sent_today":
            # Если рассылка была отправлена сегодня, но статус не обновлен
            self.status = "sent_today"
            self.save()
        elif (
            self.status == "sent_today"
            and self.end_date
            and current_time < self.end_date
        ):
            # Если статус "Отправлена сегодня" и текущая дата больше даты последнего отправления
            self.status = "active"
            self.save()

    def __str__(self):
        return f"Рассылка: {self.get_status_display()} - Начало: {timezone.localtime(self.start_date)}"

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ["-created_at"]


class Message(models.Model):
    """Представляет класс Сообщение"""

    title = models.CharField(max_length=250, verbose_name="тема письма")
    body = models.TextField(verbose_name="тело письма")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец", default=1)

    def __str__(self):
        return f"{self.title}"

    class Meta:
        verbose_name = "сообщение"
        verbose_name_plural = "сообщения"
        ordering = ("title",)


class EmailSendAttempt(models.Model):
    """Представляет класс Попытка рассылки"""

    STATUS_CHOICES = [
        ("success", "Успешно"),
        ("failed", "Не успешно"),
    ]
    last_attempt_time = models.DateTimeField(
        auto_now_add=True, verbose_name="дата и время последней попытки"
    )
    status = models.CharField(
        max_length=10, verbose_name="статус попытки", choices=STATUS_CHOICES
    )
    response = models.TextField(verbose_name="ответ почтового сервера", blank=True)

    # Позволяет получить в контроллере все рассылки, связанные с текущей попыткой (обратная связь через ForeignKey)
    # context["newsletters"] = NewsLetter.objects.filter(attempts=self.object)
    newsletter = models.ForeignKey(
        NewsLetter,
        verbose_name="рассылка",
        on_delete=models.CASCADE,
        related_name="attempts",
    )

    def __str__(self):
        return f"Попытка рассылки: {self.last_attempt_time} - Статус: {self.get_status_display()} - Ответ: {self.response or 'Нет ответа'}"

    class Meta:
        verbose_name = "попытка рассылки"
        verbose_name_plural = "попытка рассылок"
        ordering = ["-last_attempt_time"]
