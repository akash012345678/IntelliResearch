import logging
from typing import List, Dict, Any, Optional, Union
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)


class SemanticIndexService:
    """
    Coordinator service responsible for generating semantic embeddings via EmbeddingService
    and indexing/managing vectors in FAISS VectorStore.
    """

    def __init__(self, vector_store: Optional[VectorStore] = None):
        """
        Initialize SemanticIndexService.

        :param vector_store: Optional instance of VectorStore. Uses default instance if None.
        """
        self.vector_store: VectorStore = vector_store if vector_store is not None else VectorStore()

    def _extract_paper_fields(self, paper: Any) -> Dict[str, Any]:
        """Extract standardized fields from either a dict or object instance."""
        if isinstance(paper, dict):
            paper_id = paper.get("id") if "id" in paper else paper.get("paper_id")
            title = paper.get("title", "")
            abstract = paper.get("abstract")
            full_text = paper.get("full_text") or paper.get("content")
            keywords = paper.get("keywords")
            metadata = paper.get("metadata") or paper.get("extracted_metadata")
        else:
            paper_id = getattr(paper, "id", None) if hasattr(paper, "id") else getattr(paper, "paper_id", None)
            title = getattr(paper, "title", "")
            abstract = getattr(paper, "abstract", None)
            full_text = getattr(paper, "full_text", None) or getattr(paper, "content", None)
            keywords = getattr(paper, "keywords", None)
            metadata = getattr(paper, "metadata", None) or getattr(paper, "extracted_metadata", None)

        return {
            "paper_id": paper_id,
            "title": title,
            "abstract": abstract,
            "full_text": full_text,
            "keywords": keywords,
            "metadata": metadata if isinstance(metadata, dict) else {}
        }

    def index_paper(self, paper: Any) -> int:
        """
        Extract paper details, generate Sentence-BERT 384-d embedding, and store in FAISS VectorStore.

        :param paper: ResearchPaper instance or dictionary containing paper data.
        :return: FAISS position index assigned to the paper.
        """
        fields = self._extract_paper_fields(paper)
        paper_id = fields["paper_id"]

        if paper_id is None or (isinstance(paper_id, str) and not paper_id.strip()):
            logger.error("Cannot index paper: missing or invalid paper_id.")
            raise ValueError("Cannot index paper: missing or invalid paper_id.")

        # Check duplicate indexing
        if self.vector_store.contains_paper(paper_id):
            logger.info(f"Paper ID '{paper_id}' is already indexed in VectorStore. Skipping duplicate indexing.")
            raise ValueError(f"Paper ID '{paper_id}' is already indexed in VectorStore.")

        logger.info(f"Generating semantic embedding for paper ID '{paper_id}' ('{fields['title']}')...")

        # Generate 384-d embedding using existing EmbeddingService
        embedding = EmbeddingService.generate_paper_embedding(
            title=fields["title"],
            abstract=fields["abstract"],
            full_text=fields["full_text"],
            keywords=fields["keywords"],
            metadata=fields["metadata"]
        )

        # Store in FAISS VectorStore with paper_id
        assigned_pos = self.vector_store.add_paper(
            paper_id=paper_id,
            embedding=embedding
        )

        # Save index and mapping to disk
        self.vector_store.save_index()

        logger.info(f"Successfully indexed paper ID '{paper_id}' at FAISS position {assigned_pos}.")
        return assigned_pos

    def remove_paper(self, paper_id: Union[int, str]) -> bool:
        """
        Remove a paper from the vector store and update disk files.

        :param paper_id: PostgreSQL ResearchPaper ID.
        :return: True if paper was found and removed, False otherwise.
        """
        return self.vector_store.remove_paper(paper_id)

    def rebuild_index(
        self,
        papers: Optional[List[Any]] = None,
        db_session: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Rebuild the FAISS vector store index for a list of papers or database records.

        If a single paper fails embedding generation:
        - Logs the failure.
        - Continues processing remaining papers.
        - Reports indexed and failed counts.

        :param papers: Optional list of ResearchPaper objects or dicts.
        :param db_session: Optional SQLAlchemy DB session to query ResearchPaper records.
        :return: Structured result dictionary:
                 {
                     "total": N,
                     "indexed": X,
                     "failed": Y,
                     "failed_paper_ids": [...]
                 }
        """
        logger.info("Initiating full semantic index rebuild...")

        paper_list: List[Any] = []
        if papers is not None:
            paper_list = list(papers)
        elif db_session is not None:
            try:
                # Retrieve all existing ResearchPaper records from DB
                from sqlalchemy.orm import Query
                # Query dynamically if ResearchPaper model exists
                model_cls = getattr(db_session, "ResearchPaper", None)
                if hasattr(db_session, "query"):
                    if model_cls:
                        paper_list = db_session.query(model_cls).all()
                    else:
                        # Fallback query
                        paper_list = db_session.query().all()
            except Exception as e:
                logger.error(f"Failed to query papers from database session during rebuild: {e}")
                paper_list = []

        total_count = len(paper_list)
        valid_records: List[Dict[str, Any]] = []
        failed_paper_ids: List[Union[int, str]] = []

        for paper in paper_list:
            fields = self._extract_paper_fields(paper)
            p_id = fields["paper_id"]

            if p_id is None or (isinstance(p_id, str) and not p_id.strip()):
                logger.warning("Skipping paper record with missing or empty paper_id during rebuild.")
                continue

            try:
                # Generate embedding using existing EmbeddingService
                embedding = EmbeddingService.generate_paper_embedding(
                    title=fields["title"],
                    abstract=fields["abstract"],
                    full_text=fields["full_text"],
                    keywords=fields["keywords"],
                    metadata=fields["metadata"]
                )
                valid_records.append({
                    "paper_id": p_id,
                    "embedding": embedding
                })
            except Exception as e:
                logger.error(f"Failed to generate embedding for paper ID '{p_id}' during rebuild: {e}")
                failed_paper_ids.append(p_id)

        # Atomic rebuild of VectorStore with valid paper records
        self.vector_store.rebuild_index(valid_records)

        result_summary = {
            "total": total_count,
            "indexed": len(valid_records),
            "failed": len(failed_paper_ids),
            "failed_paper_ids": failed_paper_ids
        }

        logger.info(
            f"Semantic index rebuild complete. Total: {total_count}, Indexed: {len(valid_records)}, Failed: {len(failed_paper_ids)}."
        )
        return result_summary

    def search_papers(
        self,
        query: str,
        top_k: int = 5,
        db_session: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Execute semantic similarity search for a text query:
        1. Generate 384-d normalized SBERT embedding via EmbeddingService.
        2. Search FAISS index via VectorStore.search(query_embedding, top_k).
        3. Retrieve paper details from database by paper IDs.
        4. Format ranked response list preserving FAISS similarity ranking order.
        """
        clean_query = query.strip() if query else ""
        if not clean_query:
            logger.error("Empty query passed to search_papers.")
            raise ValueError("Search query cannot be empty or whitespace-only.")

        if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0:
            logger.error(f"Invalid top_k parameter '{top_k}'.")
            raise ValueError("top_k must be a positive integer.")

        if top_k > 20:
            logger.error(f"top_k parameter '{top_k}' exceeds maximum limit of 20.")
            raise ValueError("top_k cannot exceed maximum limit of 20.")

        logger.info(f"Executing semantic search for query: '{clean_query[:50]}...' with top_k={top_k}")

        # 1. Generate Query Embedding
        query_embedding = EmbeddingService.generate_embedding(clean_query)

        # 2. Search FAISS VectorStore
        search_hits = self.vector_store.search(query_embedding, top_k=top_k)

        if not search_hits:
            logger.info("Semantic search returned 0 FAISS matches.")
            return {
                "query": clean_query,
                "total_results": 0,
                "results": []
            }

        # 3. Retrieve Paper Records from Database
        paper_ids = [hit["paper_id"] for hit in search_hits]
        paper_map = {}

        if db_session is not None and hasattr(db_session, "query"):
            try:
                from app.models.paper_model import ResearchPaper
                db_papers = db_session.query(ResearchPaper).filter(ResearchPaper.id.in_(paper_ids)).all()
                for p in db_papers:
                    paper_map[p.id] = p
                    paper_map[str(p.id)] = p
            except Exception as e:
                logger.error(f"Failed to query database for paper IDs {paper_ids}: {e}")
                raise RuntimeError(f"Database query failed during semantic search: {e}") from e

        # 4. Construct Results maintaining EXACT FAISS Similarity Ranking Order
        results = []
        for hit in search_hits:
            p_id = hit["paper_id"]
            score = float(hit["similarity_score"])

            paper_obj = paper_map.get(p_id)
            if not paper_obj and isinstance(p_id, str) and p_id.isdigit():
                paper_obj = paper_map.get(int(p_id))

            if not paper_obj:
                logger.warning(
                    f"Paper ID '{p_id}' returned by FAISS vector search was not found in database. Skipping."
                )
                continue

            results.append({
                "paper_id": paper_obj.id,
                "title": paper_obj.title,
                "abstract": paper_obj.abstract,
                "keywords": getattr(paper_obj, "keywords", []) or [],
                "algorithms": getattr(paper_obj, "algorithms", []) or [],
                "datasets": getattr(paper_obj, "datasets", []) or [],
                "methodologies": getattr(paper_obj, "methodologies", []) or [],
                "application_domains": getattr(paper_obj, "application_domains", []) or [],
                "similarity_score": round(score, 4)
            })

        logger.info(f"Semantic search complete. Returning {len(results)} ranked paper results.")
        return {
            "query": clean_query,
            "total_results": len(results),
            "results": results
        }

    def find_related_papers(
        self,
        paper_id: Union[int, str],
        top_k: int = 5,
        db_session: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Find semantically similar research papers for a selected source paper:
        1. Validate source paper exists in database (raise KeyError -> 404 if missing).
        2. Retrieve or generate source paper vector embedding.
        3. Perform FAISS vector search for top_k + 1 nearest neighbors.
        4. Exclude source paper itself from results.
        5. Retrieve metadata from Supabase PostgreSQL by paper IDs.
        6. Format response list preserving FAISS similarity ranking order.
        """
        if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0:
            logger.error(f"Invalid top_k parameter '{top_k}'.")
            raise ValueError("top_k must be a positive integer.")

        if top_k > 20:
            logger.error(f"top_k parameter '{top_k}' exceeds maximum limit of 20.")
            raise ValueError("top_k cannot exceed maximum limit of 20.")

        # Step 1: Validate paper exists in Database
        source_paper_obj = None
        if db_session is not None and hasattr(db_session, "query"):
            try:
                from app.models.paper_model import ResearchPaper
                source_paper_obj = db_session.query(ResearchPaper).filter(ResearchPaper.id == paper_id).first()
            except Exception as e:
                logger.error(f"Failed to query database for paper ID {paper_id}: {e}")
                raise RuntimeError(f"Database query failed: {e}") from e

        if not source_paper_obj:
            logger.warning(f"Related papers target paper_id '{paper_id}' not found in database.")
            raise KeyError(f"Research paper with ID {paper_id} does not exist.")

        logger.info(f"Finding related papers for source paper ID {paper_id} ('{source_paper_obj.title[:30]}...'), top_k={top_k}")

        # Step 2: Retrieve source paper vector
        paper_vector = None
        pos = self.vector_store.get_vector_position(paper_id)
        if pos is not None and pos >= 0 and pos < self.vector_store.index.ntotal:
            try:
                # Reconstruct vector directly from FAISS index
                raw_vec = self.vector_store.index.reconstruct(pos)
                paper_vector = raw_vec.tolist()
            except Exception as e:
                logger.warning(f"Could not reconstruct vector for paper ID {paper_id} at position {pos}: {e}")

        if paper_vector is None:
            # Generate embedding on the fly from paper fields
            fields = self._extract_paper_fields(source_paper_obj)
            paper_vector = EmbeddingService.generate_paper_embedding(
                title=fields["title"],
                abstract=fields["abstract"],
                full_text=fields["full_text"],
                keywords=fields["keywords"],
                metadata=fields["metadata"]
            )

        # Step 3: Search FAISS for top_k + 1 nearest neighbors (to account for self-match)
        search_k = top_k + 1
        search_hits = self.vector_store.search(paper_vector, top_k=search_k)

        # Step 4: Exclude source paper itself from hits
        filtered_hits = []
        for hit in search_hits:
            hit_id = str(hit["paper_id"])
            src_id = str(paper_id)
            if hit_id == src_id:
                continue
            filtered_hits.append(hit)
            if len(filtered_hits) >= top_k:
                break

        if not filtered_hits:
            logger.info(f"No related paper hits found in FAISS for paper ID {paper_id}.")
            return {
                "source_paper": {
                    "paper_id": source_paper_obj.id,
                    "title": source_paper_obj.title
                },
                "total_results": 0,
                "related_papers": []
            }

        # Step 5: Retrieve metadata for related paper IDs from Database
        related_ids = [hit["paper_id"] for hit in filtered_hits]
        paper_map = {}

        if db_session is not None and hasattr(db_session, "query"):
            try:
                from app.models.paper_model import ResearchPaper
                db_papers = db_session.query(ResearchPaper).filter(ResearchPaper.id.in_(related_ids)).all()
                for p in db_papers:
                    paper_map[p.id] = p
                    paper_map[str(p.id)] = p
            except Exception as e:
                logger.error(f"Failed to query database for related paper IDs {related_ids}: {e}")
                raise RuntimeError(f"Database query failed during related papers search: {e}") from e

        # Step 6: Construct results maintaining EXACT FAISS Similarity Order
        related_results = []
        for hit in filtered_hits:
            p_id = hit["paper_id"]
            score = float(hit["similarity_score"])

            paper_obj = paper_map.get(p_id)
            if not paper_obj and isinstance(p_id, str) and p_id.isdigit():
                paper_obj = paper_map.get(int(p_id))

            if not paper_obj:
                logger.warning(
                    f"Related paper ID '{p_id}' returned by FAISS vector search was not found in database. Skipping."
                )
                continue

            related_results.append({
                "paper_id": paper_obj.id,
                "title": paper_obj.title,
                "abstract": paper_obj.abstract,
                "keywords": getattr(paper_obj, "keywords", []) or [],
                "algorithms": getattr(paper_obj, "algorithms", []) or [],
                "datasets": getattr(paper_obj, "datasets", []) or [],
                "methodologies": getattr(paper_obj, "methodologies", []) or [],
                "application_domains": getattr(paper_obj, "application_domains", []) or [],
                "similarity_score": round(score, 4)
            })

        logger.info(f"Related papers search complete for ID {paper_id}. Returning {len(related_results)} related papers.")
        return {
            "source_paper": {
                "paper_id": source_paper_obj.id,
                "title": source_paper_obj.title
            },
            "total_results": len(related_results),
            "related_papers": related_results
        }


