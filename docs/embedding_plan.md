# Item Embedding Implementation Plan

## Overview

This document outlines the implementation plan for generating vector embeddings for items in the bubble platform. Embeddings will be generated automatically whenever an item is saved (created or updated), enabling future similarity search and recommendation features.

## Architecture

### Components

1. **Embedding Service** (`bubble/items/services/embeddings.py`)
   - Handles embedding generation using OpenAI's API
   - Prepares text from item fields (name, description, category)
   - Returns 1536-dimensional vectors

2. **Signal Handler** (`bubble/items/signals.py`)
   - Listens to Item model's post_save signal
   - Triggers embedding generation asynchronously
   - Handles both create and update events

3. **Celery Task** (`bubble/items/tasks.py`)
   - Asynchronous task for embedding generation
   - Prevents blocking the save operation
   - Includes retry logic and error handling

4. **Admin Interface** (`bubble/items/admin.py`)
   - Display embedding status in item list/detail views
   - Show when embedding was last generated
   - Action to manually regenerate embeddings

## Implementation Steps

### Step 1: Create Embedding Service

**File**: `bubble/items/services/embeddings.py`

```python
import logging
from typing import Optional
import openai
from django.conf import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_EMBEDDING_MODEL
    
    def generate_embedding(self, text: str) -> Optional[list[float]]:
        """Generate embedding for given text using OpenAI API."""
        try:
            response = openai.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
    def prepare_item_text(self, item) -> str:
        """Prepare text from item fields for embedding."""
        parts = []
        
        if item.name:
            parts.append(f"Name: {item.name}")
        
        if item.description:
            parts.append(f"Description: {item.description}")
        
        if item.category:
            parts.append(f"Category: {item.category.get_hierarchy()}")
        
        # Add item type and status for better context
        parts.append(f"Type: {item.get_item_type_display()}")
        parts.append(f"Condition: {item.get_status_display()}")
        
        return " | ".join(parts)
```

### Step 2: Create Celery Task

**File**: `bubble/items/tasks.py`

```python
import logging
from celery import shared_task
from bubble.items.models import Item
from bubble.items.services.embeddings import EmbeddingService

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def generate_item_embedding(self, item_id: int):
    """Generate embedding for an item asynchronously."""
    try:
        item = Item.objects.get(pk=item_id)
        
        # Skip if item doesn't have minimum required fields
        if not item.name:
            logger.info(f"Skipping embedding for item {item_id}: no name")
            return
        
        service = EmbeddingService()
        text = service.prepare_item_text(item)
        embedding = service.generate_embedding(text)
        
        if embedding:
            item.embedding = embedding
            item.save(update_fields=['embedding'])
            logger.info(f"Generated embedding for item {item_id}")
        else:
            logger.warning(f"Failed to generate embedding for item {item_id}")
            
    except Item.DoesNotExist:
        logger.error(f"Item {item_id} not found")
    except Exception as e:
        logger.error(f"Error generating embedding for item {item_id}: {e}")
        raise self.retry(exc=e, countdown=60)
```

### Step 3: Create Signal Handler

**File**: `bubble/items/signals.py`

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from bubble.items.models import Item
from bubble.items.tasks import generate_item_embedding

@receiver(post_save, sender=Item)
def trigger_embedding_generation(sender, instance, created, **kwargs):
    """Trigger embedding generation when item is saved."""
    # Only generate embeddings for active items with names
    if instance.active and instance.name:
        # Queue the task asynchronously
        generate_item_embedding.delay(instance.pk)
```

### Step 4: Update App Configuration

**File**: `bubble/items/apps.py`

```python
from django.apps import AppConfig

class ItemsConfig(AppConfig):
    name = "bubble.items"
    verbose_name = "Items"

    def ready(self):
        import bubble.items.signals  # noqa
