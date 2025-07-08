import asyncio

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import models
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)
from rest_framework.authtoken.models import Token

from bubble.categories.models import ItemCategory
from bubble.items.temporal.temporal_activities import ItemProcessingRequest
from bubble.items.temporal.temporal_service import TemporalService
from bubble.messaging.models import Message

from .forms import ItemFilterForm, ItemForm, ItemImageUploadForm
from .models import Image, Item, ProcessingStatus


class ItemListView(ListView):
    model = Item
    template_name = "items/item_list.html"
    context_object_name = "items"
    paginate_by = 15

    def get_queryset(self):
        queryset = (
            Item.objects.filter(active=True)
            .select_related("user", "category")
            .prefetch_related(
                models.Prefetch("images", queryset=Image.objects.order_by("ordering")),
            )
        )

        # Apply GET parameter filters
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(description__icontains=search)
                | Q(category__name__icontains=search)
                | Q(category__parent_category__name__icontains=search)
                | Q(tags__tag__name__icontains=search)
                | Q(user__username__icontains=search)
                | Q(user__name__icontains=search),
            ).distinct()

        category = self.request.GET.get("category")
        if category:
            # Get selected category and all its descendants for hierarchical filtering
            try:
                selected_category = ItemCategory.objects.get(id=category)
                descendant_ids = self._get_all_descendant_category_ids(
                    selected_category,
                )
                queryset = queryset.filter(category_id__in=descendant_ids)
            except ItemCategory.DoesNotExist:
                # If category doesn't exist, use original filter to avoid errors
                queryset = queryset.filter(category_id=category)

        # GET parameter item_type filtering
        item_type = self.request.GET.get("item_type")
        if item_type:
            queryset = queryset.filter(item_type=item_type)

        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        tags = self.request.GET.getlist("tags")
        if tags:
            queryset = queryset.filter(tags__tag__in=tags).distinct()

        # Apply sorting
        sort = self.request.GET.get("sort", "newest")
        if sort == "oldest":
            queryset = queryset.order_by("date_created")
        elif sort == "price_low":
            queryset = queryset.order_by("price")
        elif sort == "price_high":
            queryset = queryset.order_by("-price")
        elif sort == "name":
            queryset = queryset.order_by("name")
        else:  # newest (default)
            queryset = queryset.order_by("-date_created")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Create filter form with GET parameters
        context["filter_form"] = ItemFilterForm(self.request.GET)

        # Get categories that have active items for current filter
        base_item_queryset = Item.objects.filter(active=True)

        # Apply item_type filter from GET params
        item_type = self.request.GET.get("item_type")
        if item_type:
            base_item_queryset = base_item_queryset.filter(item_type=item_type)

        # Get categories that have items in the filtered queryset
        categories_with_items = ItemCategory.objects.filter(
            items__in=base_item_queryset,
        ).distinct()

        # Get all parent categories needed to build the full tree
        all_needed_categories = set()
        for cat in categories_with_items:
            # Add this category and all its parents
            current = cat
            while current:
                all_needed_categories.add(current.id)
                current = current.parent_category

        # Get the full category objects needed for the tree
        tree_categories = (
            ItemCategory.objects.filter(id__in=all_needed_categories)
            .select_related("parent_category")
            .prefetch_related("subcategories")
        )

        # Build hierarchical structure
        def build_category_tree(categories, categories_with_direct_items):
            """Build a nested structure of categories with their subcategories"""
            category_dict = {}
            root_categories = []
            direct_item_ids = {cat.id for cat in categories_with_direct_items}

            # First pass: create dict of all categories
            for cat in categories:
                category_dict[cat.id] = {
                    "category": cat,
                    "subcategories": [],
                    "has_direct_items": cat.id in direct_item_ids,
                }

            # Second pass: organize into hierarchy
            for cat in categories:
                if cat.parent_category and cat.parent_category.id in category_dict:
                    category_dict[cat.parent_category.id]["subcategories"].append(
                        category_dict[cat.id],
                    )
                elif cat.parent_category is None:
                    root_categories.append(category_dict[cat.id])

            return root_categories

        context["category_tree"] = build_category_tree(
            tree_categories,
            categories_with_items,
        )
        context["all_categories"] = categories_with_items

        # Add sort options - these are already translated in forms
        sort_options = [
            ("newest", _("Newest first")),
            ("oldest", _("Oldest first")),
            ("price_low", _("Price: Low to High")),
            ("price_high", _("Price: High to Low")),
            ("name", _("Name A-Z")),
        ]
        context["sort_options"] = sort_options
        context["current_sort"] = self.request.GET.get("sort", "newest")

        # Add view mode
        context["view_mode"] = self.request.GET.get("view", "grid")

        # Add context for current filter type from GET params
        item_type_param = self.request.GET.get("item_type")
        if item_type_param:
            try:
                item_type_filter = int(item_type_param)
                item_type_names = {0: "sell", 1: "give_away", 2: "borrow", 3: "need"}
                context["current_filter"] = item_type_names.get(item_type_filter)
                context["current_filter_display"] = dict(Item.ITEM_TYPE_CHOICES).get(
                    item_type_filter,
                )
            except (ValueError, TypeError):
                pass

        # Add active filters for display
        active_filters = []
        if self.request.GET.get("search"):
            active_filters.append(
                ("search", f"Search: {self.request.GET.get('search')}"),
            )
        if self.request.GET.get("category"):
            try:
                cat = ItemCategory.objects.get(id=self.request.GET.get("category"))
                active_filters.append(("category", f"Category: {cat.get_hierarchy()}"))
            except ItemCategory.DoesNotExist:
                pass
        if self.request.GET.get("item_type"):
            type_dict = dict(Item.ITEM_TYPE_CHOICES)
            active_filters.append(
                (
                    "item_type",
                    f"Type: {type_dict.get(int(self.request.GET.get('item_type')))}",
                ),
            )
        if status := self.request.GET.get("status"):
            status_dict = dict(Item.STATUS_CHOICES)
            active_filters.append(
                (
                    "status",
                    f"Condition: {status_dict.get(int(status))}",
                ),
            )

        context["active_filters"] = active_filters

        # Extract content type dynamically from URL path
        # For URLs like /sachen/, /events/, /dienste/
        path_parts = self.request.path.strip("/").split("/")
        if path_parts and path_parts[0]:
            content_type_slug = path_parts[0]
            context["content_type_slug"] = content_type_slug

            # Try to get the corresponding root category
            try:
                context["root_category"] = ItemCategory.objects.get(
                    url_slug=content_type_slug,
                    parent_category__isnull=True,
                )
            except ItemCategory.DoesNotExist:
                # Fallback - create a mock object with capitalized name
                class MockCategory:
                    def __init__(self, slug):
                        self.name = slug.capitalize()

                context["root_category"] = MockCategory(content_type_slug)

        return context

    def _get_all_descendant_category_ids(self, category):
        """
        Recursively get all descendant category IDs including the parent category.
        This enables hierarchical filtering where selecting a parent category
        includes items from all its subcategories.
        """
        category_ids = [category.id]

        # Get all direct children
        children = ItemCategory.objects.filter(parent_category=category)

        # Recursively get descendants of each child
        for child in children:
            category_ids.extend(self._get_all_descendant_category_ids(child))

        return category_ids


