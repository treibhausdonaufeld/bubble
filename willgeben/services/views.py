from django.shortcuts import render
from django.views.generic import ListView, DetailView
from .models import Service


class ServiceListView(ListView):
    model = Service
    template_name = 'services/service_list.html'
    context_object_name = 'services'
    paginate_by = 12
    
    def get_queryset(self):
        return Service.objects.filter(active=True).select_related('user', 'category')


class ServiceDetailView(DetailView):
    model = Service
    template_name = 'services/service_detail.html'
    context_object_name = 'service'
    
    def get_queryset(self):
        return Service.objects.filter(active=True).select_related('user', 'category')