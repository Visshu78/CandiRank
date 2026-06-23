import os
from typing import List
from sentence_transformers import SentenceTransformer

# Load the embedding model once at module import
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
_embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

def encode_batch(texts: List[str], batch_size: int = 32, show_progress: bool = False):
    """
    Encode a list of texts using the configured embedding model.
    
    Args:
        texts: List of text strings to encode.
        batch_size: Number of texts to process per batch.
        show_progress: Whether to display a progress bar.
    
    Returns:
        List of embedding vectors (numpy arrays).
    """
    return _embedding_model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=show_progress,
        convert_to_numpy=True,
        normalize_embeddings=False,
    )

def encode_single(text: str, **kwargs) -> List[float]:
    """
    Encode a single text string.
    
    Args:
        text: Text to encode.
        **kwargs: Additional arguments passed to encode_batch.
    
    Returns:
        Embedding vector for the text.
    """
    return encode_batch([text], **kwargs)[0]

# Export public API
__all__ = ["encode_batch", "encode_single"]
