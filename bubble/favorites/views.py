import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from bubble.users.models import User

from .forms import FavoriteListForm, ManageFavoriteForm, ManualFavoriteForm
from .models import Favorite, FavoriteList


class CheckFavoriteStatusView(LoginRequiredMixin, View):
    """AJAX view to check if current page is favorited"""

    def get(self, request):
        url = request.GET.get("url")
        if not url:
            return JsonResponse({"error": _("URL is required")}, status=400)

        existing_favorites = Favorite.objects.filter(user=request.user, url=url)
        is_favorited = existing_favorites.exists()

        # Return additional info about which lists it's in
        current_lists = []
        title = ""
        if is_favorited:
            current_lists = [
                {"id": fav.favorite_list.id, "name": fav.favorite_list.name}
                for fav in existing_favorites
            ]
            title = (
                existing_favorites.first().title if existing_favorites.exists() else ""
            )

        return JsonResponse(
            {
                "is_favorited": is_favorited,
                "current_lists": current_lists,
                "title": title,
            }
        )


class ToggleFavoriteView(LoginRequiredMixin, View):
    """AJAX view to toggle favorite status"""

    def _create_response(self, status, message, *, is_favorited):
        """Helper to create JSON response."""
        return JsonResponse(
            {
                "status": status,
                "message": message,
                "is_favorited": is_favorited,
            }
        )

    def post(self, request):
        data = json.loads(request.body)
        url = data.get("url")
        title = data.get("title", "")
        update_title = data.get("update_title", False)
        favorite_list_id = data.get("favorite_list_id")

        if not url:
            return JsonResponse({"error": _("URL is required")}, status=400)

        # Get or create default favorite list if no list specified
        favorite_list = None
        error_response = None

        if favorite_list_id:
            try:
                # Get the favorite list - check if user can edit it
                favorite_list = FavoriteList.objects.get(id=favorite_list_id)

                # Check if user has permission to add to this list
                if not favorite_list.can_edit(request.user):
                    error_response = JsonResponse(
                        {"error": _("You don't have permission to add to this list")},
                        status=403,
                    )
            except FavoriteList.DoesNotExist:
                error_response = JsonResponse(
                    {"error": _("Favorite list not found")}, status=404
                )
        else:
            favorite_list = FavoriteList.get_or_create_default_list(request.user)

        if error_response:
            return error_response

        # If this is a title update request
        if update_title:
            try:
                favorite = Favorite.objects.get(
                    user=request.user, url=url, favorite_list=favorite_list
                )
                favorite.title = title
                favorite.save()
                return self._create_response(
                    "updated", _("Favorite updated"), is_favorited=True
                )
            except Favorite.DoesNotExist:
                # Create new if doesn't exist
                Favorite.objects.create(
                    user=request.user, url=url, title=title, favorite_list=favorite_list
                )
                return self._create_response(
                    "added", _("Added to favorites"), is_favorited=True
                )

        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            url=url,
            favorite_list=favorite_list,
            defaults={"title": title},
        )

        if not created:
            # If it already exists, remove it
            favorite.delete()
            return self._create_response(
                "removed", _("Remove from favorites"), is_favorited=False
            )

        return self._create_response(
            "added", _("Added to favorites"), is_favorited=True
        )


class UserFavoritesView(LoginRequiredMixin, ListView):
    """Display user's favorites with pagination"""

    model = Favorite
    template_name = "favorites/user_favorites.html"
    context_object_name = "favorites"
    paginate_by = 10

    def get_queryset(self):
        username = self.kwargs.get("username")
        user = get_object_or_404(User, username=username)
        # Only show own favorites or if user is staff
        if self.request.user == user or self.request.user.is_staff:
            return Favorite.objects.filter(user=user)
        return Favorite.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        username = self.kwargs.get("username")
        context["profile_user"] = get_object_or_404(User, username=username)
        return context


class DeleteFavoriteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    """Delete a favorite"""

    model = Favorite
    success_message = _("Favorite deleted successfully")

    def get_queryset(self):
        # Users can only delete their own favorites
        return super().get_queryset().filter(user=self.request.user)

    def get_success_url(self):
        return reverse_lazy(
            "favorites:user_list",
            kwargs={"username": self.request.user.username},
        )

    def delete(self, request, *args, **kwargs):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            self.object = self.get_object()
            self.object.delete()
            return JsonResponse(
                {"status": "success", "message": str(self.success_message)},
            )
        return super().delete(request, *args, **kwargs)


# FavoriteList Views


class FavoriteListListView(LoginRequiredMixin, ListView):
    """Display user's favorite lists"""

    model = FavoriteList
    template_name = "favorites/favorite_list_list.html"
    context_object_name = "favorite_lists"
    paginate_by = 10

    def get_queryset(self):
        return FavoriteList.get_user_accessible_lists(self.request.user)


class FavoriteListDetailView(LoginRequiredMixin, DetailView):
    """Display favorite list details with favorites"""

    model = FavoriteList
    template_name = "favorites/favorite_list_detail.html"
    context_object_name = "favorite_list"

    def get_queryset(self):
        return FavoriteList.get_user_accessible_lists(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["favorites"] = self.object.favorites.all()
        context["can_edit"] = self.object.can_edit(self.request.user)
        return context


class FavoriteListCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Create a new favorite list"""

    model = FavoriteList
    form_class = FavoriteListForm
    template_name = "favorites/favorite_list_form.html"
    success_message = _("Favorite list created successfully")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("favorites:list_detail", kwargs={"pk": self.object.pk})


class FavoriteListUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Update a favorite list"""

    model = FavoriteList
    form_class = FavoriteListForm
    template_name = "favorites/favorite_list_form.html"
    success_message = _("Favorite list updated successfully")

    def get_queryset(self):
        # Only allow editing own lists
        return super().get_queryset().filter(user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse_lazy("favorites:list_detail", kwargs={"pk": self.object.pk})


class FavoriteListDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    """Delete a favorite list"""

    model = FavoriteList
    template_name = "favorites/favorite_list_confirm_delete.html"
    success_message = _("Favorite list deleted successfully")
    success_url = reverse_lazy("favorites:list_list")

    def get_queryset(self):
        # Only allow deleting own lists and not default lists
        return super().get_queryset().filter(user=self.request.user, is_default=False)

    def delete(self, request, *args, **kwargs):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            self.object = self.get_object()
            self.object.delete()
            return JsonResponse(
                {"status": "success", "message": str(self.success_message)},
            )
        return super().delete(request, *args, **kwargs)


class GetUserFavoriteListsView(LoginRequiredMixin, View):
    """AJAX view to get user's favorite lists for selection"""

    def get(self, request):
        # Get all lists the user can access
        all_lists = FavoriteList.get_user_accessible_lists(request.user)

        # Filter to only include lists the user can edit (can add favorites to)
        editable_lists = [fl for fl in all_lists if fl.can_edit(request.user)]

        data = [
            {
                "id": fl.id,
                "name": fl.name,
                "is_default": fl.is_default,
                "can_edit": True,  # All lists in this response are editable
            }
            for fl in editable_lists
        ]
        return JsonResponse({"favorite_lists": data})


class ManualFavoriteCreateView(LoginRequiredMixin, SuccessMessageMixin, View):
    """View for manually creating favorites with multiple list selection"""

    template_name = "favorites/manual_favorite_form.html"
    form_class = ManualFavoriteForm
    success_message = _("Favorite added successfully to selected lists!")

    def get(self, request):
        form = self.form_class(user=request.user)

        # If coming from a specific list, prefill it
        list_id = request.GET.get("list")
        if list_id:
            try:
                favorite_list = FavoriteList.objects.get(pk=list_id)
                # Check if user can edit this list
                if favorite_list.can_edit(request.user):
                    form.fields["favorite_lists"].initial = [favorite_list]
            except FavoriteList.DoesNotExist:
                pass

        return self.render_to_response({"form": form})

    def post(self, request):
        form = self.form_class(request.POST, user=request.user)
        if form.is_valid():
            title = form.cleaned_data["title"]
            url = form.cleaned_data["url"]
            favorite_lists = form.cleaned_data["favorite_lists"]

            # Create favorites in each selected list
            created_count = 0
            for favorite_list in favorite_lists:
                # Check if favorite already exists in this list
                if not Favorite.objects.filter(
                    user=request.user, url=url, favorite_list=favorite_list
                ).exists():
                    Favorite.objects.create(
                        user=request.user,
                        title=title,
                        url=url,
                        favorite_list=favorite_list,
                    )
                    created_count += 1

            if created_count > 0:
                success_message = _("Favorite added to %(count)d list(s)!") % {
                    "count": created_count
                }
            else:
                success_message = _("Favorite already exists in selected lists.")

            # Redirect back to the specific list if user came from one
            list_id = request.GET.get("list")
            if (
                list_id
                and len(favorite_lists) == 1
                and str(favorite_lists[0].pk) == list_id
            ):
                redirect_url = reverse_lazy(
                    "favorites:list_detail", kwargs={"pk": list_id}
                )
            else:
                redirect_url = reverse_lazy("favorites:list_list")

            return JsonResponse(
                {
                    "status": "success",
                    "message": success_message,
                    "redirect": redirect_url,
                }
            )
        return self.render_to_response({"form": form})

    def render_to_response(self, context):
        from django.shortcuts import render

        return render(self.request, self.template_name, context)


class ManageFavoriteView(LoginRequiredMixin, View):
    """View for managing existing favorites (add/remove from lists)"""

    template_name = "favorites/manage_favorite_form.html"
    form_class = ManageFavoriteForm

    def get(self, request):
        url = request.GET.get("url")
        if not url:
            return JsonResponse({"error": _("URL is required")}, status=400)

        form = self.form_class(user=request.user, url=url)
        return self.render_to_response({"form": form, "url": url})

    def post(self, request):
        url = request.POST.get("url") or request.GET.get("url")
        if not url:
            return JsonResponse({"error": _("URL is required")}, status=400)

        form = self.form_class(request.POST, user=request.user, url=url)
        if form.is_valid():
            title = form.cleaned_data["title"]
            new_lists = set(form.cleaned_data["favorite_lists"])

            # Get current favorites for this URL
            current_favorites = Favorite.objects.filter(user=request.user, url=url)
            current_lists = {fav.favorite_list for fav in current_favorites}

            # Calculate changes
            lists_to_add = new_lists - current_lists
            lists_to_remove = current_lists - new_lists

            # Remove from lists that are no longer selected
            for favorite_list in lists_to_remove:
                Favorite.objects.filter(
                    user=request.user, url=url, favorite_list=favorite_list
                ).delete()

            # Add to new lists
            for favorite_list in lists_to_add:
                Favorite.objects.create(
                    user=request.user,
                    title=title,
                    url=url,
                    favorite_list=favorite_list,
                )

            # Update title for existing favorites
            Favorite.objects.filter(user=request.user, url=url).update(title=title)

            # Prepare success message
            total_lists = len(new_lists)
            if total_lists > 0:
                success_message = _("Favorite saved to %(count)d list(s)!") % {
                    "count": total_lists
                }
            else:
                success_message = _("Favorite removed from all lists.")

            return JsonResponse(
                {
                    "status": "success",
                    "message": success_message,
                    "is_favorited": total_lists > 0,
                }
            )
        return self.render_to_response({"form": form, "url": url})

    def render_to_response(self, context):
        from django.shortcuts import render

        return render(self.request, self.template_name, context)
