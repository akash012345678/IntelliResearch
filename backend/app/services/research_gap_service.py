import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import numpy as np

from app.services.knowledge_graph_service import KnowledgeGraphService
from app.services.knowledge_graph_builder import KnowledgeGraphBuilder
from app.services.link_prediction_service import LinkPredictionService
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class ResearchGapService:
    """
    Service responsible for analyzing link prediction candidates using multi-signal evidence evaluation
    (link prediction strength, cross-paper support, SBERT semantic evidence, underrepresentation)
    and generating ranked potential research gaps.
    """

    def __init__(
        self,
        graph_service: Optional[KnowledgeGraphService] = None,
        link_prediction_service: Optional[LinkPredictionService] = None,
        embedding_service: Optional[EmbeddingService] = None
    ):
        self.graph_service = graph_service or KnowledgeGraphService()
        self.link_prediction_service = link_prediction_service or LinkPredictionService(graph_service=self.graph_service)
        self.embedding_service = embedding_service or EmbeddingService()

    @staticmethod
    def compute_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two float vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        v1 = np.array(vec1, dtype=np.float32)
        v2 = np.array(vec2, dtype=np.float32)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (norm1 * norm2))

    def detect_gaps(self, db_session: Session, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Evaluate candidate relationships and return top_k potential research gaps.
        Does NOT mutate graph state or database records.
        """
        if db_session is None or not hasattr(db_session, "query"):
            logger.error("Invalid database session provided to detect_gaps.")
            raise ValueError("A valid database session must be provided.")

        builder = KnowledgeGraphBuilder(graph_service=self.graph_service)
        builder.build_from_database(db_session)
        graph = self.graph_service.get_graph()

        if graph is None or graph.number_of_nodes() == 0:
            logger.info("Knowledge Graph is empty. Returning 0 research gaps.")
            return []

        # 1. Obtain candidate link predictions
        link_candidates = self.link_prediction_service.predict_links(graph=graph, top_k=100)
        if not link_candidates:
            logger.info("No candidate link predictions generated. Returning 0 research gaps.")
            return []

        from app.models.paper_model import ResearchPaper
        all_papers = db_session.query(ResearchPaper).all()
        paper_map = {p.id: p for p in all_papers}
        total_papers = max(1, len(all_papers))

        undirected_graph = graph.to_undirected()
        gap_results = []

        for candidate in link_candidates:
            source_p_id = candidate["source_paper_id"]
            target_node_id = candidate["target_node_id"]
            target_label = candidate["target_label"]
            target_type = candidate["target_type"]
            rel_type = candidate["relationship_type"]
            link_score = candidate["scores"]["combined"]

            source_paper = paper_map.get(source_p_id)
            source_title = source_paper.title if source_paper else f"Paper {source_p_id}"

            # Signal B: Cross-Paper Support
            target_papers = set(undirected_graph.neighbors(target_node_id)) if target_node_id in undirected_graph else set()
            source_neighbors = set(undirected_graph.neighbors(f"paper_{source_p_id}")) if f"paper_{source_p_id}" in undirected_graph else set()

            # Papers related to source_paper (papers sharing at least 1 concept with source paper)
            related_papers = set()
            for c_node in source_neighbors:
                for p_node in undirected_graph.neighbors(c_node):
                    if p_node.startswith("paper_") and p_node != f"paper_{source_p_id}":
                        related_papers.add(p_node)

            if related_papers:
                supporting_papers = related_papers.intersection(target_papers)
                cross_paper_support = round(len(supporting_papers) / len(related_papers), 4)
            else:
                cross_paper_support = 0.0

            # Signal C: Semantic Evidence using Sentence-BERT
            semantic_evidence = 0.0
            if source_paper and target_papers:
                try:
                    source_text = f"{source_paper.title}. {source_paper.abstract or ''}"
                    source_emb = self.embedding_service.generate_embedding(source_text)

                    target_embs = []
                    for tp_node in target_papers:
                        tp_num_id = graph.nodes[tp_node].get("paper_id")
                        if tp_num_id and tp_num_id in paper_map:
                            tp_obj = paper_map[tp_num_id]
                            tp_text = f"{tp_obj.title}. {tp_obj.abstract or ''}"
                            target_embs.append(self.embedding_service.generate_embedding(tp_text))

                    if target_embs:
                        sims = [self.compute_similarity(source_emb, te) for te in target_embs]
                        semantic_evidence = round(float(np.max(sims)), 4)
                except Exception as e:
                    logger.warning(f"Failed to calculate semantic evidence: {e}")
                    semantic_evidence = 0.0

            # Signal E: Underrepresentation Score
            paper_count = len(target_papers)
            underrepresentation_score = round(max(0.0, 1.0 - (paper_count / total_papers)), 4)

            # Combined gap score formula
            gap_score = round(
                0.35 * link_score +
                0.25 * cross_paper_support +
                0.25 * semantic_evidence +
                0.15 * underrepresentation_score,
                4
            )

            # Minimum Evidence Rule: Must have at least TWO active signals (> 0.1)
            active_signals = sum([
                1 if link_score > 0.1 else 0,
                1 if cross_paper_support > 0.1 else 0,
                1 if semantic_evidence > 0.1 else 0,
                1 if underrepresentation_score > 0.1 else 0
            ])

            if active_signals < 2:
                continue

            # Confidence Level Mapping
            if gap_score >= 0.75:
                confidence = "High"
            elif gap_score >= 0.50:
                confidence = "Moderate"
            else:
                confidence = "Low"

            # Explanations Generation
            explanations = []
            if link_score >= 0.5:
                explanations.append("The predicted relationship has strong graph-based structural support.")
            if cross_paper_support > 0.0:
                explanations.append("The target concept appears in related research papers within the collection.")
            if semantic_evidence >= 0.5:
                explanations.append("Semantic similarity indicates high relevance between the source paper and research using this concept.")
            if underrepresentation_score >= 0.5:
                explanations.append("The specific paper-concept combination is currently underrepresented in the collection.")

            if not explanations:
                explanations.append("Moderate structural and collection-level evidence supports this potential research gap.")

            gap_results.append({
                "source_paper_id": source_p_id,
                "source_paper_title": source_title,
                "target_node_id": target_node_id,
                "target_type": target_type,
                "target_label": target_label,
                "relationship_type": rel_type,
                "gap_score": gap_score,
                "confidence": confidence,
                "evidence": {
                    "link_prediction_score": round(link_score, 4),
                    "cross_paper_support": cross_paper_support,
                    "semantic_evidence": semantic_evidence,
                    "underrepresentation_score": underrepresentation_score
                },
                "explanation": explanations
            })

        # Rank gaps: gap_score DESC, target_type ASC, target_label ASC, source_paper_id ASC
        gap_results.sort(
            key=lambda x: (
                -x["gap_score"],
                x["target_type"],
                x["target_label"],
                str(x["source_paper_id"])
            )
        )

        return gap_results[:top_k]
