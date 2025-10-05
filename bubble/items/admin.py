from datetime import timedelta

from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Image, Item, ItemCategory, SearchStatus, SimilaritySearch

# Constants for publishing status
PUBLISHING_STATUS_DRAFT = 0
PUBLISHING_STATUS_PROCESSING = 1
PUBLISHING_STATUS_COMPLETED = 2
PUBLISHING_STATUS_FAILED = 3

# Time constants
SECONDS_IN_HOUR = 3600
DAYS_IN_WEEK = 7


@admin.register(ItemCategory)
class ItemCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "emoji",
        "get_hierarchy_display",
        "parent_category",
        "ordering",
        "description",
    )
    list_filter = ("parent_category",)
    search_fields = (
        "name",
        "description",
    )
    ordering = ("ordering", "parent_category__name", "name")
    autocomplete_fields = ("parent_category",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "emoji",
                    "parent_category",
                    "description",
                    "ordering",
                ),
            },
        ),
    )

    @admin.display(
        description="Category Hierarchy",
        ordering="name",
    )
    def get_hierarchy_display(self, obj):
        hierarchy = obj.get_hierarchy()
        parts = hierarchy.split(" > ")
        if len(parts) > 1:
            parent_parts = " > ".join(parts[:-1])
            return format_html(
                '<span style="color: #888;">{}</span> > <strong>{}</strong>',
                parent_parts,
                parts[-1],
            )
        return format_html("<strong>{}</strong>", hierarchy)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("parent_category")


