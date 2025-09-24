from django.urls import path

from . import views

app_name = "messaging"

urlpatterns = [
    # Conversation list
    path("", views.conversation_list, name="conversation_list"),
    # Private messages (no item)
    path(
        "send/<str:username>/", views.send_private_message, name="send_private_message"
    ),
    path(
        "conversation/<str:username>/",
        views.conversation_detail,
        name="conversation_detail",
    ),
    # Item-related messages
    path("send/item/<int:item_id>/", views.send_message, name="send_message"),
    path(
        "conversation/<str:username>/item/<int:item_id>/",
        views.conversation_detail,
        name="conversation_detail_item",
    ),
    # Mark as read
    path(
        "mark-read/<str:username>/",
        views.mark_conversation_read,
        name="mark_conversation_read",
    ),
    path(
        "mark-read/<str:username>/item/<int:item_id>/",
        views.mark_conversation_read,
        name="mark_conversation_read_item",
    ),
    # AJAX endpoints
    path(
        "ajax/conversation/<int:item_id>/",
        views.get_conversation,
        name="get_conversation",
    ),
    path("ajax/send/<int:item_id>/", views.send_message_ajax, name="send_message_ajax"),
]
