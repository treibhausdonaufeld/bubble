from django.contrib import admin
from .models import Service, ServiceTagRelation


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'category', 'price', 'active', 'date_created']
    list_filter = ['active', 'category', 'intern', 'th_payment', 'date_created']
    search_fields = ['name', 'description', 'user__username']
    readonly_fields = ['date_created', 'date_updated']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'user')
        }),
        ('Service Details', {
            'fields': ('price', 'duration', 'location', 'availability')
        }),
        ('Settings', {
            'fields': ('active', 'display_contact', 'intern', 'th_payment')
        }),
        ('Timestamps', {
            'fields': ('date_created', 'date_updated'),
            'classes': ('collapse',)
        })
    )


@admin.register(ServiceTagRelation)
class ServiceTagRelationAdmin(admin.ModelAdmin):
    list_display = ['service', 'tag']
    list_filter = ['tag']
    search_fields = ['service__name', 'tag__name']