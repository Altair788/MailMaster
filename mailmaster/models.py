from django.db import models

from users.models import User

NULLABLE = {"blank": True, "null": True}


class NewsLetter(models.Model):
    """Представляет класс Рассылка"""

    PERIOD_CHOICES = [
        ("once", "Единоразовая рассылка"),
        ("days", "Ежедневная рассылка"),
        ("weeks", "Еженедельная рассылка"),
        ("months", "Ежемесячная рассылка"),
    ]
    STATUS_CHOICES = [
        ("created", "Рассылка создана"),
        ("active", "Рассылка запущена"),
        ("closed", "Рассылка завершена"),
    ]

    created_at = models.DateTimeField(
        auto_now=True, verbose_name="Дата и время создания рассылки"
    )
    start_date = models.DateTimeField(verbose_name="Дата и время отправки рассылки")
    end_date = models.DateTimeField(
        verbose_name="Дата и время отправки следующей рассылки"
    )
    period = models.CharField(
        max_length=10, verbose_name="Периодичность рассылки", choices=PERIOD_CHOICES
    )
    status = models.CharField(
        max_length=10,
        verbose_name="Статус рассылки",
        choices=STATUS_CHOICES,
        default="created",
    )

    user = models.ForeignKey(
        User, verbose_name="Пользователь рассылки", on_delete=models.CASCADE
    )
    clients = models.ManyToManyField(to="Client", verbose_name="Клиенты")
    message = models.ForeignKey(
        to="Message", verbose_name="Сообщение для рассылки", on_delete=models.CASCADE
    )

    def __str__(self):
        return (
            f"Дата и время отправки первой рассылки - {self.start_date}"
            f"Дата и время отправки следующей рассылки - {self.end_date}"
            f"Периодичность рассылки - {self.get_period_display()}"
            f"Статус рассылки - {self.get_status_display()}"
        )

    class Meta:
        verbose_name = "рассылка"
        verbose_name_plural = "рассылки"
        ordering = (
            "status",
            "period",
        )


class Client(models.Model):
    """Представляет класс Клиент"""

    name = models.CharField(max_length=250, verbose_name="ФИО")
    email = models.EmailField(unique=True, verbose_name="почта")
    comment = models.TextField(verbose_name="комментарий")

    def __str__(self):
        return f"{self.name} ({self.email})"

    class Meta:
        verbose_name = "клиент"
        verbose_name_plural = "клиенты"
        ordering = ("email",)


class Message(models.Model):
    """Представляет класс Сообщение"""

    title = models.CharField(max_length=250, verbose_name="тема письма")
    body = models.TextField(verbose_name="тело письма")

    def __str__(self):
        return f"{self.title}"

    class Meta:
        verbose_name = "письмо"
        verbose_name_plural = "письма"
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
    response = models.TextField(verbose_name="ответ почтового сервера", **NULLABLE)
    newsletter = models.ForeignKey(
        NewsLetter, verbose_name="рассылка", on_delete=models.CASCADE
    )

    def __str__(self):
        return f"Попытка рассылки: {self.last_attempt_time} - Статус: {self.get_status_display()} - Ответ: {self.response or 'Нет ответа'}"
