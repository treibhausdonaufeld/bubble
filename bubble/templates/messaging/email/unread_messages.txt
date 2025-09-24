{% load i18n %}{% trans "Hello" %} {{ user.username }},

{% blocktrans count counter=unread_count %}You have {{ counter }} unread message.{% plural %}You have {{ counter }} unread messages.{% endblocktrans %}

{% trans "Recent messages:" %}

{% for message in messages %}
- {% trans "From:" %} {{ message.sender.username }}{% if message.sender.name %} ({{ message.sender.name }}){% endif %}
  {% if message.item %}{% trans "About:" %} {{ message.item.name }}{% endif %}
  {{ message.message|truncatewords:20 }}
  ({{ message.date_created|timesince }} {% trans "ago" %})

{% endfor %}
{% if unread_count > 5 %}
{% trans "...and more messages waiting for you." %}
{% endif %}

{% trans "View all messages at:" %} {{ site_url }}{% url 'messaging:conversation_list' %}

---
{% trans "This is an automated message from bubble." %}
{% trans "To stop receiving these notifications, please update your email preferences in your profile settings." %}