```

### Step 5: Update Settings

**File**: `config/settings/base.py` (add to environment variables section)

```python
# OpenAI Configuration
OPENAI_API_KEY = env("OPENAI_API_KEY", default="")
OPENAI_EMBEDDING_MODEL = env("OPENAI_EMBEDDING_MODEL", default="text-embedding-3-small")
```

### Step 6: Update Admin Interface

**File**: `bubble/items/admin.py` (modifications)

```python
from django.contrib import admin
from django.utils.html import format_html
from bubble.items.models import Item
from bubble.items.tasks import generate_item_embedding

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = [...existing..., 'has_embedding', 'embedding_status']
    readonly_fields = [...existing..., 'embedding_info']
    
    def has_embedding(self, obj):
        """Show if item has embedding."""
        return bool(obj.embedding)
    has_embedding.boolean = True
    has_embedding.short_description = "Has Embedding"
    
    def embedding_status(self, obj):
        """Show embedding status with visual indicator."""
        if obj.embedding:
            return format_html(
                '<span style="color: green;">✓ Generated</span>'
            )
        return format_html(
            '<span style="color: gray;">- Not generated</span>'
        )
    embedding_status.short_description = "Embedding Status"
    
    def embedding_info(self, obj):
        """Display embedding information in detail view."""
        if obj.embedding:
            return f"Embedding dimensions: {len(obj.embedding)}"
        return "No embedding generated"
    embedding_info.short_description = "Embedding Information"
    
    actions = [...existing..., 'regenerate_embeddings']
    
    def regenerate_embeddings(self, request, queryset):
        """Admin action to regenerate embeddings."""
        count = 0
        for item in queryset:
            if item.active and item.name:
                generate_item_embedding.delay(item.pk)
                count += 1
        
        self.message_user(
            request,
            f"Queued {count} items for embedding regeneration."
        )
    regenerate_embeddings.short_description = "Regenerate embeddings"
```

### Step 7: Update Dependencies

**File**: `pyproject.toml` (add to dependencies)

```toml
[project]
dependencies = [
    ...existing...,
    "openai>=1.0.0",
]
```

## Configuration

### Environment Variables

Add to `.env` file:

```bash
OPENAI_API_KEY=your_api_key_here
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

### Docker Configuration

No changes needed - environment variables are already passed through.

## Testing Strategy

### Unit Tests

**File**: `bubble/items/tests/test_embeddings.py`

```python
from unittest.mock import patch, MagicMock
from django.test import TestCase
from bubble.items.services.embeddings import EmbeddingService
from bubble.items.models import Item
from bubble.users.models import User

class EmbeddingServiceTest(TestCase):
    def setUp(self):
        self.service = EmbeddingService()
        self.user = User.objects.create_user(username='testuser')
        self.item = Item.objects.create(
            user=self.user,
            name="Test Item",
            description="Test Description"
        )
    
    @patch('openai.embeddings.create')
    def test_generate_embedding_success(self, mock_create):
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
        mock_create.return_value = mock_response
        
        embedding = self.service.generate_embedding("test text")
        self.assertEqual(len(embedding), 1536)
    
    def test_prepare_item_text(self):
        text = self.service.prepare_item_text(self.item)
        self.assertIn("Test Item", text)
        self.assertIn("Test Description", text)
```

### Integration Tests

**File**: `bubble/items/tests/test_signals.py`

```python
from unittest.mock import patch
from django.test import TestCase
from bubble.items.models import Item
from bubble.users.models import User

class SignalTest(TestCase):
    @patch('bubble.items.tasks.generate_item_embedding.delay')
    def test_embedding_triggered_on_save(self, mock_task):
        user = User.objects.create_user(username='testuser')
        item = Item.objects.create(
            user=user,
            name="Test Item",
            active=True
        )
        
        mock_task.assert_called_once_with(item.pk)
```

## Error Handling

1. **API Failures**: Celery task includes retry logic with exponential backoff
2. **Missing Fields**: Skip embedding generation if required fields are missing
3. **Rate Limiting**: Consider implementing rate limiting for OpenAI API calls
4. **Logging**: Comprehensive logging at all levels for debugging

## Security Considerations

1. **API Key**: Store OpenAI API key securely in environment variables
2. **Data Privacy**: Ensure item data sent to OpenAI complies with privacy policies
3. **Access Control**: Embedding generation only triggered by authenticated saves

## Future Enhancements

1. **Batch Processing**: Process multiple items in a single API call
2. **Similarity Search**: Implement vector similarity search using pgvector
3. **Recommendation Engine**: Use embeddings for item recommendations
4. **Multilingual Support**: Generate embeddings for German content
5. **Embedding Updates**: Track which fields changed to avoid unnecessary regeneration

## Deployment Checklist

- [ ] Add OpenAI API key to production environment
- [ ] Run migrations to ensure pgvector extension is enabled
- [ ] Deploy code changes
- [ ] Monitor Celery tasks for errors
- [ ] Test embedding generation on staging
- [ ] Consider rate limits and costs