class ImageInline(admin.TabularInline):
    model = Image
    extra = 1
    fields = ("original", "ordering")


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "user",
        "category",
        "item_type",
        "price",
        "active",
        "date_created",
    )
    list_filter = ("active", "item_type", "category", "date_created")
    search_fields = ("name", "description", "user__username", "category__name")
    ordering = ("-date_created",)
    autocomplete_fields = ("user", "category")
    readonly_fields = (
        "date_created",
        "date_updated",
        "embedding_display",
        "processing_status",
        "workflow_id",
        "publishing_status",
        "publishing_workflow_id",
    )
    inlines = [ImageInline]

    def _get_publishing_status_text(self, status):
        """Get text representation of publishing status."""
        status_map = {
            PUBLISHING_STATUS_DRAFT: " - Draft",
            PUBLISHING_STATUS_PROCESSING: " - Processing...",
            PUBLISHING_STATUS_COMPLETED: " - Published",
            PUBLISHING_STATUS_FAILED: " - Failed",
        }
        return status_map.get(status, "")

    def _get_time_display(self, obj):
        """Get formatted time display for embedding update."""
        if not obj.date_updated:
            return ""

        # Format the date in a readable way
        if timezone.is_aware(obj.date_updated):
            local_time = timezone.localtime(obj.date_updated)
            time_diff = timezone.now() - obj.date_updated
        else:
            local_time = obj.date_updated
            time_diff = timezone.now().replace(tzinfo=None) - obj.date_updated

        # Calculate relative time display
        if time_diff.days == 0:
            if time_diff.seconds < SECONDS_IN_HOUR:  # Less than 1 hour
                minutes = time_diff.seconds // 60
                time_str = f"{minutes}m ago"
            else:  # Less than 1 day
                hours = time_diff.seconds // SECONDS_IN_HOUR
                time_str = f"{hours}h ago"
        elif time_diff.days == 1:
            time_str = "1 day ago"
        elif time_diff.days < DAYS_IN_WEEK:
            time_str = f"{time_diff.days} days ago"
        else:
            time_str = local_time.strftime("%Y-%m-%d %H:%M")

        return f" (updated: {time_str})"

    @admin.display(description=_("Embedding Status"))
    def embedding_display(self, obj):
        """Display embedding information in a readable format."""
        if obj.embedding is not None:
            try:
                embedding_length = len(obj.embedding)
                status_text = f"✓ Embedding present ({embedding_length} dimensions)"

                # Add publishing status context
                status_text += self._get_publishing_status_text(obj.publishing_status)

                # Add timestamp information
                status_text += self._get_time_display(obj)

            except (TypeError, AttributeError):
                return "⚠ Embedding format error"
            else:
                return status_text
        # Show publishing status even without embedding
        elif obj.publishing_status == PUBLISHING_STATUS_PROCESSING:
            return "⏳ Processing embedding..."
        elif obj.publishing_status == PUBLISHING_STATUS_FAILED:
            return "❌ Embedding generation failed"
        else:
            return "✗ No embedding"

    fieldsets = (
        (
            None,
            {
                "fields": ("name", "description", "user", "category", "active"),
            },
        ),
        (
            _("Item Details"),
            {
                "fields": ("item_type", "price", "display_contact"),
            },
        ),
        (
            _("Internal Options"),
            {
                "fields": ("internal", "payment_enabled"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("date_created", "date_updated"),
                "classes": ("collapse",),
            },
        ),
        (
            _("AI Processing"),
            {
                "fields": ("embedding_display", "processing_status", "workflow_id"),
                "classes": ("collapse",),
                "description": _("AI image processing workflow status"),
            },
        ),
        (
            _("Publishing"),
            {
                "fields": ("publishing_status", "publishing_workflow_id"),
                "classes": ("collapse",),
                "description": _("Item publishing and embedding generation status"),
            },
        ),
    )


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ("item", "filename", "ordering")
    list_filter = ("item__category",)
    search_fields = ("item__name",)
    ordering = ("item", "ordering")


@admin.register(SimilaritySearch)
class SimilaritySearchAdmin(admin.ModelAdmin):
    list_display = (
        "search_id",
        "query",
        "user",
        "status",
        "results_count",
        "date_created",
        "date_completed",
    )
    list_filter = ("status", "date_created", "date_completed")
    search_fields = ("search_id", "query", "user__username")
    ordering = ("-date_created",)
    readonly_fields = (
        "search_id",
        "date_created",
        "date_completed",
        "workflow_id",
        "results_display",
    )
    actions = ["cleanup_old_searches"]

    @admin.display(description=_("Search Results"))
    def results_display(self, obj):
        """Display search results in a readable format."""
        if obj.results:
            try:
                return f"✓ {len(obj.results)} items found"
            except (TypeError, AttributeError):
                return "⚠ Results format error"
        return "✗ No results"

    fieldsets = (
        (
            None,
            {
                "fields": ("search_id", "query", "user", "status"),
            },
        ),
        (
            _("Results"),
            {
                "fields": ("results_count", "results_display", "error_message"),
            },
        ),
        (
            _("Workflow"),
            {
                "fields": ("workflow_id",),
                "classes": ("collapse",),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("date_created", "date_completed"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.action(description=_("Clean up old searches"))
    def cleanup_old_searches(self, request, queryset):
        """Admin action to clean up old searches."""

        # Find old completed and failed searches (older than 7 days)
        cutoff_date = timezone.now() - timedelta(days=7)
        old_searches = SimilaritySearch.objects.filter(
            status__in=[SearchStatus.COMPLETED, SearchStatus.FAILED],
            date_completed__lt=cutoff_date,
        )

        # Find stuck searches (older than 1 day)
        stuck_cutoff = timezone.now() - timedelta(days=1)
        stuck_searches = SimilaritySearch.objects.filter(
            status__in=[SearchStatus.PENDING, SearchStatus.PROCESSING],
            date_created__lt=stuck_cutoff,
        )

        old_count = old_searches.count()
        stuck_count = stuck_searches.count()

        # Delete them
        old_searches.delete()
        stuck_searches.delete()

        total_deleted = old_count + stuck_count

        self.message_user(
            request,
            f"Successfully cleaned up {total_deleted} searches "
            f"({old_count} old, {stuck_count} stuck).",
        )
