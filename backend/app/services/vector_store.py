import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
import numpy as np
import faiss

logger = logging.getLogger(__name__)

EXPECTED_DIMENSION = 384

# Default persistent directory and file paths: backend/app/vector_store/
DEFAULT_VECTOR_STORE_DIR = Path(__file__).resolve().parent.parent / "vector_store"
DEFAULT_INDEX_FILE = DEFAULT_VECTOR_STORE_DIR / "research_papers.index"
DEFAULT_MAPPING_FILE = DEFAULT_VECTOR_STORE_DIR / "paper_id_mapping.json"


class VectorStore:
    """
    FAISS-backed vector store for normalized 384-dimensional Sentence-BERT embeddings.
    Uses faiss.IndexFlatIP(384) for inner product (cosine similarity on normalized vectors).
    Maintains a persistent two-way mapping between FAISS vector positions and PostgreSQL ResearchPaper IDs.
    """

    def __init__(
        self,
        dimension: int = EXPECTED_DIMENSION,
        index_path: Optional[Union[str, Path]] = None,
        mapping_path: Optional[Union[str, Path]] = None
    ):
        """
        Initialize the FAISS VectorStore.

        :param dimension: Dimensionality of vectors. Must be exactly 384.
        :param index_path: Custom path for persistent index file.
                           Defaults to backend/app/vector_store/research_papers.index
        :param mapping_path: Custom path for persistent mapping file.
                            Defaults to backend/app/vector_store/paper_id_mapping.json
        """
        if dimension != EXPECTED_DIMENSION:
            logger.error(f"Invalid dimension {dimension}. VectorStore requires {EXPECTED_DIMENSION}.")
            raise ValueError(f"VectorStore dimension must be exactly {EXPECTED_DIMENSION}, got {dimension}.")

        self.dimension: int = dimension
        self.index_path: Path = Path(index_path) if index_path else DEFAULT_INDEX_FILE
        self.mapping_path: Path = Path(mapping_path) if mapping_path else DEFAULT_MAPPING_FILE
        
        self.index: faiss.IndexFlatIP = faiss.IndexFlatIP(self.dimension)
        
        # Two-way persistent mappings
        # Position (int) -> paper_id (int or str)
        self.position_to_paper: Dict[int, Union[int, str]] = {}
        # paper_id (str) -> Position (int)
        self.paper_to_position: Dict[str, int] = {}

        if self.index_path.exists() and self.mapping_path.exists():
            try:
                self.load_index()
            except Exception as e:
                logger.warning(f"Could not auto-load existing VectorStore files: {e}")

        logger.info(f"Initialized FAISS VectorStore with IndexFlatIP (dim={self.dimension}).")

    def _validate_vector(
        self,
        embedding: Union[List[float], np.ndarray],
        normalize: bool = False
    ) -> np.ndarray:
        """
        Validate vector dimension and numeric validity, returning float32 2D numpy array (1, 384).

        :param embedding: Vector input as list of floats or 1D/2D numpy array.
        :param normalize: If True, normalize non-zero vector to unit L2 norm.
        :return: 2D numpy array of shape (1, 384) with float32 dtype.
        """
        if embedding is None:
            logger.error("Embedding vector cannot be None.")
            raise ValueError("Embedding vector cannot be None.")

        if isinstance(embedding, list):
            try:
                vec_np = np.array(embedding, dtype=np.float32)
            except (ValueError, TypeError) as e:
                logger.error(f"Failed to convert list to float numpy array: {e}")
                raise ValueError("Embedding contains invalid non-numeric values.") from e
        elif isinstance(embedding, np.ndarray):
            if not np.issubdtype(embedding.dtype, np.number):
                logger.error(f"Numpy array contains non-numeric dtype: {embedding.dtype}")
                raise ValueError("Embedding contains invalid non-numeric values.")
            vec_np = embedding.astype(np.float32)
        else:
            logger.error(f"Unsupported vector type: {type(embedding)}. Expected List[float] or np.ndarray.")
            raise TypeError(f"Vector must be a list or numpy array, got {type(embedding)}.")

        # Check for NaN or Inf values
        if np.isnan(vec_np).any() or np.isinf(vec_np).any():
            logger.error("Embedding vector contains NaN or Infinite values.")
            raise ValueError("Embedding contains invalid numeric values (NaN or Inf).")

        # Validate dimensions
        if vec_np.ndim == 1:
            if vec_np.shape[0] != self.dimension:
                logger.error(f"Vector dimension mismatch! Expected {self.dimension}, got {vec_np.shape[0]}.")
                raise ValueError(f"Vector dimension mismatch: expected {self.dimension}, got {vec_np.shape[0]}.")
            vec_np = vec_np.reshape(1, -1)
        elif vec_np.ndim == 2:
            if vec_np.shape[0] != 1 or vec_np.shape[1] != self.dimension:
                logger.error(f"Vector dimension mismatch! Expected shape (1, {self.dimension}), got shape {vec_np.shape}.")
                raise ValueError(f"Vector dimension mismatch: expected width {self.dimension}, got shape {vec_np.shape}.")
        else:
            logger.error(f"Invalid vector shape {vec_np.shape}. Must be 1D or 2D array.")
            raise ValueError(f"Invalid vector shape {vec_np.shape}. Must be 1D or 2D array.")

        if normalize:
            norm = float(np.linalg.norm(vec_np))
            if norm > 0 and not np.isclose(norm, 1.0, atol=1e-5):
                vec_np = vec_np / norm

        return vec_np

    def contains_paper(self, paper_id: Union[int, str]) -> bool:
        """
        Check whether a given ResearchPaper ID is already present in the vector store.

        :param paper_id: PostgreSQL ResearchPaper ID.
        :return: True if paper exists in vector store, False otherwise.
        """
        if paper_id is None:
            return False
        return str(paper_id) in self.paper_to_position

    def add_paper(
        self,
        paper_id: Union[int, str],
        embedding: Union[List[float], np.ndarray]
    ) -> int:
        """
        Add a 384-dimensional paper embedding vector to FAISS and record the mapping to paper_id.

        :param paper_id: PostgreSQL ResearchPaper ID (integer or non-empty string).
        :param embedding: 384-dimensional vector embedding.
        :return: FAISS position index assigned to the paper.
        """
        if paper_id is None or (isinstance(paper_id, str) and not paper_id.strip()):
            logger.error("Paper ID cannot be None or empty.")
            raise ValueError("Paper ID cannot be None or empty.")

        if self.contains_paper(paper_id):
            logger.error(f"Duplicate Paper ID detected: '{paper_id}' is already indexed.")
            raise ValueError(f"Paper ID '{paper_id}' is already indexed in VectorStore.")

        vec_np = self._validate_vector(embedding)
        assigned_pos = self.index.ntotal
        self.index.add(vec_np)

        self.position_to_paper[assigned_pos] = paper_id
        self.paper_to_position[str(paper_id)] = assigned_pos

        logger.info(
            f"Successfully added paper ID {paper_id} at FAISS position {assigned_pos}. Total vectors: {self.index.ntotal}."
        )
        return assigned_pos

    def add_vector(self, embedding: Union[List[float], np.ndarray]) -> int:
        """
        Add a raw 384-dimensional vector to the FAISS index (auto-generates paper_id mapping).

        :param embedding: 384-dimensional normalized vector embedding.
        :return: FAISS position index assigned to the vector.
        """
        assigned_pos = self.index.ntotal
        auto_paper_id = f"vector_{assigned_pos}"
        return self.add_paper(paper_id=auto_paper_id, embedding=embedding)

    def get_paper_id(self, vector_position: int) -> Optional[Union[int, str]]:
        """
        Get the PostgreSQL ResearchPaper ID associated with a FAISS vector position.

        :param vector_position: FAISS vector position index (0, 1, 2...).
        :return: Mapped paper_id or None if position is not found.
        """
        if not isinstance(vector_position, int) or vector_position < 0:
            return None
        return self.position_to_paper.get(vector_position)

    def get_vector_position(self, paper_id: Union[int, str]) -> Optional[int]:
        """
        Get the FAISS vector position index associated with a PostgreSQL ResearchPaper ID.

        :param paper_id: PostgreSQL ResearchPaper ID.
        :return: FAISS vector position index or None if paper_id is not indexed.
        """
        if paper_id is None:
            return None
        return self.paper_to_position.get(str(paper_id))

    def search(
        self,
        query_embedding: Union[List[float], np.ndarray],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Perform inner-product (cosine similarity) search for nearest vectors.

        :param query_embedding: 384-dimensional query vector.
        :param top_k: Positive integer specifying top nearest neighbors to return.
        :return: List of search result dicts containing paper_id and similarity_score in descending order.
        """
        try:
            if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0:
                logger.error(f"Invalid top_k parameter '{top_k}'. Must be a positive integer.")
                raise ValueError(f"top_k must be a positive integer, got {top_k}.")

            vec_np = self._validate_vector(query_embedding, normalize=True)

            if self.index.ntotal == 0:
                logger.info("Search called on empty VectorStore. Returning empty results.")
                return []

            search_k = min(top_k, self.index.ntotal)
            distances, indices = self.index.search(vec_np, search_k)

            results: List[Dict[str, Any]] = []
            for score, idx in zip(distances[0], indices[0]):
                if idx == -1:
                    continue
                idx_int = int(idx)
                paper_id = self.get_paper_id(idx_int)
                if paper_id is not None:
                    results.append({
                        "paper_id": paper_id,
                        "similarity_score": float(score)
                    })

            logger.info(f"VectorStore search completed. Found {len(results)} matches for top_k={top_k}.")
            return results

        except (ValueError, TypeError) as ve:
            raise ve
        except Exception as e:
            logger.error(f"Error executing vector search: {e}")
            raise RuntimeError(f"Vector search execution failed: {str(e)}") from e

    def rebuild_index(
        self,
        paper_records: Optional[List[Union[Dict[str, Any], Tuple[Any, ...]]]] = None
    ) -> int:
        """
        Atomically construct a fresh FAISS vector index and paper ID mapping from provided records.

        Each record can be a dictionary:
            {"paper_id": 15, "embedding": [...]}
        Or a tuple:
            (paper_id, embedding)

        :param paper_records: List of records containing paper_id and embedding.
        :return: Count of successfully indexed papers.
        """
        logger.info("Initiating atomic FAISS vector store index rebuild...")
        try:
            new_index = faiss.IndexFlatIP(self.dimension)
            new_pos_to_paper: Dict[int, Union[int, str]] = {}
            new_paper_to_pos: Dict[str, int] = {}

            if paper_records:
                for record in paper_records:
                    paper_id = None
                    embedding = None

                    if isinstance(record, dict):
                        paper_id = record.get("paper_id")
                        embedding = record.get("embedding")
                    elif isinstance(record, (list, tuple)):
                        if len(record) >= 2:
                            paper_id = record[0]
                            embedding = record[1]

                    if paper_id is None or embedding is None:
                        logger.warning("Skipping record during index rebuild: missing paper_id or embedding.")
                        continue

                    str_p_id = str(paper_id)
                    if str_p_id in new_paper_to_pos:
                        logger.warning(f"Skipping duplicate paper_id '{paper_id}' during index rebuild.")
                        continue

                    try:
                        vec_np = self._validate_vector(embedding)
                        assigned_pos = new_index.ntotal
                        new_index.add(vec_np)

                        new_pos_to_paper[assigned_pos] = paper_id
                        new_paper_to_pos[str_p_id] = assigned_pos
                    except (ValueError, TypeError) as ve:
                        logger.warning(f"Skipping paper_id '{paper_id}' during index rebuild: {ve}")
                        continue

            # Atomic swap of in-memory structures
            self.index = new_index
            self.position_to_paper = new_pos_to_paper
            self.paper_to_position = new_paper_to_pos

            # Persist fresh index to disk safely
            self.save_index()

            logger.info(f"VectorStore index rebuild complete. Total indexed papers: {self.index.ntotal}.")
            return self.index.ntotal

        except Exception as e:
            logger.error(f"Failed to rebuild VectorStore index: {e}")
            raise RuntimeError(f"VectorStore index rebuild failed: {str(e)}") from e

    def remove_paper(self, paper_id: Union[int, str]) -> bool:
        """
        Remove a paper from the FAISS vector store.

        :param paper_id: PostgreSQL ResearchPaper ID to remove.
        :return: True if paper was found and removed, False otherwise.
        """
        if paper_id is None or not self.contains_paper(paper_id):
            logger.info(f"Paper ID '{paper_id}' not found in VectorStore. No removal needed.")
            return False

        logger.info(f"Removing paper ID '{paper_id}' from VectorStore...")
        remaining_records: List[Tuple[Union[int, str], np.ndarray]] = []

        for i in range(self.index.ntotal):
            curr_id = self.get_paper_id(i)
            if curr_id is None or str(curr_id) == str(paper_id):
                continue
            vec = self.index.reconstruct(i)
            remaining_records.append((curr_id, vec))

        self.rebuild_index(remaining_records)
        logger.info(f"Successfully removed paper ID '{paper_id}'. Remaining vectors: {self.index.ntotal}.")
        return True

    def save_index(
        self,
        index_path: Optional[Union[str, Path]] = None,
        mapping_path: Optional[Union[str, Path]] = None
    ) -> None:
        """
        Persist the FAISS index and paper ID mapping JSON to disk.

        :param index_path: Optional path for index file (defaults to backend/app/vector_store/research_papers.index).
        :param mapping_path: Optional path for mapping JSON file (defaults to backend/app/vector_store/paper_id_mapping.json).
        """
        try:
            target_index = Path(index_path) if index_path else self.index_path
            target_mapping = Path(mapping_path) if mapping_path else self.mapping_path

            # Ensure parent directories exist
            target_index.parent.mkdir(parents=True, exist_ok=True)
            target_mapping.parent.mkdir(parents=True, exist_ok=True)

            # 1. Save FAISS binary index
            faiss.write_index(self.index, str(target_index))

            # 2. Save Paper ID Mapping JSON (IDs and positions only)
            pos_to_paper_json = {str(k): v for k, v in self.position_to_paper.items()}
            
            mapping_data = {
                "position_to_paper": pos_to_paper_json,
                "paper_to_position": self.paper_to_position
            }

            with open(target_mapping, "w", encoding="utf-8") as f:
                json.dump(mapping_data, f, ensure_ascii=False, indent=2)

            logger.info(
                f"Successfully saved FAISS index to '{target_index}' and mapping to '{target_mapping}'."
            )
        except Exception as e:
            logger.error(f"Failed to save FAISS index and mapping: {e}")
            raise RuntimeError(f"FAISS index/mapping save failed: {str(e)}") from e

    def load_index(
        self,
        index_path: Optional[Union[str, Path]] = None,
        mapping_path: Optional[Union[str, Path]] = None
    ) -> None:
        """
        Load FAISS index and paper ID mapping JSON from disk and verify synchronization.

        :param index_path: Optional path for index file (defaults to backend/app/vector_store/research_papers.index).
        :param mapping_path: Optional path for mapping JSON file (defaults to backend/app/vector_store/paper_id_mapping.json).
        """
        target_index = Path(index_path) if index_path else self.index_path
        target_mapping = Path(mapping_path) if mapping_path else self.mapping_path

        if not target_index.exists():
            logger.error(f"FAISS index file not found at '{target_index}'.")
            raise FileNotFoundError(f"FAISS index file not found at '{target_index}'.")

        if not target_mapping.exists():
            logger.error(f"Paper ID mapping file not found at '{target_mapping}'.")
            raise FileNotFoundError(f"Paper ID mapping file not found at '{target_mapping}'.")

        # 1. Read FAISS binary index
        try:
            loaded_index = faiss.read_index(str(target_index))
        except Exception as e:
            logger.error(f"Failed to parse binary FAISS index file '{target_index}': {e}")
            raise RuntimeError(f"FAISS index file at '{target_index}' is corrupted or unreadable.") from e

        if loaded_index.d != self.dimension:
            logger.error(f"Loaded FAISS index dimension mismatch! Expected {self.dimension}, got {loaded_index.d}.")
            raise ValueError(f"Loaded FAISS index dimension mismatch: expected {self.dimension}, got {loaded_index.d}.")

        # 2. Read Paper ID Mapping JSON
        try:
            with open(target_mapping, "r", encoding="utf-8") as f:
                mapping_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to parse paper ID mapping JSON file '{target_mapping}': {e}")
            raise RuntimeError(f"Paper ID mapping file at '{target_mapping}' is corrupted JSON.") from e

        raw_pos_to_paper = mapping_data.get("position_to_paper", {})
        raw_paper_to_pos = mapping_data.get("paper_to_position", {})

        pos_to_paper: Dict[int, Union[int, str]] = {int(k): v for k, v in raw_pos_to_paper.items()}
        paper_to_pos: Dict[str, int] = {str(k): int(v) for k, v in raw_paper_to_pos.items()}

        # 3. Synchronize verification: FAISS index size MUST equal number of mapped vectors
        if loaded_index.ntotal != len(pos_to_paper) or loaded_index.ntotal != len(paper_to_pos):
            logger.error(
                f"VectorStore desynchronization error: FAISS index size ({loaded_index.ntotal}) != mapping count ({len(pos_to_paper)})."
            )
            raise RuntimeError(
                f"VectorStore state inconsistent: FAISS index size ({loaded_index.ntotal}) does not match paper ID mapping count ({len(pos_to_paper)})."
            )

        self.index = loaded_index
        self.position_to_paper = pos_to_paper
        self.paper_to_position = paper_to_pos

        logger.info(
            f"Successfully loaded VectorStore from '{target_index}' and '{target_mapping}' (Total synchronized vectors: {self.index.ntotal})."
        )
