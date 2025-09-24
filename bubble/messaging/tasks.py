from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext as _

from .models import Message

User = get_user_model()


@shared_task
def send_unread_message_notifications():
    """Send email notifications to users with unread messages"""
    users_with_unread = User.objects.filter(
        received_messages__is_read=False
    ).distinct()
    
    notifications_sent = 0
    
    for user in users_with_unread:
        # Skip if user has opted out of email reminders
        if not user.profile.email_reminder:
            continue
            
        # Get unread messages
        unread_messages = Message.objects.filter(
            receiver=user,
            is_read=False
        ).select_related('sender', 'item').order_by('-date_created')
        
        if unread_messages.exists():
            # Prepare email context
            from django.contrib.sites.models import Site
            current_site = Site.objects.get_current()
            
            context = {
                'user': user,
                'unread_count': unread_messages.count(),
                'messages': unread_messages[:5],  # Show first 5 messages
                'site_url': f'https://{current_site.domain}',
            }
            
            # Render email content
            subject = _('You have %(count)d unread messages') % {'count': unread_messages.count()}
            html_message = render_to_string(
                'messaging/email/unread_messages.html',
                context
            )
            text_message = render_to_string(
                'messaging/email/unread_messages.txt',
                context
            )
            
            # Send email
            try:
                send_mail(
                    subject=subject,
                    message=text_message,
                    from_email=None,  # Use default from settings
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                notifications_sent += 1
            except Exception as e:
                # Log error but continue with other users
                print(f"Failed to send email to {user.email}: {str(e)}")
    
    return f"Sent {notifications_sent} unread message notifications"


@shared_task
def cleanup_old_read_messages():
    """Clean up old read messages after 90 days"""
    cutoff_date = timezone.now() - timezone.timedelta(days=90)
    
    deleted_count = Message.objects.filter(
        is_read=True,
        read_at__lt=cutoff_date
    ).delete()[0]
    
    return f"Deleted {deleted_count} old read messages"