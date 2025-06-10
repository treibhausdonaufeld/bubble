from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    path('', views.ServiceListView.as_view(), name='list'),
    path('<int:pk>/', views.ServiceDetailView.as_view(), name='detail'),
]