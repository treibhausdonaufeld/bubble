import logging

from django.conf import settings
from django.db.models import Q
from sentence_transformers import SentenceTransformer

from bubble.items.models import Item

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and managing item embeddings."""

    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def model(self) -> SentenceTransformer:
        """Lazy load the sentence transformer model."""
        if self._model is None:
            logger.info(
                f"Loading sentence transformer model: {settings.SENTENCE_TRANSFORMER_MODEL}"
            )
            self._model = SentenceTransformer(settings.SENTENCE_TRANSFORMER_MODEL)
            logger.info(
                f"Model loaded. Embedding dimension: {self._model.get_sentence_embedding_dimension()}"
            )
        return self._model

    def generate_embedding(self, text: str) -> list[float] | None:
        """Generate embedding for text."""
        try:
            if not text:
                logger.warning("Empty text provided for embedding generation")
                return None

            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

    def prepare_item_text(self, item: Item) -> str:
        """Prepare item text for embedding generation."""
        parts = []

        if item.name:
            parts.append(f"Name: {item.name}")

        if item.description:
            parts.append(f"Description: {item.description}")

        if item.category:
            parts.append(f"Category: {item.category.get_hierarchy()}")

        text = " | ".join(parts)
        logger.debug(f"Prepared text for item {item.pk}: {text[:100]}...")

        return text

    def generate_item_embedding(self, item: Item) -> list[float] | None:
        """Generate embedding for an item."""
        text = self.prepare_item_text(item)
        return self.generate_embedding(text)

    def find_similar_items(
        self, query: str, limit: int = 10
    ) -> list[tuple[Item, float]]:
        """Find items similar to the given query.

        Args:
            query: Search query text
            limit: Maximum number of items to return (default 10)

        Returns:
            List of tuples (item, similarity_score) ordered by similarity
        """
        try:
            if not query.strip():
                logger.warning("Empty query provided for similarity search")
                return []

            # Generate embedding for the search query
            query_embedding = self.generate_embedding(query.strip())
            if not query_embedding:
                logger.warning("Could not generate embedding for query: %s", query)
                return []

            # Find similar items using pgvector cosine distance
            # Filter for active items with non-null embeddings
            # Convert list to vector format for PostgreSQL
            query_vector = str(query_embedding).replace(
                " ", ""
            )  # Remove spaces for vector format
            similar_items = (
                Item.objects.filter(Q(active=True) & Q(embedding__isnull=False))
                .extra(
                    select={"similarity": "embedding <=> %s::vector"},
                    select_params=[query_vector],
                )
                .order_by("similarity")  # Lower distance = higher similarity
                .select_related("user", "category")
                .prefetch_related("images")[:limit]
            )

            # Convert distance to similarity score (1 - distance for cosine distance)
            results = []
            for item in similar_items:
                similarity_score = 1.0 - float(item.similarity)
                results.append((item, similarity_score))

            logger.info(
                "Found %d similar items for query: %s",
                len(results),
                query[:50] + "..." if len(query) > 50 else query,
            )

            return results

        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return []
