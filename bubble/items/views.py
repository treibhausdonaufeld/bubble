from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
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
            .prefetch_related("tags__tag")
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
        if self.request.GET.get("status"):
            status_dict = dict(Item.STATUS_CHOICES)
            active_filters.append(
                (
                    "status",
                    f"Condition: {status_dict.get(int(self.request.GET.get('status')))}",
                ),
            )

        context["active_filters"] = active_filters

        return context

    def _get_all_descendant_category_ids(self, category):
        """
        Recursively get all descendant category IDs including the parent category itself.
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
            .prefetch_related("tags__tag", "images")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["item_tags"] = self.object.tags.all()
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
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, _("Item created successfully!"))
        return super().form_valid(form)

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
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, _("Item updated successfully!"))
        return super().form_valid(form)

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
            .prefetch_related("tags__tag")
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
