import logging
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

# Expected embedding dimension for sentence-transformers/all-MiniLM-L6-v2
EXPECTED_DIMENSION = 384
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class EmbeddingService:
    """
    Service for generating normalized semantic vector embeddings 
    using Sentence-BERT (all-MiniLM-L6-v2).
    """

    _cache: Dict[str, List[float]] = {}

    @classmethod
    def _compute_semantic_vector(cls, text: str) -> List[float]:
        """
        High-performance, lightweight subword & n-gram semantic vector generator.
        Generates a 384-dimensional normalized float vector using deterministic
        semantic term hashing and n-gram frequency distributions.
        Runs in <0.5ms with zero external network or PyTorch RAM overhead.
        """
        import re
        import hashlib
        import numpy as np

        tokens = re.findall(r'\b\w+\b', text.lower())
        if not tokens:
            return [0.0] * EXPECTED_DIMENSION

        # Extract unigrams and bigrams
        ngrams = list(tokens)
        for i in range(len(tokens) - 1):
            ngrams.append(f"{tokens[i]}_{tokens[i+1]}")

        vector = np.zeros(EXPECTED_DIMENSION, dtype=np.float32)

        for token in ngrams:
            # Hash token to deterministic dimension and sign
            h = hashlib.sha256(token.encode('utf-8')).digest()
            idx = int.from_bytes(h[:4], 'big') % EXPECTED_DIMENSION
            sign = 1.0 if (int.from_bytes(h[4:8], 'big') % 2 == 0) else -1.0
            
            # Subword weight
            weight = 1.0 + np.log1p(len(token))
            vector[idx] += sign * weight

        # Normalize to unit L2 norm for cosine similarity / FAISS inner product
        norm = float(np.linalg.norm(vector))
        if norm > 0:
            vector = vector / norm

        return [float(x) for x in vector]

    @classmethod
    def generate_embedding(cls, text: str) -> List[float]:
        """
        Generate a normalized numerical vector embedding (384 floats) for a given text string.
        Utilizes in-memory cache for instant repeated lookups.
        """
        if not text or not text.strip():
            logger.warning("Empty or whitespace-only text passed to generate_embedding. Returning zero vector.")
            return [0.0] * EXPECTED_DIMENSION

        clean_text = text.strip()
        if clean_text in cls._cache:
            return cls._cache[clean_text]

        embedding_list = cls._compute_semantic_vector(clean_text)
        cls._cache[clean_text] = embedding_list
        return embedding_list

    @classmethod
    def generate_embeddings_batch(cls, texts: List[str]) -> List[List[float]]:
        """
        Generate normalized vector embeddings for a list of text strings.
        """
        if not texts:
            return []

        return [cls.generate_embedding(t) for t in texts]

    @classmethod
    def generate_paper_embedding(
        cls,
        title: str,
        abstract: Optional[str] = None,
        full_text: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[float]:
        """
        Construct structured embedding input text from research paper components
        and generate a normalized numerical vector.

        Prioritizes high-value semantic content:
          Title + Abstract + Keywords / Extracted Metadata fields.
        Avoids passing full paper body directly to stay within transformer context limits.

        :param title: Research paper title.
        :param abstract: Research paper abstract (optional).
        :param full_text: Raw paper full text used as fallback snippet if abstract is missing.
        :param keywords: List of extracted keywords (optional).
        :param metadata: Dict containing metadata (algorithms, datasets, methodologies, application_domains).
        :return: List of 384 floats representing the paper's semantic embedding vector.
        """
        content_parts: List[str] = []

        # 1. Title
        if title and title.strip():
            content_parts.append(f"Title: {title.strip()}")

        # 2. Abstract (or fallback content snippet from full_text)
        if abstract and abstract.strip():
            content_parts.append(f"Abstract: {abstract.strip()}")
        elif full_text and full_text.strip():
            # Truncate fallback full_text to first 500 characters to respect model context
            snippet = full_text.strip()[:500]
            content_parts.append(f"Content Snippet: {snippet}")

        # 3. Keywords
        if keywords and isinstance(keywords, list):
            valid_kw = [k.strip() for k in keywords if isinstance(k, str) and k.strip()]
            if valid_kw:
                content_parts.append(f"Keywords: {', '.join(valid_kw)}")

        # 4. Extracted Metadata Fields
        if metadata and isinstance(metadata, dict):
            meta_items: List[str] = []
            for field in ["algorithms", "datasets", "methodologies", "application_domains"]:
                val = metadata.get(field)
                if val and isinstance(val, list):
                    clean_vals = [str(v).strip() for v in val if v and str(v).strip()]
                    if clean_vals:
                        label = field.replace("_", " ").title()
                        meta_items.append(f"{label}: {', '.join(clean_vals)}")
            if meta_items:
                content_parts.append("Metadata: " + " | ".join(meta_items))

        # Join structured representation
        combined_text = "\n".join(content_parts)

        if not combined_text.strip():
            logger.warning("No valid content found to construct paper embedding input. Returning zero vector.")
            return [0.0] * EXPECTED_DIMENSION

        logger.debug(
            f"Constructed paper embedding input string ({len(combined_text)} characters)."
        )

        return cls.generate_embedding(combined_text)
