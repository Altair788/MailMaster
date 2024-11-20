from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin,
                                        UserPassesTestMixin)
from django.forms import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from mailmaster.forms import ClientForm, MessageForm, NewsLetterForm
from mailmaster.models import Client, Message, NewsLetter
from mailmaster.services import get_newsletter_from_cache


@login_required
def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")
        print(f"name: {name}\nemail: {email}\nmessage: {message}\n")

    context = {"title": "Контакты"}
    return render(request, "mailmaster/contact.html", context)


class NewsLetterListView(LoginRequiredMixin, ListView):
    model = NewsLetter
    permission_required = "mailmaster.view_newsletter"


class NewsLetterDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = NewsLetter
    permission_required = "mailmaster.view_newsletter"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["subjects"] = get_newsletter_from_cache(self.object.pk)
        return context_data


class NewsLetterCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = NewsLetter
    success_url = reverse_lazy("mailmaster:index")
    form_class = NewsLetterForm
    permission_required = "mailmaster.add_newsletter"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


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
        self.object = form.save()  # Сохраняем основной объект
        form.save_m2m()  # Сохраняем связи ManyToManyField
        return super().form_valid(form)


class NewsLetterDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = NewsLetter
    success_url = reverse_lazy("mailmaster:index")

    # def get_success_url(self):
    #     # Получаем pk удаляемого объекта
    #     return reverse_lazy("mailmaster:view_newsletter", args=[self.object.pk])

    def test_func(self):
        return self.request.user.is_superuser

def toggle_activity(request, pk):
    newsletter_item = get_object_or_404(NewsLetter, pk=pk)
    if newsletter_item.is_active:
        newsletter_item.is_active = False
    else:
        newsletter_item.is_active = True

    newsletter_item.save()

    return redirect(reverse("mailmaster:index"))


#  CRUD for message


class MessageCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Message
    success_url = reverse_lazy("mailmaster:index")
    form_class = MessageForm
    permission_required = "mailmaster.add_message"


class MessageDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Message
    permission_required = "mailmaster.view_message"


class MessageUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Message
    form_class = MessageForm
    template_name = "mailmaster/message_form.html"
    success_url = reverse_lazy("mailmaster:index")
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


class MessageDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Message
    success_url = reverse_lazy("mailmaster:view_message")


class MessageListView(LoginRequiredMixin, ListView):
    model = Message
    permission_required = "mailmaster.view_message"


#  CRUD for client


class ClientListView(LoginRequiredMixin, ListView):
    model = Client


class ClientDetailView(LoginRequiredMixin, DetailView):
    model = Client


class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    fields = ["email", "name", "comment"]
    success_url = reverse_lazy("mailmaster:index")


class ClientUpdateView(LoginRequiredMixin, UpdateView):
    model = Client
    fields = ["email", "name", "comment"]
    success_url = reverse_lazy("mailmaster:view_client")


class ClientDeleteView(LoginRequiredMixin, DeleteView):
    model = Client
    success_url = reverse_lazy("mailmaster:view_client")
