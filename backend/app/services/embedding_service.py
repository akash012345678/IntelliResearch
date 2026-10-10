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

    _model = None
    _loading = False
    _load_failed = False
    _cache: Dict[str, List[float]] = {}

    @classmethod
    def get_model(cls):
        """
        Lazy-load the Sentence-BERT model as a singleton.
        If loading fails or on memory-constrained servers, safely returns None to use fast fallback.
        """
        if cls._load_failed:
            return None

        if cls._model is None and not cls._loading:
            cls._loading = True
            logger.info(f"Initializing Sentence-BERT model: '{MODEL_NAME}'...")
            try:
                import torch
                torch.set_num_threads(1)  # Limit CPU threads to prevent server lockup on cloud free tiers
                from sentence_transformers import SentenceTransformer
                cls._model = SentenceTransformer(MODEL_NAME)
                logger.info(f"Successfully loaded Sentence-BERT model '{MODEL_NAME}'.")
            except Exception as e:
                cls._load_failed = True
                logger.warning(f"Could not initialize SentenceTransformer '{MODEL_NAME}' ({e}). Fast deterministic embeddings will be used.")
            finally:
                cls._loading = False
        return cls._model

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

        try:
            model = cls.get_model()
            if model is None:
                raise RuntimeError("Embedding model unavailable")
            raw_embedding = model.encode(
                clean_text,
                convert_to_numpy=True,
                normalize_embeddings=True
            )

            embedding_list: List[float] = [float(x) for x in raw_embedding.tolist()]
            if len(embedding_list) != EXPECTED_DIMENSION:
                raise ValueError(f"Embedding dimension mismatch: expected {EXPECTED_DIMENSION}, got {len(embedding_list)}")

            cls._cache[clean_text] = embedding_list
            return embedding_list
        except ValueError as ve:
            raise ve
        except Exception as e:
            logger.warning(f"Embedding model unavailable or error ({e}). Generating fallback deterministic hash vector.")
            import hashlib
            import numpy as np
            h = hashlib.sha256(clean_text.encode('utf-8')).digest()
            np.random.seed(int.from_bytes(h[:4], 'big'))
            vec = np.random.randn(EXPECTED_DIMENSION)
            vec = vec / (np.linalg.norm(vec) + 1e-9)
            fallback_list = [float(x) for x in vec]
            cls._cache[clean_text] = fallback_list
            return fallback_list

    @classmethod
    def generate_embeddings_batch(cls, texts: List[str]) -> List[List[float]]:
        """
        Generate normalized vector embeddings for a list of text strings in a SINGLE parallel batch call.
        Utilizes in-memory cache for any texts already computed.
        """
        if not texts:
            return []

        results: List[Optional[List[float]]] = [None] * len(texts)
        uncached_indices: List[int] = []
        uncached_texts: List[str] = []

        for i, raw_t in enumerate(texts):
            clean_t = (raw_t or "").strip()
            if not clean_t:
                results[i] = [0.0] * EXPECTED_DIMENSION
            elif clean_t in cls._cache:
                results[i] = cls._cache[clean_t]
            else:
                uncached_indices.append(i)
                uncached_texts.append(clean_t)

        if uncached_texts:
            try:
                model = cls.get_model()
                if model is None:
                    raise RuntimeError("Embedding model unavailable")
                batch_embeddings = model.encode(
                    uncached_texts,
                    batch_size=64,
                    convert_to_numpy=True,
                    normalize_embeddings=True
                )
                for idx, clean_t, raw_emb in zip(uncached_indices, uncached_texts, batch_embeddings):
                    emb_list = [float(x) for x in raw_emb.tolist()]
                    cls._cache[clean_t] = emb_list
                    results[idx] = emb_list
            except Exception as e:
                logger.error(f"Batch embedding generation error: {e}")
                # Fallback to individual calls
                for idx, clean_t in zip(uncached_indices, uncached_texts):
                    results[idx] = cls.generate_embedding(clean_t)

        return [r if r is not None else [0.0] * EXPECTED_DIMENSION for r in results]

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
