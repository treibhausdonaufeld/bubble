from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView

from .forms import TagForm
from .models import ItemTag


class TagListView(ListView):
    model = ItemTag
    template_name = "tags/tag_list.html"
    context_object_name = "tags"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.annotate(
            item_count=Count("items__item", distinct=True),
        )


class TagDetailView(DetailView):
    model = ItemTag
    template_name = "tags/tag_detail.html"
    context_object_name = "tag"
    pk_url_kwarg = "pk"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tag = self.object
        context["items"] = tag.items.select_related("item").filter(item__active=True)[
            :10
        ]
        context["total_items"] = tag.items.filter(item__active=True).count()
        return context


class TagCreateView(LoginRequiredMixin, CreateView):
    model = ItemTag
    form_class = TagForm
    template_name = "tags/tag_form.html"
    success_url = reverse_lazy("tags:list")

    def form_valid(self, form):
        return super().form_valid(form)


class TagUpdateView(LoginRequiredMixin, UpdateView):
    model = ItemTag
    form_class = TagForm
    template_name = "tags/tag_form.html"
    pk_url_kwarg = "pk"

    def get_success_url(self):
        return reverse_lazy("tags:detail", kwargs={"pk": self.object.pk})


class TagDeleteView(LoginRequiredMixin, DeleteView):
    model = ItemTag
    template_name = "tags/tag_confirm_delete.html"
    success_url = reverse_lazy("tags:list")
    pk_url_kwarg = "pk"
