from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.utils import timezone
from .models import Event


class EventListView(ListView):
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    paginate_by = 12
    
    def get_queryset(self):
        return Event.objects.filter(
            active=True,
            start_datetime__gte=timezone.now()
        ).select_related('organizer').prefetch_related('attendees')


class EventDetailView(DetailView):
    model = Event
    template_name = 'events/event_detail.html'
    context_object_name = 'event'
    
    def get_queryset(self):
        return Event.objects.filter(active=True).select_related('organizer').prefetch_related('attendees')