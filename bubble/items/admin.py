from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Image, Item, SimilaritySearch


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

    @admin.display(description=_("Embedding Status"))
    def embedding_display(self, obj):
        """Display embedding information in a readable format."""
        if obj.embedding is not None:
            try:
                from django.utils import timezone

                embedding_length = len(obj.embedding)
                status_text = f"✓ Embedding present ({embedding_length} dimensions)"

                # Add publishing status context
                if obj.publishing_status == 0:  # DRAFT
                    status_text += " - Draft"
                elif obj.publishing_status == 1:  # PROCESSING
                    status_text += " - Processing..."
                elif obj.publishing_status == 2:  # COMPLETED
                    status_text += " - Published"
                elif obj.publishing_status == 3:  # FAILED
                    status_text += " - Failed"

                # Add timestamp information
                # Use date_updated as a proxy for when embedding was last generated
                if obj.date_updated:
                    # Format the date in a readable way
                    if timezone.is_aware(obj.date_updated):
                        local_time = timezone.localtime(obj.date_updated)
                    else:
                        local_time = obj.date_updated

                    # Show relative time if recent, otherwise show full date
                    now = timezone.now()
                    if timezone.is_aware(obj.date_updated):
                        time_diff = now - obj.date_updated
                    else:
                        time_diff = (
                            timezone.now().replace(tzinfo=None) - obj.date_updated
                        )

                    if time_diff.days == 0:
                        if time_diff.seconds < 3600:  # Less than 1 hour
                            minutes = time_diff.seconds // 60
                            time_str = f"{minutes}m ago"
                        else:  # Less than 1 day
                            hours = time_diff.seconds // 3600
                            time_str = f"{hours}h ago"
                    elif time_diff.days == 1:
                        time_str = "1 day ago"
                    elif time_diff.days < 7:
                        time_str = f"{time_diff.days} days ago"
                    else:
                        time_str = local_time.strftime("%Y-%m-%d %H:%M")

                    status_text += f" (updated: {time_str})"

                return status_text
            except (TypeError, AttributeError):
                return "⚠ Embedding format error"
        else:
            # Show publishing status even without embedding
            if obj.publishing_status == 1:  # PROCESSING
                return "⏳ Processing embedding..."
            if obj.publishing_status == 3:  # FAILED
                return "❌ Embedding generation failed"
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
            _("Media"),
            {
                "fields": ("profile_img_frame", "profile_img_frame_alt"),
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
        from datetime import timedelta

        from django.utils import timezone

        from .models import SearchStatus

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
