import math
import logging
from typing import Dict, Any, List, Optional
import networkx as nx

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

RELATIONSHIP_TYPE_MAP = {
    NODE_TYPE_ALGORITHM: "USES_ALGORITHM",
    NODE_TYPE_DATASET: "USES_DATASET",
    NODE_TYPE_METHODOLOGY: "USES_METHODOLOGY",
    NODE_TYPE_DOMAIN: "HAS_DOMAIN",
    NODE_TYPE_KEYWORD: "HAS_KEYWORD"
}


class LinkPredictionService:
    """
    Deterministic Graph-Based Link Prediction Engine using Jaccard Coefficient,
    Adamic-Adar Index, and Resource Allocation Index for bipartite research graph nodes.
    """

    def __init__(self, graph_service: Optional[KnowledgeGraphService] = None):
        self.graph_service = graph_service or KnowledgeGraphService()

    def predict_links(self, graph: Optional[nx.DiGraph] = None, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Generate candidate paper-concept links and compute structural similarity scores.
        Does NOT mutate the input graph.
        """
        target_graph = graph if graph is not None else self.graph_service.get_graph()

        if target_graph is None or target_graph.number_of_nodes() == 0:
            logger.info("Graph is empty. Returning 0 link predictions.")
            return []

        # Create undirected view for neighbor calculations without mutating graph
        undirected_graph = target_graph.to_undirected()

        paper_nodes = []
        concept_nodes = []

        for node_id, attrs in target_graph.nodes(data=True):
            n_type = attrs.get("type")
            if n_type == NODE_TYPE_PAPER:
                paper_nodes.append((node_id, attrs))
            elif n_type in RELATIONSHIP_TYPE_MAP:
                concept_nodes.append((node_id, attrs))

        if not paper_nodes or not concept_nodes:
            logger.info("Insufficient paper or concept nodes to form candidate pairs.")
            return []

        candidates = []

        for p_id, p_attrs in paper_nodes:
            paper_num_id = p_attrs.get("paper_id")
            p_concepts = set(undirected_graph.neighbors(p_id))

            for c_id, c_attrs in concept_nodes:
                # Exclude existing edges and self links
                if c_id in p_concepts or p_id == c_id:
                    continue

                c_type = c_attrs.get("type")
                c_label = c_attrs.get("label", c_id)
                rel_type = RELATIONSHIP_TYPE_MAP.get(c_type, "RELATED_TO")

                # Papers currently connected to concept c_id
                c_papers = set(undirected_graph.neighbors(c_id))
                if not c_papers:
                    continue

                # Find all shared concept nodes between paper p_id and any paper in c_papers
                shared_concepts = set()
                max_jaccard = 0.0

                for other_p in c_papers:
                    if other_p == p_id:
                        continue

                    other_concepts = set(undirected_graph.neighbors(other_p))
                    common = p_concepts.intersection(other_concepts)
                    union = p_concepts.union(other_concepts)

                    if union:
                        j_val = len(common) / len(union)
                        if j_val > max_jaccard:
                            max_jaccard = j_val

                    shared_concepts.update(common)

                # 1. Jaccard Score
                jaccard = max_jaccard

                # 2. Adamic-Adar Index
                adamic_adar = 0.0
                for z in shared_concepts:
                    deg = undirected_graph.degree(z)
                    if deg > 1:
                        adamic_adar += 1.0 / math.log(deg)

                # 3. Resource Allocation Index
                resource_alloc = 0.0
                for z in shared_concepts:
                    deg = undirected_graph.degree(z)
                    if deg > 0:
                        resource_alloc += 1.0 / deg

                # Normalized combined score in [0.0, 1.0]
                aa_norm = 1.0 - math.exp(-adamic_adar)
                ra_norm = 1.0 - math.exp(-resource_alloc)
                combined = round(0.30 * jaccard + 0.35 * aa_norm + 0.35 * ra_norm, 4)

                candidates.append({
                    "source_paper_id": paper_num_id if paper_num_id is not None else p_id,
                    "target_node_id": c_id,
                    "target_type": c_type,
                    "target_label": c_label,
                    "relationship_type": rel_type,
                    "existing_relationship": False,
                    "scores": {
                        "jaccard": round(jaccard, 4),
                        "adamic_adar": round(adamic_adar, 4),
                        "resource_allocation": round(resource_alloc, 4),
                        "combined": combined
                    }
                })

        # Rank candidates: combined DESC, then target_type ASC, target_label ASC, source_paper_id ASC
        candidates.sort(
            key=lambda x: (
                -x["scores"]["combined"],
                x["target_type"],
                x["target_label"],
                str(x["source_paper_id"])
            )
        )

        return candidates[:top_k]