class ItemDetailView(DetailView):
    model = Item
    template_name = "items/item_detail.html"
    context_object_name = "item"

    def get_queryset(self):
        return (
            Item.objects.filter(active=True)
            .select_related("user", "category")
            .prefetch_related("images")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["item_images"] = self.object.images.all().order_by("ordering")
        context["is_owner"] = (
            self.request.user == self.object.user
            if self.request.user.is_authenticated
            else False
        )

        # Check if there's an existing conversation for this item and user
        if self.request.user.is_authenticated:
            conversation_exists = Message.objects.filter(
                item=self.object,
                sender__in=[self.request.user, self.object.user],
                receiver__in=[self.request.user, self.object.user],
            ).exists()
            context["conversation_exists"] = conversation_exists

        return context


class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    form_class = ItemForm
    template_name = "items/item_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user

        # Try to determine root_category from URL or other context
        # This allows dynamic fields to work even in non-content-specific URLs
        root_category = getattr(self, "root_category", None)
        if root_category:
            kwargs["root_category"] = root_category

        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)

        # Handle multiple image uploads
        images = self.request.FILES.getlist("images")
        for image in images:
            Image.objects.create(item=self.object, original=image)

        messages.success(self.request, _("Item created successfully!"))
        return response

    def get_success_url(self):
        return reverse("items:detail", kwargs={"pk": self.object.pk})


class ItemUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Item
    form_class = ItemForm
    template_name = "items/item_form.html"

    def test_func(self):
        obj = self.get_object()
        return obj.user == self.request.user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user

        # Try to determine root_category from URL or other context
        # This allows dynamic fields to work even in non-content-specific URLs
        root_category = getattr(self, "root_category", None)
        if root_category:
            kwargs["root_category"] = root_category

        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)

        # Handle multiple image uploads
        images = self.request.FILES.getlist("images")
        for image in images:
            Image.objects.create(item=self.object, original=image)

        messages.success(self.request, _("Item updated successfully!"))
        return response

    def get_success_url(self):
        if "publish" in self.request.POST:
            # If publish button was clicked, set item as active
            self.object.active = True
            self.object.save()
            url = reverse("items:detail", kwargs={"pk": self.object.pk})
        else:
            url = reverse("items:edit", kwargs={"pk": self.object.pk})

        return url


class ItemDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Item
    template_name = "items/item_confirm_delete.html"
    success_url = reverse_lazy("items:my_items")

    def test_func(self):
        obj = self.get_object()
        return obj.user == self.request.user

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, _("Item deleted successfully!"))
        return super().delete(request, *args, **kwargs)


class MyItemsView(LoginRequiredMixin, ListView):
    model = Item
    template_name = "items/my_items.html"
    context_object_name = "items"
    paginate_by = 10

    def get_queryset(self):
        return (
            Item.objects.filter(user=self.request.user)
            .select_related("category")
            .order_by("-date_created")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        context["active_items"] = queryset.filter(active=True).count()
        context["inactive_items"] = queryset.filter(active=False).count()

        # Add processing status counts
        context["draft_items"] = queryset.filter(
            processing_status=ProcessingStatus.DRAFT,
        ).count()
        context["processing_items"] = queryset.filter(
            processing_status=ProcessingStatus.PROCESSING,
        ).count()
        context["failed_items"] = queryset.filter(
            processing_status=ProcessingStatus.FAILED,
        ).count()

        return context


@login_required
def toggle_item_status(request, pk):
    """Toggle item active status"""
    item = get_object_or_404(Item, pk=pk, user=request.user)
    item.active = not item.active
    item.save()

    if item.active:
        messages.success(
            request,
            _("Item '%(name)s' has been activated.") % {"name": item.name},
        )
    else:
        messages.success(
            request,
            _("Item '%(name)s' has been deactivated.") % {"name": item.name},
        )

    return redirect("items:my_items")


@login_required
def delete_image(request, image_id):
    """AJAX view to delete an image."""
    if request.method == "POST":
        image = get_object_or_404(Image, id=image_id)

        # Check if the user owns the item
        if image.item.user != request.user:
            return JsonResponse({"success": False, "error": "Permission denied"})

        # Delete the image file and database record
        image.original.delete(save=False)  # Delete the physical file
        image.delete()  # Delete the database record

        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "error": "Invalid request method"})


# Content-aware views for dynamic URLs (e.g., /sachen/, /events/)
class ContentMixin:
    """Mixin to handle content type specific functionality"""

    def dispatch(self, request, *args, **kwargs):
        # Get content type from URL
        self.content_type_slug = kwargs.get("content_type")

        # Find root category by slug
        try:
            self.root_category = ItemCategory.objects.get(
                url_slug=self.content_type_slug,
                parent_category__isnull=True,
            )
        except ItemCategory.DoesNotExist:
            # If not found, redirect to main items list
            return redirect("items:list")

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """Filter items by content type's category tree"""
        queryset = super().get_queryset()

        # Get all descendant categories of this content type
        category_ids = [self.root_category.id]
        category_ids.extend([cat.id for cat in self.root_category.get_descendants()])

        return queryset.filter(category_id__in=category_ids)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["content_type_slug"] = self.content_type_slug
        context["root_category"] = self.root_category
        return context


class ContentListView(ContentMixin, ItemListView):
    """List view for content type specific items"""

    def get_template_names(self):
        # Allow content-type specific templates
        return [
            f"items/{self.content_type_slug}_list.html",
            "items/content_list.html",
            "items/item_list.html",  # fallback
        ]


class ContentDetailView(ContentMixin, ItemDetailView):
    """Detail view for content type specific items"""

    def get_template_names(self):
        return [
            f"items/{self.content_type_slug}_detail.html",
            "items/content_detail.html",
            "items/item_detail.html",  # fallback
        ]


