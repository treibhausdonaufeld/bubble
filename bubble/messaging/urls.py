from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('send/<int:item_id>/', views.send_message, name='send_message'),
    path('conversation/<int:item_id>/', views.get_conversation, name='get_conversation'),
    path('send-ajax/<int:item_id>/', views.send_message_ajax, name='send_message_ajax'),
]