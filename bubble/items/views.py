from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db import models
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView

from bubble.categories.models import ItemCategory

from .forms import ItemFilterForm
from .forms import ItemForm
from .models import Image
from .models import Item


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

        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        tags = self.request.GET.getlist("tags")
        if tags:
            queryset = queryset.filter(tags__tag__in=tags).distinct()

        # Apply dynamic filters
        content_type_slug = self.kwargs.get("content_type", "")
        if content_type_slug:
            try:
                root_category = ItemCategory.objects.get(
                    url_slug=content_type_slug,
                    parent_category__isnull=True,
                )
                # Process dynamic filters
                for filter_name in root_category.filters:
                    filter_value = self.request.GET.get(f"filter_{filter_name}")
                    if filter_value and filter_name in root_category.custom_fields:
                        # Filter by custom field value
                        queryset = queryset.filter(
                            custom_fields__contains={
                                filter_name: {"value": filter_value},
                            },
                        )
            except ItemCategory.DoesNotExist:
                pass

        # Apply sorting
        sort = self.request.GET.get("sort", "newest")

        # Get root category for dynamic sorting
        content_type_slug = self.kwargs.get("content_type", "")
        try:
            root_category = ItemCategory.objects.get(
                url_slug=content_type_slug,
                parent_category__isnull=True,
            )
            # Check if this is a custom field sort
            if sort.startswith("custom_"):
                field_name = (
                    sort.replace("custom_", "").replace("_asc", "").replace("_desc", "")
                )
                if field_name in root_category.sort_by:
                    if sort.endswith("_desc"):
                        queryset = queryset.order_by(
                            f"-custom_fields__{field_name}__value",
                        )
                    else:
                        queryset = queryset.order_by(
                            f"custom_fields__{field_name}__value",
                        )
                else:
                    # Fallback to newest
                    queryset = queryset.order_by("-date_created")
            elif sort == "oldest":
                queryset = queryset.order_by("date_created")
            elif sort == "name":
                queryset = queryset.order_by("name")
            elif sort == "name_desc":
                queryset = queryset.order_by("-name")
            else:  # newest (default)
                queryset = queryset.order_by("-date_created")
        except ItemCategory.DoesNotExist:
            # Fallback sorting without category
            if sort == "oldest":
                queryset = queryset.order_by("date_created")
            elif sort == "name":
                queryset = queryset.order_by("name")
            elif sort == "name_desc":
                queryset = queryset.order_by("-name")
            else:  # newest (default)
                queryset = queryset.order_by("-date_created")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get root category first if available
        content_type_slug = self.kwargs.get("content_type", "")
        root_category = None
        if content_type_slug:
            try:
                root_category = ItemCategory.objects.get(
                    url_slug=content_type_slug,
                    parent_category__isnull=True,
                )
            except ItemCategory.DoesNotExist:
                pass

        # Create filter form with GET parameters and root category
        if root_category:
            context["filter_form"] = ItemFilterForm(
                self.request.GET,
                root_category=root_category,
            )
        else:
            context["filter_form"] = ItemFilterForm(self.request.GET)

        # Get categories that have active items for current filter
        base_item_queryset = Item.objects.filter(active=True)

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

        # Build dynamic sort options based on category
        sort_options = [
            ("newest", _("Newest first")),
            ("oldest", _("Oldest first")),
            ("name", _("Name A-Z")),
            ("name_desc", _("Name Z-A")),
        ]

        # Add custom field sorting if root_category exists and has sort_by fields
        if "root_category" in context and hasattr(context["root_category"], "sort_by"):
            root_cat = context["root_category"]
            if root_cat.sort_by:
                # Get custom field definitions
                for field_name in root_cat.sort_by:
                    if field_name in root_cat.custom_fields:
                        field_config = root_cat.custom_fields[field_name]
                        field_label = field_config.get("label", field_name.title())
                        sort_options.append(
                            (f"custom_{field_name}_asc", f"{field_label} ↑"),
                        )
                        sort_options.append(
                            (f"custom_{field_name}_desc", f"{field_label} ↓"),
                        )

        context["sort_options"] = sort_options
        context["current_sort"] = self.request.GET.get("sort", "newest")

        # Add view mode
        context["view_mode"] = self.request.GET.get("view", "grid")

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

        # Add dynamic filter active filters
        if root_category and root_category.filters:
            for filter_name in root_category.filters:
                filter_value = self.request.GET.get(f"filter_{filter_name}")
                if filter_value and filter_name in root_category.custom_fields:
                    field_config = root_category.custom_fields[filter_name]
                    label = field_config.get("label", filter_name.title())

                    # For choice fields, get the display value
                    display_value = filter_value
                    if field_config.get("type") == "choice":
                        choices = field_config.get("choices", [])
                        for choice in choices:
                            if isinstance(choice, dict):
                                if choice.get("key") == filter_value:
                                    display_value = choice.get("value", filter_value)
                                    break
                            elif choice == filter_value:
                                display_value = choice
                                break

                    active_filters.append(
                        (f"filter_{filter_name}", f"{label}: {display_value}"),
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
                root_category = ItemCategory.objects.get(
                    url_slug=content_type_slug,
                    parent_category__isnull=True,
                )
                context["root_category"] = root_category
                # Check if root category has subcategories
                context["has_subcategories"] = root_category.subcategories.exists()

                # Pass filter configuration to template
                if root_category.filters:
                    filter_configs = []
                    for filter_name in root_category.filters:
                        if filter_name in root_category.custom_fields:
                            field_config = root_category.custom_fields[filter_name]
                            filter_configs.append(
                                {
                                    "name": filter_name,
                                    "config": field_config,
                                },
                            )
                    context["dynamic_filters"] = filter_configs

            except ItemCategory.DoesNotExist:
                # Fallback - create a mock object with capitalized name
                class MockCategory:
                    def __init__(self, slug):
                        self.name = slug.capitalize()
                        self.filters = []
                        self.sort_by = []

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
            from bubble.messaging.models import Message

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
        return reverse("items:detail", kwargs={"pk": self.object.pk})


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
        context["active_items"] = self.get_queryset().filter(active=True).count()
        context["inactive_items"] = self.get_queryset().filter(active=False).count()
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


def get_subcategories(request):
    """AJAX view to get subcategories for a parent category"""
    parent_id = request.GET.get("parent_id")
    if parent_id:
        subcategories = ItemCategory.objects.filter(parent_category_id=parent_id)
        data = [{"id": cat.id, "name": cat.name} for cat in subcategories]
    else:
        # Return root categories
        root_categories = ItemCategory.objects.filter(parent_category=None)
        data = [{"id": cat.id, "name": cat.name} for cat in root_categories]

    return JsonResponse({"subcategories": data})


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


class ContentCreateView(ContentMixin, ItemCreateView):
    """Create view for content type specific items"""

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["root_category"] = self.root_category
        return kwargs

    def get_template_names(self):
        return [
            f"items/{self.content_type_slug}_form.html",
            "items/content_form.html",
            "items/item_form.html",  # fallback
        ]

    def get_success_url(self):
        return reverse(
            "items:detail",
            kwargs={
                "content_type": self.content_type_slug,
                "pk": self.object.pk,
            },
        )


class ContentUpdateView(ContentMixin, ItemUpdateView):
    """Update view for content type specific items"""

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["root_category"] = self.root_category
        return kwargs

    def get_template_names(self):
        return [
            f"items/{self.content_type_slug}_form.html",
            "items/content_form.html",
            "items/item_form.html",  # fallback
        ]

    def get_success_url(self):
        return reverse(
            "items:detail",
            kwargs={
                "content_type": self.content_type_slug,
                "pk": self.object.pk,
            },
        )


class ContentDeleteView(ContentMixin, ItemDeleteView):
    """Delete view for content type specific items"""

    def get_success_url(self):
        return reverse(
            "items:my_items",
            kwargs={
                "content_type": self.content_type_slug,
            },
        )


class MyContentView(ContentMixin, MyItemsView):
    """User's content management view for specific content type"""

    def get_template_names(self):
        return [
            f"items/my_{self.content_type_slug}.html",
            "items/my_content.html",
            "items/my_items.html",  # fallback
        ]


@login_required
def toggle_content_status(request, pk, content_type):
    """Toggle active status for content type specific items"""
    item = get_object_or_404(Item, pk=pk, user=request.user)

    # Verify item belongs to this content type
    root_category = item.category.get_root_category()
    if root_category.url_slug != content_type:
        messages.error(request, _("Invalid content type"))
        return redirect("items:my_items")

    item.active = not item.active
    item.save()

    status = _("activated") if item.active else _("deactivated")
    messages.success(request, _("Item {} successfully.").format(status))

    return redirect(reverse("my_content", kwargs={"content_type": content_type}))
