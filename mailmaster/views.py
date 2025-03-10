from django.utils import timezone

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin,
                                        UserPassesTestMixin)
from django.forms import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from mailmaster.tasks import send_mailing

from mailmaster.forms import MessageForm, NewsLetterForm
from mailmaster.models import Client, Message, NewsLetter, EmailSendAttempt
from mailmaster.services import get_newsletter_from_cache
from django.core.mail import send_mail
from config import settings
from django.db.models import Count


@login_required
def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")
        print(f"name: {name}\nemail: {email}\nmessage: {message}\n")

    context = {"title": "Контакты"}
    return render(request, "mailmaster/contact.html", context)


#  CRUD для рассылок


@method_decorator(never_cache, name="dispatch")
class NewsLetterListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = NewsLetter
    permission_required = "mailmaster.view_newsletter"
    paginate_by = 3

    def get_queryset(self):
        if self.request.user.has_perm("mailmaster.can_view_by_manager"):
            return NewsLetter.objects.all()
        return NewsLetter.objects.filter(owner=self.request.user).order_by('-created_at')


    def get_context_data(self, **kwargs):
        #  Дя отображения на главной странице статистики
        context = super().get_context_data(**kwargs)

        context['all_newsletters'] = self.model.objects.count()

        # Количество активных рассылок (не завершённых и не приостановленных)
        context['active_newsletters'] = self.model.objects.exclude(
            status__in=["closed", "paused"]
        ).count()

        # Подсчет уникальных клиентов, которые связаны хотя бы с одной рассылкой
        unique_clients = Client.objects.filter(newsletters__isnull=False).distinct().count()

        context['unique_clients'] = unique_clients

        return context


class NewsLetterDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = NewsLetter
    permission_required = "mailmaster.view_newsletter"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Обновляем статус рассылки перед передачей в шаблон
        self.object.update_status_based_on_time()

        # Получаем всех клиентов, связанных с текущей рассылкой
        context['clients'] = self.object.clients.all()
        # context['subjects'] = get_newsletter_from_cache(self.object.pk)
        return context

    def get_queryset(self):
        if self.request.user.has_perm("mailmaster.can_view_by_manager"):
            return NewsLetter.objects.all()
        return NewsLetter.objects.filter(owner=self.request.user).order_by('-created_at')


class NewsLetterCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = NewsLetter
    success_url = reverse_lazy("mailmaster:index")
    form_class = NewsLetterForm
    permission_required = "mailmaster.add_newsletter"

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        send_mailing()
        return response


class NewsLetterUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = NewsLetter
    success_url = reverse_lazy("mailmaster:index")
    form_class = NewsLetterForm
    permission_required = "mailmaster.change_newsletter"

    def get_success_url(self):
        return reverse("mailmaster:view_newsletter", args=[self.kwargs.get("pk")])

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        # Получаем всех клиентов для отображения в форме
        context_data["clients"] = Client.objects.all()
        return context_data

    def form_valid(self, form):
        newsletter = form.save(commit=False)
        newsletter.user = self.request.user
        newsletter.save()
        form.save_m2m()
        return super().form_valid(form)

    def get_queryset(self):
        if self.request.user.has_perm("mailmaster.can_change_by_manager"):
            return NewsLetter.objects.all()
        return NewsLetter.objects.filter(owner=self.request.user).order_by('-created_at')


class NewsLetterDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = NewsLetter
    success_url = reverse_lazy("mailmaster:index")

    def test_func(self):
        return self.request.user.is_superuser

    def get_queryset(self):
        return NewsLetter.objects.filter(owner=self.request.user)


#  функция переключения тестовой кнопки (демо) Не используется на проде

def toggle_activity(request, pk):
    newsletter_item = get_object_or_404(NewsLetter, pk=pk)
    if newsletter_item.is_active:
        newsletter_item.is_active = False
    else:
        newsletter_item.is_active = True

    newsletter_item.save()

    return redirect(reverse("mailmaster:index"))


@login_required
@permission_required('mailmaster.change_newsletter', raise_exception=True)
def send_newsletter_now(request, pk):
    newsletter = get_object_or_404(NewsLetter, pk=pk)

    # Проверяем, можно ли отправить рассылку
    if newsletter.status in ["closed", "paused"]:
        messages.error(
            request,
            f"Рассылка '{newsletter.message.title}' не может быть отправлена сейчас. Текущий статус: {newsletter.get_status_display()}."
        )
        return redirect("mailmaster:index")

    # Устанавливаем время начала на текущее время и статус "active"
    newsletter.start_date = timezone.now()
    newsletter.status = "active"
    newsletter.save()
    #  TODO: создать отдельную таску и запускать delay
    send_mailing()

    messages.success(request, f"Рассылка '{newsletter.message.title}' запущена на отправку.")
    return redirect("mailmaster:index")


#  функция для приостановления/возобновления рассылки

