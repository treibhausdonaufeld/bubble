"""Embedding generation for semantic search using sentence-transformers."""

from functools import lru_cache

from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """
    Load and cache the embedding model.

    Uses all-MiniLM-L6-v2 which produces 384-dimensional embeddings.
    This model is lightweight, fast, and suitable for semantic search.

    Returns:
        SentenceTransformer: The loaded model instance.
    """
    return SentenceTransformer("all-MiniLM-L6-v2")


def generate_item_embedding(item) -> list[float] | None:
    """
    Generate an embedding vector for an Item.

    Combines the item's name and description into a single text representation
    and encodes it using the embedding model.

    Args:
        item: An Item model instance with name and description fields.

    Returns:
        list[float] | None: A 384-dimensional embedding vector, or None if no text.
    """
    # Combine name and description with a separator
    text_parts = []
    if item.name:
        text_parts.append(item.name)
    if item.description:
        text_parts.append(item.description)

    # If no text available, return None
    if not text_parts:
        return None

    text = " | ".join(text_parts)

    # Generate embedding
    model = get_embedding_model()
    embedding = model.encode(text, convert_to_numpy=True)

    # Convert to list for database storage
    return embedding.tolist()
