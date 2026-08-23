import logging
import networkx as nx
from typing import List, Dict, Any, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# Node Type Constants
NODE_TYPE_PAPER = "PAPER"
NODE_TYPE_KEYWORD = "KEYWORD"
NODE_TYPE_ALGORITHM = "ALGORITHM"
NODE_TYPE_DATASET = "DATASET"
NODE_TYPE_METHODOLOGY = "METHODOLOGY"
NODE_TYPE_DOMAIN = "DOMAIN"

# Relationship Type Constants
REL_HAS_KEYWORD = "HAS_KEYWORD"
REL_USES_ALGORITHM = "USES_ALGORITHM"
REL_USES_DATASET = "USES_DATASET"
REL_USES_METHODOLOGY = "USES_METHODOLOGY"
REL_HAS_DOMAIN = "HAS_DOMAIN"


def normalize_entity(name: str) -> Tuple[str, str]:
    """
    Normalize entity strings:
    - Trims whitespace.
    - Ignores empty/whitespace-only values.
    - Generates a case-insensitive key for lookup/deduplication.
    - Preserves clean original display label.
    - Preserves distinctness of technical entities (e.g. YOLO vs YOLOv5 vs YOLOv8).
    """
    if not name or not isinstance(name, str):
        return "", ""
    trimmed = name.strip()
    if not trimmed:
        return "", ""
    cleaned_label = " ".join(trimmed.split())
    normalized_key = cleaned_label.lower()
    return normalized_key, cleaned_label


class KnowledgeGraphService:
    """
    In-memory Knowledge Graph Service using NetworkX.
    Constructs and analyzes relationships between research papers and extracted research concepts.
    """

    def __init__(self):
        self.graph = nx.DiGraph()

    def clear_graph(self) -> None:
        """Clear all nodes and edges from the Knowledge Graph."""
        self.graph.clear()
        logger.info("Knowledge Graph cleared.")

    def get_graph(self) -> nx.DiGraph:
        """Return the underlying NetworkX DiGraph instance."""
        return self.graph

    def _get_entity_node_id(self, entity_type: str, norm_key: str) -> str:
        """Generate deterministic node ID for entity types."""
        prefix = entity_type.lower()
        return f"{prefix}_{norm_key}"

    def add_paper_node(self, paper_id: Union[int, str], title: str) -> str:
        """
        Add or retrieve a PAPER node.
        PAPER node format:
        {
            "id": "paper_{paper_id}",
            "type": "PAPER",
            "label": "Paper Title",
            "paper_id": paper_id
        }
        """
        node_id = f"paper_{paper_id}"
        if not self.graph.has_node(node_id):
            self.graph.add_node(
                node_id,
                id=node_id,
                type=NODE_TYPE_PAPER,
                label=title or f"Paper {paper_id}",
                paper_id=paper_id
            )
        return node_id

    def add_entity(self, entity_type: str, raw_name: str) -> Optional[str]:
        """
        Normalize and add an entity node if valid.
        Returns node_id if added/exists, None if name is invalid/empty.
        """
        norm_key, display_label = normalize_entity(raw_name)
        if not norm_key:
            return None

        node_id = self._get_entity_node_id(entity_type, norm_key)
        if not self.graph.has_node(node_id):
            self.graph.add_node(
                node_id,
                id=node_id,
                type=entity_type,
                label=display_label
            )
        return node_id

    def add_relationship(self, source_id: str, target_id: str, relation: str) -> bool:
        """
        Add a directed edge between source and target nodes with relationship attribute.
        Prevents duplicate edges.
        """
        if not self.graph.has_node(source_id) or not self.graph.has_node(target_id):
            logger.warning(f"Cannot add edge {source_id} -> {target_id}: node missing.")
            return False

        if not self.graph.has_edge(source_id, target_id):
            self.graph.add_edge(source_id, target_id, relation=relation)
            return True
        return False

    def add_paper(self, paper: Any) -> str:
        """
        Extract concepts from a ResearchPaper object or dictionary and add nodes + edges.
        """
        if isinstance(paper, dict):
            p_id = paper.get("id")
            title = paper.get("title", "")
            keywords = paper.get("keywords", []) or []
            algorithms = paper.get("algorithms", []) or []
            datasets = paper.get("datasets", []) or []
            methodologies = paper.get("methodologies", []) or []
            application_domains = paper.get("application_domains", []) or []
        else:
            p_id = getattr(paper, "id", None)
            title = getattr(paper, "title", "")
            keywords = getattr(paper, "keywords", []) or []
            algorithms = getattr(paper, "algorithms", []) or []
            datasets = getattr(paper, "datasets", []) or []
            methodologies = getattr(paper, "methodologies", []) or []
            application_domains = getattr(paper, "application_domains", []) or []

        if p_id is None:
            raise ValueError("ResearchPaper record must contain an 'id'.")

        paper_node_id = self.add_paper_node(paper_id=p_id, title=title)

        entity_mappings = [
            (NODE_TYPE_KEYWORD, REL_HAS_KEYWORD, keywords),
            (NODE_TYPE_ALGORITHM, REL_USES_ALGORITHM, algorithms),
            (NODE_TYPE_DATASET, REL_USES_DATASET, datasets),
            (NODE_TYPE_METHODOLOGY, REL_USES_METHODOLOGY, methodologies),
            (NODE_TYPE_DOMAIN, REL_HAS_DOMAIN, application_domains),
        ]

        for entity_type, relation, items in entity_mappings:
            if not items:
                continue
            for item in items:
                entity_node_id = self.add_entity(entity_type, item)
                if entity_node_id:
                    self.add_relationship(paper_node_id, entity_node_id, relation)

        return paper_node_id

    def build_graph(self, papers: List[Any]) -> Dict[str, Any]:
        """
        Construct/rebuild the Knowledge Graph from a list of ResearchPaper records.
        """
        self.clear_graph()
        indexed_count = 0
        for paper in papers:
            try:
                self.add_paper(paper)
                indexed_count += 1
            except Exception as e:
                logger.error(f"Error adding paper to Knowledge Graph: {e}")

        stats = self.get_statistics()
        logger.info(f"Knowledge Graph built successfully for {indexed_count} papers. Stats: {stats}")
        return stats

    def get_statistics(self) -> Dict[str, int]:
        """
        Calculate dynamic Knowledge Graph statistics from NetworkX graph.
        Returns:
        {
            "total_nodes": int,
            "total_edges": int,
            "paper_nodes": int,
            "keyword_nodes": int,
            "algorithm_nodes": int,
            "dataset_nodes": int,
            "methodology_nodes": int,
            "domain_nodes": int
        }
        """
        stats = {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "paper_nodes": 0,
            "keyword_nodes": 0,
            "algorithm_nodes": 0,
            "dataset_nodes": 0,
            "methodology_nodes": 0,
            "domain_nodes": 0,
        }

        type_map = {
            NODE_TYPE_PAPER: "paper_nodes",
            NODE_TYPE_KEYWORD: "keyword_nodes",
            NODE_TYPE_ALGORITHM: "algorithm_nodes",
            NODE_TYPE_DATASET: "dataset_nodes",
            NODE_TYPE_METHODOLOGY: "methodology_nodes",
            NODE_TYPE_DOMAIN: "domain_nodes",
        }

        for _, attrs in self.graph.nodes(data=True):
            n_type = attrs.get("type")
            if n_type in type_map:
                stats[type_map[n_type]] += 1

        return stats