@login_required
@permission_required('mailmaster.change_newsletter', raise_exception=True)
def toggle_newsletter_status(request, pk):
    newsletter = get_object_or_404(NewsLetter, pk=pk)

    if newsletter.status == "active":
        # Приостановка активной рассылки
        newsletter.status = "paused"
        messages.warning(
            request,
            f"Рассылка '{newsletter.message.title}' приостановлена. "
            f"Следующая отправка была запланирована на {newsletter.start_date.strftime('%d.%m.%Y %H:%M')}.",
        )
    elif newsletter.status == "paused":
        # Возобновление приостановленной рассылки
        if newsletter.end_date and timezone.now() >= newsletter.end_date:
            # Нельзя возобновить рассылку, если срок завершения истёк
            messages.error(
                request,
                f"Невозможно возобновить рассылку '{newsletter.message.title}', так как её срок завершения истёк.",
            )
        else:
            newsletter.status = "active"
            messages.success(
                request,
                f"Рассылка '{newsletter.message.title}' возобновлена. "
                f"Следующая отправка запланирована на {newsletter.start_date.strftime('%d.%m.%Y %H:%M')}.",
            )
    elif newsletter.status == "created":

        # Логика для статуса "Создана"
        if timezone.now() >= newsletter.start_date:
            # Если время начала уже наступило, переводим в "Запущена"
            newsletter.status = "active"
            messages.success(
                request,
                f"Рассылка '{newsletter.message.title}' переведена в статус 'Запущена'.",
            )
        else:
            messages.warning(
                request,
                f"Рассылка '{newsletter.message.title}' ещё не может быть приостановлена, так как время начала не наступило.",
            )
    elif newsletter.status == "sent_today":
        # Логика для статуса "Отправлена сегодня"
        newsletter.status = "paused"
        # messages.info(
        #     request,
        #     f"Рассылка '{newsletter.message.title}' уже отправлена сегодня. "
        #     f"Она автоматически перейдёт в статус 'Запущена' завтра.",
        # )
        messages.warning(
            request,
            f"Рассылка '{newsletter.message.title}' приостановлена. "
            f"Следующая отправка была запланирована на {newsletter.start_date.strftime('%d.%m.%Y %H:%M')}.",
        )
    elif newsletter.status == "closed":
        # Логика для статуса "Завершена"
        messages.error(
            request,
            f"Невозможно изменить статус рассылки '{newsletter.message.title}', так как она завершена.",
        )
    else:
        # Обработка неизвестных статусов
        messages.error(
            request,
            f"Невозможно изменить статус рассылки '{newsletter.message.title}'. "
            f"Текущий статус: {newsletter.get_status_display()}.",
        )

    newsletter.save()

    return redirect("mailmaster:index")


#  CRUD for message


class MessageCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Message
    success_url = reverse_lazy("mailmaster:index")
    form_class = MessageForm
    permission_required = "mailmaster.add_message"


class MessageDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Message
    permission_required = "mailmaster.view_message"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Получаем все рассылки, связанные с текущим сообщением (обратная связь через ForeignKey)
        context["newsletters"] = NewsLetter.objects.filter(message=self.object)
        return context

    def get_queryset(self):
        # Если пользователь имеет право "can_view_by_manager", он видит все сообщения
        if self.request.user.has_perm("mailmaster.can_view_by_manager"):
            return Message.objects.all()
        # Иначе пользователь видит только свои сообщения
        return Message.objects.filter(owner=self.request.user)


class MessageUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Message
    form_class = MessageForm
    template_name = "mailmaster/message_form.html"
    success_url = reverse_lazy("mailmaster:message_list")
    permission_required = "mailmaster.change_message"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Редактирование сообщения"
        # Получаем связанные рассылки
        context["newsletters"] = NewsLetter.objects.filter(message=self.object)
        return context

    def form_valid(self, form):
        self.object = form.save()
        return super().form_valid(form)

    def get_queryset(self):
        return Message.objects.filter(owner=self.request.user)


class MessageDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Message
    success_url = reverse_lazy("mailmaster:message_list")

    def test_func(self):
        return self.request.user.is_superuser

    def get_queryset(self):
        return Message.objects.filter(owner=self.request.user)


class MessageListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Message
    permission_required = "mailmaster.view_message"

    def get_queryset(self):
        if self.request.user.has_perm("mailmaster.can_view_by_manager"):
            return Message.objects.all()
        # Иначе пользователь видит только свои сообщения
        return Message.objects.filter(owner=self.request.user)


#  CRUD for client


class ClientListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Client
    permission_required = "mailmaster.view_client"

    def get_queryset(self):
        if self.request.user.has_perm("mailmaster.can_view_by_manager"):
            return Client.objects.all()
        return Client.objects.filter(owner=self.request.user)


class ClientDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Client
    permission_required = "mailmaster.view_client"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Получаем все рассылки, связанные с текущим клиентом (обратная связь через ForeignKey)
        context["newsletters"] = NewsLetter.objects.filter(clients=self.object)
        return context

    def get_queryset(self):
        if self.request.user.has_perm("mailmaster.can_view_by_manager"):
            return Client.objects.all()
        return Client.objects.filter(owner=self.request.user)

class ClientCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Client
    fields = ["email", "name", "comment"]
    success_url = reverse_lazy("mailmaster:index")
    permission_required = "mailmaster.add_client"


class ClientUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Client
    fields = ["email", "name", "comment"]
    success_url = reverse_lazy("mailmaster:client_list")
    permission_required = "mailmaster.change_client"

    def get_queryset(self):
        return Client.objects.filter(owner=self.request.user)


class ClientDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Client
    success_url = reverse_lazy("mailmaster:client_list")
    permission_required = "mailmaster.view_client"

    def test_func(self):
        return self.request.user.is_superuser

    def get_queryset(self):
        return Client.objects.filter(owner=self.request.user)


# CRUD for EmailSendAttempt
class EmailSendAttemptListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = EmailSendAttempt
    permission_required = "mailmaster.view_email_send_attempt"


class EmailSendAttemptDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = EmailSendAttempt
    permission_required = "mailmaster.view_email_send_attempt"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Получаем все рассылки, связанные с текущей попыткой (обратная связь через ForeignKey)
        context["newsletters"] = NewsLetter.objects.filter(attempts=self.object)
        return context


class EmailSendAttemptDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = EmailSendAttempt
    success_url = reverse_lazy("mailmaster:email_send_attempt_list")
    permission_required = "mailmaster.view_email_send_attempt"

    def test_func(self):
        return self.request.user.is_superuser
