from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.forms import inlineformset_factory
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from mailmaster.forms import NewsLetterForm, ClientForm
from mailmaster.models import NewsLetter, Client
from mailmaster.services import get_newsletter_from_cache


@login_required
def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")
        print(f"name: {name}\nemail: {email}\nmessage: {message}\n")

    context = {
        'title': 'Контакты'
    }
    return render(request, 'mailmaster/contact.html', context)


class NewsLetterListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = NewsLetter
    permission_required = 'mailmaster.view_newsletter'



class NewsLetterDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = NewsLetter
    permission_required = 'mailmaster.view_newsletter'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['subjects'] = get_newsletter_from_cache(self.object.pk)
        return context_data



class NewsLetterCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = NewsLetter
    success_url = reverse_lazy('mailmaster:index')
    form_class = NewsLetterForm
    permission_required = 'mailmaster.add_newsletter'


class NewsLetterUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = NewsLetter
    success_url = reverse_lazy('mailmaster:index')
    form_class = NewsLetterForm
    permission_required = 'mailmaster.change_newsletter'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        SubjectFormset = inlineformset_factory(NewsLetter, Client, form=ClientForm, extra=1)
        if self.request.method == 'POST':
            context_data['formset'] = SubjectFormset(self.request.POST, instance=self.object)
        else:
            context_data['formset'] = SubjectFormset(instance=self.object)
        return context_data

    def form_valid(self, form):
        formset = self.get_context_data()['formset']
        self.object = form.save()
        if formset.is_valid():
            formset.instance = self.object
            formset.save()

        return super().form_valid(form)



class NewsLetterDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = NewsLetter
    success_url = reverse_lazy('mailmaster:index')

    def test_func(self):
        return self.request.user.is_superuser



def toggle_activity(request, pk):
    newsletter_item = get_object_or_404(NewsLetter, pk=pk)
    if newsletter_item.is_active:
        newsletter_item.is_active = False
    else:
        newsletter_item.is_active = True

    newsletter_item.save()

    return redirect(reverse('main:index'))