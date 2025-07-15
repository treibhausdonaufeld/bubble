# Simple Embedding Implementation Plan

## Overview

This is a simplified plan for implementing embeddings that:
1. Automatically generates embeddings when items are published (not saved as draft)
2. Provides similarity search functionality in the item list view
3. Uses `paraphrase-multilingual-mpnet-base-v2` model (768 dimensions)

## Key Components

### 1. Model Update

Update embedding field dimensions from 384 to 768:
```python
# bubble/items/models.py
embedding = VectorField(
    dimensions=768,  # Updated for mpnet-base model
    null=True,
    blank=True,
    help_text=_("Vector embedding for similarity search"),
)
```

### 2. Embedding Service

Create a simple service class:
```python
# bubble/items/services/embedding_service.py
from sentence_transformers import SentenceTransformer
from django.conf import settings

class EmbeddingService:
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def model(self):
        if self._model is None:
            self._model = SentenceTransformer(settings.SENTENCE_TRANSFORMER_MODEL)
        return self._model
    
    def generate_embedding(self, text: str):
        """Generate embedding for text"""
        return self.model.encode(text).tolist()
    
    def prepare_item_text(self, item):
        """Prepare item text for embedding"""
        parts = []
        if item.name:
            parts.append(f"Name: {item.name}")
        if item.description:
            parts.append(f"Description: {item.description}")
        if item.category:
            parts.append(f"Category: {item.category.get_hierarchy()}")
        parts.append(f"Type: {item.get_item_type_display()}")
        parts.append(f"Condition: {item.get_status_display()}")
        return " | ".join(parts)
```

### 3. Form Integration

Modify the item form view to generate embeddings on publish:
```python
# bubble/items/views.py - in ItemCreateView/ItemUpdateView

def form_valid(self, form):
    response = super().form_valid(form)
    
    # Check if "publish" button was clicked (not draft)
    if 'publish' in self.request.POST and self.object.active:
        # Generate embedding
        from bubble.items.services.embedding_service import EmbeddingService
        service = EmbeddingService()
        text = service.prepare_item_text(self.object)
        embedding = service.generate_embedding(text)
        
        # Save embedding
        self.object.embedding = embedding
        self.object.save(update_fields=['embedding'])
    
    return response
```

### 4. Similarity Search View

Create a new view for similarity search:
```python
# bubble/items/views.py

class ItemSimilaritySearchView(ListView):
    model = Item
    template_name = 'items/item_similarity_list.html'
    context_object_name = 'items'
    paginate_by = 10
    
    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        if not query:
            return Item.objects.none()
        
        # Generate embedding for search query
        from bubble.items.services.embedding_service import EmbeddingService
        from pgvector.django import CosineDistance
        
        service = EmbeddingService()
        query_embedding = service.generate_embedding(query)
        
        # Search only active items with embeddings
        return (
            Item.objects
            .filter(active=True, embedding__isnull=False)
            .annotate(distance=CosineDistance('embedding', query_embedding))
            .order_by('distance')[:10]  # Top 10 results
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context
```

### 5. URL Configuration

Add similarity search URL:
```python
# bubble/items/urls.py
urlpatterns = [
    # ... existing patterns
    path('search/similar/', ItemSimilaritySearchView.as_view(), name='similarity_search'),
]
```

### 6. Template Updates

#### Item List Template Enhancement
Add a similarity search button/link in `item_list.html`:
```html
<!-- In the search section -->
<div class="filter-section">
    <label class="form-label fw-bold">
        <i class="fas fa-search"></i> {% trans "Search" %}
    </label>
    <div class="search-container">
        <!-- Existing search input -->
        <input type="text" name="search" class="form-control search-input" ...>
        
        <!-- New similarity search link -->
        <div class="mt-2">
            <a href="{% url 'items:similarity_search' %}" class="btn btn-sm btn-outline-primary">
                <i class="fas fa-brain"></i> {% trans "AI-Powered Search" %}
            </a>
        </div>
    </div>
</div>
```

#### Similarity Search Template
Create `templates/items/item_similarity_list.html`:
```html
{% extends "base.html" %}
{% load i18n %}

{% block title %}{% trans "AI Search Results" %}{% endblock %}

{% block content %}
<div class="container">
    <div class="row">
        <div class="col-12">
            <h2>{% trans "AI-Powered Search" %}</h2>
            
            <!-- Search Form -->
            <form method="get" class="mb-4">
                <div class="input-group">
                    <input type="text" 
                           name="q" 
                           class="form-control" 
                           placeholder="{% trans 'Describe what you are looking for...' %}"
                           value="{{ search_query }}">
                    <button class="btn btn-primary" type="submit">
                        <i class="fas fa-search"></i> {% trans "Search" %}
                    </button>
                </div>
                <small class="text-muted">
                    {% trans "Example: 'Gaming laptop with good graphics' or 'Kaffeemaschine für Espresso'" %}
                </small>
            </form>
            
            <!-- Results -->
            {% if search_query %}
                {% if items %}
                    <h3>{% trans "Top 10 Similar Items" %}</h3>
                    <div class="row">
                        {% for item in items %}
                            <div class="col-lg-4 col-md-6 mb-4">
                                {% include 'includes/item_card.html' with item=item %}
                                <small class="text-muted">
                                    {% trans "Similarity" %}: {{ item.distance|floatformat:3 }}
                                </small>
                            </div>
                        {% endfor %}
                    </div>
                {% else %}
                    <div class="alert alert-info">
                        {% trans "No similar items found. Try a different search query." %}
                    </div>
                {% endif %}
            {% endif %}
            
            <div class="mt-3">
                <a href="{% url 'items:list' %}" class="btn btn-secondary">
                    <i class="fas fa-arrow-left"></i> {% trans "Back to All Items" %}
                </a>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

### 7. Migration

1. Update model to 768 dimensions
2. Create and run migration:
```bash
just manage makemigrations items
just manage migrate
```

### 8. Settings Update

```python
# config/settings/temporal.py
SENTENCE_TRANSFORMER_MODEL = env(
    "SENTENCE_TRANSFORMER_MODEL", 
    default="sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
)
EMBEDDING_DIMENSION = env.int("EMBEDDING_DIMENSION", default=768)
```

## Implementation Steps

1. **Update Model**: Change embedding dimensions to 768
2. **Create Migration**: Update database schema
3. **Create Service**: Implement EmbeddingService class
4. **Update Views**: Modify form_valid to generate embeddings on publish
5. **Create Search View**: Implement ItemSimilaritySearchView
6. **Update URLs**: Add similarity search route
7. **Create Templates**: Add similarity search UI
8. **Test**: Verify embedding generation and search functionality

## Key Features

- **Automatic Generation**: Embeddings created only when items are published (not drafts)
- **Active Items Only**: Search filters for `active=True` items only
- **Top 10 Results**: Returns the 10 most similar items
- **Multilingual**: Supports German text with mpnet model
- **Simple UI**: Dedicated search page for similarity queries

## Notes

- No Temporal workflow needed for this simple implementation
- Embeddings generated synchronously on publish (fast with sentence-transformers)
- Model loaded once as singleton for efficiency
- No batch processing needed - items processed individually on save