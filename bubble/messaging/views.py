from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from bubble.items.models import Item

from .forms import MessageForm
from .models import Message

User = get_user_model()


@login_required
def send_message(request, item_id):
    """Send a message about an item"""
    item = get_object_or_404(Item, id=item_id)

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.item = item
            message.sender = request.user
            message.receiver = item.user
            message.save()
            messages.success(request, _("Your request has been sent!"))
            return redirect("items:detail", pk=item.id)
    else:
        form = MessageForm()

    return render(
        request,
        "messaging/send_message.html",
        {
            "form": form,
            "item": item,
        },
    )


@login_required
def get_conversation(request, item_id):
    """Get conversation messages for an item (AJAX)"""
    item = get_object_or_404(Item, id=item_id)

    # Get all messages between current user and item owner
    conversation = Message.get_conversation(request.user, item.user, item)

    # Mark messages as read if user is the receiver
    conversation.filter(receiver=request.user, is_read=False).update(is_read=True)

    html = render_to_string(
        "messaging/conversation_messages.html",
        {
            "messages": conversation,
            "current_user": request.user,
        },
    )

    return JsonResponse({"html": html})


@login_required
def send_message_ajax(request, item_id):
    """Send a message via AJAX"""
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid method"})

    item = get_object_or_404(Item, id=item_id)
    form = MessageForm(request.POST)

    if form.is_valid():
        message = form.save(commit=False)
        message.item = item
        message.sender = request.user
        message.receiver = item.user
        message.save()

        # Return the new message HTML
        html = render_to_string(
            "messaging/message_item.html",
            {
                "message": message,
                "current_user": request.user,
            },
        )

        return JsonResponse(
            {
                "success": True,
                "message_html": html,
            },
        )

    return JsonResponse(
        {
            "success": False,
            "errors": form.errors,
        },
    )


@login_required
def conversation_list(request):
    """Show all conversations for the current user"""
    conversations = Message.get_user_conversations(request.user)

    return render(
        request,
        "messaging/conversation_list.html",
        {
            "conversations": conversations,
        },
    )


@login_required
def conversation_detail(request, username, item_id=None):
    """Show conversation with a specific user, optionally filtered by item"""
    other_user = get_object_or_404(User, username=username)
    item = None

    if item_id:
        item = get_object_or_404(Item, id=item_id)

    # Get conversation messages
    messages_qs = Message.get_conversation(request.user, other_user, item)

    # Mark messages as read where current user is receiver
    unread_messages = messages_qs.filter(receiver=request.user, is_read=False)
    for msg in unread_messages:
        msg.mark_as_read()

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.receiver = other_user
            message.item = item
            message.save()

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                # Return JSON for AJAX requests
                html = render_to_string(
                    "messaging/message_item.html",
                    {
                        "message": message,
                        "current_user": request.user,
                    },
                )
                return JsonResponse(
                    {
                        "success": True,
                        "message_html": html,
                    }
                )
            # Redirect for regular form submissions
            if item:
                return redirect(
                    "messaging:conversation_detail_item",
                    username=username,
                    item_id=item.id,
                )
            return redirect("messaging:conversation_detail", username=username)
    else:
        form = MessageForm()

    return render(
        request,
        "messaging/conversation_detail.html",
        {
            "other_user": other_user,
            "item": item,
            "messages": messages_qs,
            "form": form,
        },
    )


@login_required
def send_private_message(request, username):
    """Send a private message to a user (no item)"""
    receiver = get_object_or_404(User, username=username)

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.receiver = receiver
            message.save()
            messages.success(request, _("Message sent successfully!"))
            return redirect("messaging:conversation_detail", username=username)
    else:
        form = MessageForm()

    return render(
        request,
        "messaging/send_private_message.html",
        {
            "receiver": receiver,
            "form": form,
        },
    )


@login_required
@require_POST
def mark_conversation_read(request, username, item_id=None):
    """Mark all messages in a conversation as read"""
    other_user = get_object_or_404(User, username=username)
    item = None

    if item_id:
        item = get_object_or_404(Item, id=item_id)

    # Get unread messages where current user is receiver
    messages_qs = Message.get_conversation(request.user, other_user, item)
    unread_messages = messages_qs.filter(receiver=request.user, is_read=False)

    for msg in unread_messages:
        msg.mark_as_read()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"success": True, "marked_count": unread_messages.count()})

    return redirect("messaging:conversation_list")
