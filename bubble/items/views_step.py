import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from django.views.generic import UpdateView

from .forms_step import ItemDetailsForm
from .forms_step import ItemImageUploadForm
from .models import Image
from .models import Item
from .models import ProcessingStatus
from .tasks import process_item_images

logger = logging.getLogger(__name__)


class ItemCreateStepOneView(LoginRequiredMixin, TemplateView):
    """Step 1: Upload images and create temporary item."""

    template_name = "items/item_create_step1.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = ItemImageUploadForm()
        return context

    def post(self, request, *args, **kwargs):
        # Create temporary item
        item = Item.objects.create(
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

        if images:
            # Start background processing
            item.processing_status = ProcessingStatus.PROCESSING
            item.save(update_fields=["processing_status"])

            # Trigger async image processing
            process_item_images.delay(item.pk)

            messages.info(
                request,
                _(
                    "Images uploaded! We're analyzing them to suggest a title "
                    "and description. You can continue editing below.",
                ),
            )
        else:
            # No images, skip processing
            item.processing_status = ProcessingStatus.COMPLETED
            item.save(update_fields=["processing_status"])

        # Redirect to step 2
        return redirect("items:create_step2", pk=item.pk)


class ItemCreateStepTwoView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Step 2: Edit item details with AI suggestions."""

    model = Item
    form_class = ItemDetailsForm
    template_name = "items/item_create_step2.html"

    def test_func(self):
        obj = self.get_object()
        return obj.user == self.request.user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = self.get_object()

        context["item"] = item
        context["images"] = item.images.order_by("ordering")
        context["is_processing"] = item.processing_status == ProcessingStatus.PROCESSING
        context["processing_failed"] = item.processing_status == ProcessingStatus.FAILED

        return context

    def form_valid(self, form):
        item = form.save(commit=False)

        # Ensure the item has required fields
        if not item.name:
            form.add_error("name", _("Item name is required."))
            return self.form_invalid(form)

        # Check which button was pressed
        is_draft = "draft" in self.request.POST

        if is_draft:
            item.processing_status = ProcessingStatus.DRAFT
            success_message = _("Item saved as draft!")
            redirect_url = reverse("items:create_step2", kwargs={"pk": item.pk})
        else:
            # Default behavior if no specific button is detected
            item.active = True
            item.processing_status = ProcessingStatus.COMPLETED
            success_message = _("Item published successfully!")
            redirect_url = self.get_success_url()

        item.save()

        # Handle additional image uploads
        new_images = self.request.FILES.getlist("images")
        existing_image_count = item.images.count()

        for i, image in enumerate(new_images):
            Image.objects.create(
                item=item,
                original=image,
                ordering=existing_image_count + i,
            )

        messages.success(self.request, success_message)
        return HttpResponseRedirect(redirect_url)

    def get_success_url(self):
        return reverse("items:detail", kwargs={"pk": self.object.pk})


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
            },
        )

    except Item.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Item not found"},
            status=404,
        )


@login_required
@require_http_methods(["POST"])
def skip_image_upload(request):
    """Allow user to skip image upload and go directly to step 2."""
    item = Item.objects.create(
        user=request.user,
        processing_status=ProcessingStatus.COMPLETED,
        active=False,
    )

    return redirect("items:create_step2", pk=item.pk)


@login_required
@require_http_methods(["POST"])
def delete_draft_item(request, pk):
    """Delete a draft item if user wants to cancel creation."""
    try:
        item = get_object_or_404(Item, pk=pk, user=request.user)

        # Only allow deletion of draft/processing items
        if item.processing_status in [
            ProcessingStatus.DRAFT,
            ProcessingStatus.PROCESSING,
        ]:
            item.delete()
            messages.info(request, _("Draft item deleted."))
            return JsonResponse({"status": "success"})
        return JsonResponse(
            {"status": "error", "message": "Cannot delete completed items"},
            status=400,
        )

    except Item.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Item not found"},
            status=404,
        )


class DraftItemsView(LoginRequiredMixin, TemplateView):
    """View to show user's draft/processing items."""

    template_name = "items/draft_items.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["draft_items"] = (
            Item.objects.filter(
                user=self.request.user,
                processing_status__in=[
                    ProcessingStatus.DRAFT,
                    ProcessingStatus.PROCESSING,
                    ProcessingStatus.FAILED,
                ],
            )
            .prefetch_related("images")
            .order_by("-date_created")
        )

        return context
