# Embedding System with Temporal Workflow - Implementation Plan

## Overview

This document outlines the implementation plan for integrating sentence-transformer embeddings into the bubble platform using Temporal workflows, following the existing Anthropic workflow pattern.

## Model Configuration

**Model**: `paraphrase-multilingual-mpnet-base-v2`
- **Dimensions**: 768 (updated from 384)
- **Language Support**: Excellent multilingual support including German
- **Performance**: Better semantic understanding than MiniLM variant

## Architecture Components

### 1. Temporal Workflow Structure

```
bubble/items/temporal/
├── embedding_workflows.py      # Workflow definitions
├── embedding_activities.py     # Activity implementations
├── embedding_service.py        # Service layer for Django integration
├── embedding_dataclasses.py    # Request/Response data structures
└── sentence_transformer_client.py  # Sentence Transformer wrapper
```

### 2. Workflow Design

#### Main Workflow: `ItemEmbeddingWorkflow`
- Processes single or batch items for embedding generation
- Orchestrates the embedding pipeline
- Handles retries and error recovery

#### Activities:
1. `fetch_items_for_embedding` - Retrieves items needing embeddings
2. `generate_item_embedding` - Creates embeddings using Sentence Transformers
3. `store_item_embedding` - Saves embeddings to database
4. `batch_generate_embeddings` - Processes multiple items efficiently

### 3. Data Models

#### Request Classes:
```python
@dataclass
class ItemEmbeddingRequest:
    item_id: int
    force_regenerate: bool = False
    
@dataclass
class BatchEmbeddingRequest:
    item_ids: List[int]
    batch_size: int = 10
    force_regenerate: bool = False
```

#### Response Classes:
```python
@dataclass
class ItemEmbeddingResult:
    item_id: int
    success: bool
    embedding_dimensions: Optional[int] = None
    error_message: Optional[str] = None
    
@dataclass
class BatchEmbeddingResult:
    total_items: int
    successful: int
    failed: int
    results: List[ItemEmbeddingResult]
```

### 4. Activity Implementations

#### `generate_item_embedding` Activity:
- Loads item from database
- Prepares text: `Name | Description | Category | Type | Status`
- Generates embedding using Sentence Transformers
- Returns embedding vector

#### `store_item_embedding` Activity:
- Updates item's embedding field
- Sets embedding generation timestamp
- Handles database transactions

### 5. Filtering Strategy

**Active Items Only**: 
- Filter query: `Item.objects.filter(active=True)`
- Only generate embeddings for active items
- Similarity search also filters by `active=True`

### 6. Django Integration

#### Management Commands:
- `generate_embeddings` - Process all active items without embeddings
- `regenerate_embeddings` - Force regenerate for specified items
- `check_embedding_status` - Report on embedding coverage

#### Admin Actions:
- "Generate Embeddings" - Trigger workflow for selected items
- View embedding status in list display
- Bulk operations support

#### Signal Handlers:
- Post-save signal on Item model
- Queue embedding generation if:
  - Item is active
  - Item has name and description
  - Embedding doesn't exist or content changed

### 7. Similarity Search Implementation

```python
def find_similar_items(query_text: str, limit: int = 10):
    # Generate query embedding
    query_embedding = generate_embedding(query_text)
    
    # Search only active items with embeddings
    similar_items = (
        Item.objects
        .filter(active=True, embedding__isnull=False)
        .annotate(distance=CosineDistance('embedding', query_embedding))
        .order_by('distance')[:limit]
    )
    return similar_items
```

### 8. Temporal Service Layer

#### `EmbeddingTemporalService`:
- Singleton pattern like existing service
- Methods:
  - `start_item_embedding(item_id)`
  - `start_batch_embedding(item_ids)`
  - `get_embedding_status(workflow_id)`
  - `cancel_embedding_workflow(workflow_id)`

### 9. Worker Configuration

Update existing worker to include embedding activities:
```python
# In temporal_worker.py
from bubble.items.temporal.embedding_activities import (
    fetch_items_for_embedding,
    generate_item_embedding,
    store_item_embedding,
    batch_generate_embeddings
)
from bubble.items.temporal.embedding_workflows import ItemEmbeddingWorkflow

# Register activities and workflows
activities = [
    # ... existing activities
    fetch_items_for_embedding,
    generate_item_embedding,
    store_item_embedding,
    batch_generate_embeddings
]

workflows = [
    # ... existing workflows
    ItemEmbeddingWorkflow
]
```

### 10. Migration Requirements

1. Update Item model embedding field dimensions to 768
2. Create migration for dimension change
3. Clear existing embeddings (incompatible dimensions)

### 11. Environment Configuration

Update settings:
```python
# config/settings/temporal.py
SENTENCE_TRANSFORMER_MODEL = env(
    "SENTENCE_TRANSFORMER_MODEL", 
    default="sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
)
EMBEDDING_DIMENSION = env.int("EMBEDDING_DIMENSION", default=768)
```

### 12. Performance Considerations

- Batch processing for efficiency
- Model loaded once per worker
- Use model caching
- Implement rate limiting for large batches
- Monitor memory usage (larger model)

### 13. Error Handling

- Retry failed embeddings with exponential backoff
- Log failures for manual review
- Graceful degradation if embedding service unavailable
- Track items that consistently fail

### 14. Testing Strategy

- Unit tests for activities
- Integration tests for workflows
- Performance benchmarks
- Memory usage monitoring
- Multilingual content testing

## Implementation Order

1. Update model configuration and create migration
2. Implement sentence transformer client
3. Create dataclasses for requests/responses
4. Implement activities
5. Create workflow
6. Build service layer
7. Update worker registration
8. Add Django integration (commands, admin)
9. Implement signal handlers
10. Create similarity search utilities
11. Add monitoring and logging
12. Write tests

## Next Steps

After reviewing this plan, we will:
1. Update the model configuration to use mpnet-base
2. Create the migration for 768 dimensions
3. Begin implementing the Temporal workflow components