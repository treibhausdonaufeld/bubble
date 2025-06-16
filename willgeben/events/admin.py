from django.contrib import admin
from .models import Event, EventTagRelation


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'organizer', 'event_type', 'start_date', 'attendee_count', 'is_upcoming', 'active']
    list_filter = ['event_type', 'active', 'intern', 'registration_required', 'start_date']
    search_fields = ['name', 'description', 'organizer__username', 'location']
    readonly_fields = ['date_created', 'date_updated', 'attendee_count', 'is_upcoming', 'has_space']
    filter_horizontal = ['attendees']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'organizer', 'event_type')
        }),
        ('Schedule & Location', {
            'fields': ('start_date', 'end_date', 'is_full_day', 'start_time', 'end_time', 'location')
        }),
        ('Participation', {
            'fields': ('attendees', 'max_attendees', 'registration_required')
        }),
        ('Event Details', {
            'fields': ('price', 'requirements', 'materials_needed', 'contact_info')
        }),
        ('Settings', {
            'fields': ('active', 'intern')
        }),
        ('Statistics', {
            'fields': ('attendee_count', 'is_upcoming', 'has_space'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('date_created', 'date_updated'),
            'classes': ('collapse',)
        })
    )


@admin.register(EventTagRelation)
class EventTagRelationAdmin(admin.ModelAdmin):
    list_display = ['event', 'tag']
    list_filter = ['tag']
    search_fields = ['event__name', 'tag__name']