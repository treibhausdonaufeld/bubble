from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string
from bubble.items.models import Item
from .models import Message
from .forms import MessageForm


@login_required
def send_message(request, item_id):
    """Send a message about an item"""
    item = get_object_or_404(Item, id=item_id)
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.item = item
            message.sender = request.user
            message.receiver = item.user
            message.save()
            messages.success(request, 'Ihre Anfrage wurde gesendet!')
            return redirect('items:detail', pk=item.id)
    else:
        form = MessageForm()
    
    return render(request, 'messaging/send_message.html', {
        'form': form,
        'item': item
    })


@login_required
def get_conversation(request, item_id):
    """Get conversation messages for an item (AJAX)"""
    item = get_object_or_404(Item, id=item_id)
    
    # Get all messages between current user and item owner
    conversation = Message.get_conversation(item, request.user, item.user)
    
    # Mark messages as read if user is the receiver
    conversation.filter(receiver=request.user, is_read=False).update(is_read=True)
    
    html = render_to_string('messaging/conversation_messages.html', {
        'messages': conversation,
        'current_user': request.user
    })
    
    return JsonResponse({'html': html})


@login_required
def send_message_ajax(request, item_id):
    """Send a message via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'})
    
    item = get_object_or_404(Item, id=item_id)
    form = MessageForm(request.POST)
    
    if form.is_valid():
        message = form.save(commit=False)
        message.item = item
        message.sender = request.user
        message.receiver = item.user
        message.save()
        
        # Return the new message HTML
        html = render_to_string('messaging/message_item.html', {
            'message': message,
            'current_user': request.user
        })
        
        return JsonResponse({
            'success': True,
            'message_html': html
        })
    
    return JsonResponse({
        'success': False,
        'errors': form.errors
    })
