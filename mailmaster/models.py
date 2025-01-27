from django.db import models

from users.models import User

NULLABLE = {"blank": True, "null": True}


class Client(models.Model):
    """Представляет класс Клиент"""

    name = models.CharField(max_length=250, verbose_name="ФИО")
    email = models.EmailField(unique=True, verbose_name="почта")
    comment = models.TextField(verbose_name="комментарий", blank=True)

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
        ("closed", "Завершена"),
    ]

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    start_date = models.DateTimeField(verbose_name="Дата начала рассылки")
    end_date = models.DateTimeField(verbose_name="Дата окончания рассылки", null=True, blank=True)
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, verbose_name="Периодичность")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="created", verbose_name="Статус")

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Создатель")
    clients = models.ManyToManyField(Client, verbose_name="Клиенты")
    message = models.ForeignKey("Message", on_delete=models.CASCADE, verbose_name="Сообщение")

    def update_status(self, new_status):
        if new_status in dict(self.STATUS_CHOICES):
            self.status = new_status
            self.save()
        else:
            raise ValueError("Недопустимый статус")
    def __str__(self):
        return f"Рассылка: {self.get_status_display()} - Начало: {self.start_date}"

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ["-created_at"]



class Message(models.Model):
    """Представляет класс Сообщение"""

    title = models.CharField(max_length=250, verbose_name="тема письма")
    body = models.TextField(verbose_name="тело письма")

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
