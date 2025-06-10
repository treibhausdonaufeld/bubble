from django.contrib import admin
from .models import Project, ProjectTagRelation


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'creator', 'status', 'participant_count', 'start_date', 'active', 'date_created']
    list_filter = ['status', 'active', 'intern', 'start_date', 'date_created']
    search_fields = ['name', 'description', 'creator__username']
    readonly_fields = ['date_created', 'date_updated', 'participant_count']
    filter_horizontal = ['participants']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'creator')
        }),
        ('Project Details', {
            'fields': ('goals', 'requirements', 'status', 'start_date', 'end_date')
        }),
        ('Participation', {
            'fields': ('participants', 'max_participants', 'location')
        }),
        ('Settings', {
            'fields': ('active', 'intern', 'contact_info')
        }),
        ('Statistics', {
            'fields': ('participant_count',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('date_created', 'date_updated'),
            'classes': ('collapse',)
        })
    )


@admin.register(ProjectTagRelation)
class ProjectTagRelationAdmin(admin.ModelAdmin):
    list_display = ['project', 'tag']
    list_filter = ['tag']
    search_fields = ['project__name', 'tag__name']