class ItemCreateImagesView(LoginRequiredMixin, TemplateView):
    """Upload images and create temporary item."""

    template_name = "items/item_create_images.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = ItemImageUploadForm()
        return context

    def post(self, request, *args, **kwargs):
        # Create temporary item
        item: Item = Item.objects.create(
            user=request.user,
            processing_status=ProcessingStatus.DRAFT,
            active=False,  # Not active until completed
        )

        # Handle image uploads
        images = request.FILES.getlist("images")
        image_objects = []

        for i, image in enumerate(images):
            image_obj = Image.objects.create(item=item, original=image, ordering=i)
            image_objects.append(image_obj)

        item.processing_status = ProcessingStatus.DRAFT
        if "skip_ai" in request.POST:
            item.save(update_fields=["processing_status"])

            messages.info(
                request,
                _(
                    "AI processing skipped. You can now edit the item details below.",
                ),
            )
        elif images:
            # Start background processing
            item.processing_status = ProcessingStatus.PROCESSING

            # Trigger async image processing
            token = Token.objects.get_or_create(user=request.user)[0]
            input_data = ItemProcessingRequest(
                item_id=item.pk,
                user_id=request.user.pk,
                token=str(token),
                base_url=request.build_absolute_uri("/")[:-1],  # Remove trailing slash
            )
            workflow_id = asyncio.run(TemporalService.start_item_processing(input_data))

            # Store the workflow ID for potential cancellation
            item.workflow_id = workflow_id
            item.save(update_fields=["processing_status", "workflow_id"])

            messages.info(
                request,
                _(
                    "Images uploaded! We're analyzing them to suggest a title "
                    "and description. You can continue editing below.",
                ),
            )

        item.save(update_fields=["processing_status"])

        # Redirect to step 2
        return redirect("items:edit", pk=item.pk)


@login_required
@require_http_methods(["GET"])
def check_processing_status(request, pk):
    """AJAX endpoint to check item processing status."""
    try:
        item = get_object_or_404(Item, pk=pk, user=request.user)

        return JsonResponse(
            {
                "status": "success",
                "processing_status": item.processing_status,
                "processing_status_display": dict(ProcessingStatus.choices).get(
                    item.processing_status,
                    "",
                ),
                "name": item.name,
                "description": item.description,
                "is_processing": item.processing_status == ProcessingStatus.PROCESSING,
                "is_completed": item.processing_status == ProcessingStatus.COMPLETED,
                "has_failed": item.processing_status == ProcessingStatus.FAILED,
                "workflow_id": item.workflow_id,
                "can_cancel": (item.processing_status == ProcessingStatus.PROCESSING),
            },
        )

    except Item.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Item not found"},
            status=404,
        )


@login_required
@require_http_methods(["POST"])
def cancel_processing(request, pk):
    """AJAX endpoint to cancel item processing."""
    try:
        item = get_object_or_404(Item, pk=pk, user=request.user)

        # Check if item is currently being processed
        if item.processing_status != ProcessingStatus.PROCESSING:
            return JsonResponse(
                {"status": "error", "message": "Item is not currently being processed"},
                status=400,
            )

        # If no workflow_id, just mark as completed (graceful fallback)
        if not item.workflow_id:
            item.processing_status = ProcessingStatus.COMPLETED
            item.save(update_fields=["processing_status"])

            return JsonResponse(
                {
                    "status": "success",
                    "message": "Processing marked as completed",
                    "processing_status": item.processing_status,
                }
            )

        success = asyncio.run(TemporalService.cancel_workflow(item.workflow_id))

        if success:
            # Update item status to completed and clear workflow_id
            item.processing_status = ProcessingStatus.COMPLETED
            item.workflow_id = None
            item.save(update_fields=["processing_status", "workflow_id"])

            return JsonResponse(
                {
                    "status": "success",
                    "message": "Processing cancelled successfully",
                    "processing_status": item.processing_status,
                }
            )
        return JsonResponse(
            {"status": "error", "message": "Failed to cancel workflow"},
            status=500,
        )

    except Item.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Item not found"},
            status=404,
        )


@login_required
@require_http_methods(["POST"])
def retrigger_processing(request, pk):
    """AJAX endpoint to retrigger AI processing for an existing item."""
    try:
        item = get_object_or_404(Item, pk=pk, user=request.user)

        # Check if item is in a state that allows retriggering
        if item.processing_status == ProcessingStatus.PROCESSING:
            return JsonResponse(
                {"status": "error", "message": "Item is already being processed"},
                status=400,
            )

        # Check if item has images to process
        if not item.images.exists():
            return JsonResponse(
                {"status": "error", "message": "No images found to process"},
                status=400,
            )

        # Start background processing
        item.processing_status = ProcessingStatus.PROCESSING

        # Trigger async image processing
        token = Token.objects.get_or_create(user=request.user)[0]
        input_data = ItemProcessingRequest(
            item_id=item.pk,
            user_id=request.user.pk,
            token=str(token),
            base_url=request.build_absolute_uri("/")[:-1],  # Remove trailing slash
        )
        workflow_id = asyncio.run(TemporalService.start_item_processing(input_data))

        # Store the workflow ID for potential cancellation
        item.workflow_id = workflow_id
        item.save(update_fields=["processing_status", "workflow_id"])

        return JsonResponse(
            {
                "status": "success",
                "message": "AI processing restarted successfully",
                "processing_status": item.processing_status,
                "workflow_id": workflow_id,
            }
        )

    except Item.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Item not found"},
            status=404,
        )
