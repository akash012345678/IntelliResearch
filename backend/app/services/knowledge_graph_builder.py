import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.services.knowledge_graph_service import (
    KnowledgeGraphService,
    NODE_TYPE_PAPER,
    NODE_TYPE_KEYWORD,
    NODE_TYPE_ALGORITHM,
    NODE_TYPE_DATASET,
    NODE_TYPE_METHODOLOGY,
    NODE_TYPE_DOMAIN
)

logger = logging.getLogger(__name__)


class KnowledgeGraphBuilder:
    """
    Service responsible for fetching ResearchPaper records from Supabase PostgreSQL,
    delegating construction to KnowledgeGraphService, and calculating top shared entities.
    """

    def __init__(self, graph_service: Optional[KnowledgeGraphService] = None):
        self.graph_service = graph_service or KnowledgeGraphService()

    def build_from_database(self, db_session: Session) -> Dict[str, Any]:
        """
        Fetch ResearchPaper records from active database session and build in-memory NetworkX Knowledge Graph.
        """
        if db_session is None or not hasattr(db_session, "query"):
            logger.error("Invalid database session provided to build_from_database.")
            raise ValueError("A valid database session must be provided.")

        try:
            from app.models.paper_model import ResearchPaper
            papers = db_session.query(ResearchPaper).all()
        except Exception as e:
            logger.error(f"Failed to query ResearchPaper records from database: {e}")
            raise RuntimeError(f"Database query failed during Knowledge Graph construction: {e}") from e

        total_papers = len(papers)
        if total_papers == 0:
            logger.info("Database returned 0 ResearchPaper records. Returning empty Knowledge Graph stats.")
            self.graph_service.clear_graph()
            empty_stats = self.graph_service.get_statistics()
            return {
                "total_papers": 0,
                **empty_stats,
                "top_entities": {
                    "top_algorithms": [],
                    "top_datasets": [],
                    "top_methodologies": [],
                    "top_domains": [],
                    "top_keywords": []
                }
            }

        # Clear prior graph and construct graph from paper records
        stats = self.graph_service.build_graph(papers)
        top_entities = self.get_top_entities(top_k=5)

        result = {
            "total_papers": total_papers,
            **stats,
            "top_entities": top_entities
        }

        logger.info(
            f"Knowledge Graph construction complete. Papers: {total_papers}, "
            f"Nodes: {stats['total_nodes']}, Edges: {stats['total_edges']}"
        )
        return result

    def get_top_entities(self, top_k: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """
        Calculate top shared research concepts based on NetworkX in-degree (number of connected papers).
        """
        graph = self.graph_service.get_graph()
        node_type_mapping = [
            ("top_algorithms", NODE_TYPE_ALGORITHM),
            ("top_datasets", NODE_TYPE_DATASET),
            ("top_methodologies", NODE_TYPE_METHODOLOGY),
            ("top_domains", NODE_TYPE_DOMAIN),
            ("top_keywords", NODE_TYPE_KEYWORD),
        ]

        results = {}
        for key, n_type in node_type_mapping:
            type_nodes = [
                (node_id, attrs.get("label", node_id), graph.in_degree(node_id))
                for node_id, attrs in graph.nodes(data=True)
                if attrs.get("type") == n_type
            ]
            # Sort by in_degree descending
            type_nodes.sort(key=lambda x: x[2], reverse=True)

            results[key] = [
                {
                    "label": label,
                    "paper_count": count
                }
                for _, label, count in type_nodes[:top_k]
            ]

        return results
