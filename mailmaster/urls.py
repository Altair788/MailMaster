from django.urls import path
from django.views.decorators.cache import cache_page

from mailmaster.apps import MailmasterConfig
from mailmaster.views import (
    MessageCreateView,
    MessageDeleteView,
    MessageDetailView,
    MessageListView,
    MessageUpdateView,
    NewsLetterCreateView,
    NewsLetterDeleteView,
    NewsLetterDetailView,
    NewsLetterListView,
    NewsLetterUpdateView,
    contact,
    ClientCreateView,
    ClientListView,
    ClientDetailView,
    ClientUpdateView,
    ClientDeleteView,
    toggle_activity,
    toggle_newsletter_status, EmailSendAttemptListView,
)

app_name = MailmasterConfig.name

urlpatterns = [
    path("", NewsLetterListView.as_view(), name="index"),
    path("contact/", contact, name="contact"),
    path("view/<int:pk>/", NewsLetterDetailView.as_view(), name="view_newsletter"),
    path("create/", NewsLetterCreateView.as_view(), name="create_newsletter"),
    path("edit/<int:pk>/", NewsLetterUpdateView.as_view(), name="update_newsletter"),
    path("delete/<int:pk>/", NewsLetterDeleteView.as_view(), name="delete_newsletter"),
    path("toggle/<int:pk>/", toggle_newsletter_status, name="toggle_newsletter_status"),
    path("message/", MessageListView.as_view(), name="message_list"),
    path("create/message/", MessageCreateView.as_view(), name="create_message"),
    path("message/view/<int:pk>/", MessageDetailView.as_view(), name="view_message"),
    path("message/edit/<int:pk>/", MessageUpdateView.as_view(), name="update_message"),
    path(
        "message/delete/<int:pk>/", MessageDeleteView.as_view(), name="delete_message"
    ),
    path("clients/", cache_page(5)(ClientListView.as_view()), name="client_list"),
    path("clients/create/", ClientCreateView.as_view(), name="create_client"),
    path("clients/view/<int:pk>/", ClientDetailView.as_view(), name="view_client"),
    path("clients/edit/<int:pk>/", ClientUpdateView.as_view(), name="update_client"),
    path("clients/delete/<int:pk>/", ClientDeleteView.as_view(), name="delete_client"),
    path("activity/<int:pk>/", toggle_activity, name="toggle_activity"),

    path("email_send_attempts/", cache_page(5)(EmailSendAttemptListView.as_view()), name="email_send_attempt_list"),
    path("email_send_attempts/view/<int:pk>/", EmailSendAttemptDetailView.as_view(), name="view_email_send_attempt"),
    path("email_send_attempts/delete/<int:pk>/", EmailSendAttemptDeleteView.as_view(), name="delete_email_send_attempt"),

]
