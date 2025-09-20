"""
Embeddings service for generating and managing book embeddings.
"""
import logging
from abc import ABC, abstractmethod
from typing import List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


class EmbeddingBackend(ABC):
    """Abstract base class for embedding backends."""
    
    @abstractmethod
    def encode(self, text: str) -> List[float]:
        """Generate embedding for the given text."""
        pass
    
    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Return the dimensions of the embeddings."""
        pass


class SentenceTransformerBackend(EmbeddingBackend):
    """SentenceTransformers backend for generating embeddings."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._dimensions = 384  # all-MiniLM-L6-v2 dimensions
    
    @property
    def model(self):
        """Lazy load the model to avoid loading during imports."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                logger.info(f"Loaded SentenceTransformer model: {self.model_name}")
            except ImportError:
                logger.error("sentence-transformers package not found. Please install it: pip install sentence-transformers")
                raise
        return self._model
    
    def encode(self, text: str) -> List[float]:
        """Generate embedding for the given text."""
        if not text.strip():
            # Return zero vector for empty text
            return [0.0] * self.dimensions
        
        try:
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Return zero vector on error
            return [0.0] * self.dimensions
    
    @property
    def dimensions(self) -> int:
        """Return the dimensions of the embeddings."""
        return self._dimensions


class OpenAIBackend(EmbeddingBackend):
    """OpenAI backend for generating embeddings."""
    
    def __init__(self, model_name: str = "text-embedding-3-small"):
        self.model_name = model_name
        self._dimensions = 1536 if model_name == "text-embedding-3-small" else 1536
        
    def encode(self, text: str) -> List[float]:
        """Generate embedding for the given text using OpenAI API."""
        if not text.strip():
            return [0.0] * self.dimensions
            
        try:
            from openai import OpenAI
            import os
            
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            response = client.embeddings.create(
                model=self.model_name,
                input=text
            )
            return response.data[0].embedding
        except ImportError:
            logger.error("OpenAI package not found. Please install it: pip install openai")
            return [0.0] * self.dimensions
        except Exception as e:
            logger.error(f"Error generating OpenAI embedding: {e}")
            return [0.0] * self.dimensions
    
    @property  
    def dimensions(self) -> int:
        """Return the dimensions of the embeddings."""
        return self._dimensions


class EmbeddingsService:
    """Service for managing book embeddings."""
    
    def __init__(self, backend: Optional[EmbeddingBackend] = None):
        if backend is None:
            # Default to SentenceTransformers backend
            backend = SentenceTransformerBackend()
        self.backend = backend
    
    def generate_book_embedding(self, book) -> Optional[List[float]]:
        """Generate embedding for a book based on its content."""
        content = book.get_content_for_embedding()
        if not content.strip():
            logger.warning(f"No content available for book {book.id} to generate embedding")
            return None
            
        try:
            embedding = self.backend.encode(content)
            logger.info(f"Generated embedding for book {book.id}: {book.title}")
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding for book {book.id}: {e}")
            return None
    
    def update_book_embedding(self, book) -> bool:
        """Update the embedding for a book and save it."""
        embedding = self.generate_book_embedding(book)
        if embedding is not None:
            book.embedding = embedding
            book.save(update_fields=['embedding'])
            return True
        return False
    
    @property
    def dimensions(self) -> int:
        """Return the dimensions of the current backend."""
        return self.backend.dimensions


# Global instance
_embeddings_service = None

def get_embeddings_service() -> EmbeddingsService:
    """Get the global embeddings service instance."""
    global _embeddings_service
    if _embeddings_service is None:
        # Check settings for preferred backend
        backend_type = getattr(settings, 'BOOK_EMBEDDING_BACKEND', 'sentence_transformers')
        
        if backend_type == 'openai':
            backend = OpenAIBackend()
        else:
            backend = SentenceTransformerBackend()
            
        _embeddings_service = EmbeddingsService(backend)
    
    return _embeddings_service