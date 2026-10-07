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

    def add_entity(
        self,
        entity_type: str,
        raw_name: str,
        role: Optional[str] = None,
        evidence_text: Optional[str] = None,
        confidence: Optional[float] = None
    ) -> Optional[str]:
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
                label=display_label,
                role=role or "GENERAL",
                evidence_text=evidence_text or "",
                confidence=confidence if confidence is not None else 1.0
            )
        else:
            if role and role in ["EXPERIMENTAL_DATASET", "PRIMARY_DOMAIN", "PROPOSED_MODEL"]:
                self.graph.nodes[node_id]["role"] = role
            if evidence_text and not self.graph.nodes[node_id].get("evidence_text"):
                self.graph.nodes[node_id]["evidence_text"] = evidence_text

        return node_id

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relation: str,
        role: Optional[str] = None,
        evidence_text: Optional[str] = None,
        confidence: Optional[float] = None,
        section: Optional[str] = None
    ) -> bool:
        """
        Add a directed edge between source and target nodes with relationship attribute.
        Prevents duplicate edges and strictly excludes self-relationships (source_id == target_id).
        """
        if source_id == target_id:
            logger.warning(f"Prevented self-loop relationship on node '{source_id}'.")
            return False

        if not self.graph.has_node(source_id) or not self.graph.has_node(target_id):
            logger.warning(f"Cannot add edge {source_id} -> {target_id}: node missing.")
            return False

        if not self.graph.has_edge(source_id, target_id):
            self.graph.add_edge(
                source_id,
                target_id,
                relation=relation,
                role=role or "GENERAL",
                evidence_text=evidence_text or "",
                confidence=confidence if confidence is not None else 1.0,
                section=section or "General Context"
            )
            return True
        return False

    def add_paper(self, paper: Any) -> str:
        """
        Extract concepts from a ResearchPaper object or dictionary and add nodes + edges.
        Supports role-aware metadata structures when available.
        """
        def _get_list(obj: Any, key: str) -> List[Any]:
            val = obj.get(key) if isinstance(obj, dict) else getattr(obj, key, None)
            return val if isinstance(val, list) else []

        if isinstance(paper, dict):
            p_id = paper.get("id")
            title = paper.get("title", "")
        else:
            p_id = getattr(paper, "id", None)
            title = getattr(paper, "title", "")

        keywords = _get_list(paper, "keywords")
        algorithms = _get_list(paper, "algorithms")
        datasets = _get_list(paper, "datasets")
        methodologies = _get_list(paper, "methodologies")
        application_domains = _get_list(paper, "application_domains")

        datasets_roles = _get_list(paper, "datasets_with_roles")
        algorithms_roles = _get_list(paper, "algorithms_with_roles")
        domains_roles = _get_list(paper, "application_domains_with_roles")

        if p_id is None:
            raise ValueError("ResearchPaper record must contain an 'id'.")

        paper_node_id = self.add_paper_node(paper_id=p_id, title=title)

        if datasets_roles:
            for d_info in datasets_roles:
                d_name = d_info.get("dataset") if isinstance(d_info, dict) else getattr(d_info, "dataset", "")
                d_role = d_info.get("role") if isinstance(d_info, dict) else getattr(d_info, "role", "MENTIONED_DATASET")
                d_ev = d_info.get("evidence_text") if isinstance(d_info, dict) else getattr(d_info, "evidence_text", "")
                d_conf = d_info.get("confidence") if isinstance(d_info, dict) else getattr(d_info, "confidence", 1.0)
                d_sec = d_info.get("section") if isinstance(d_info, dict) else getattr(d_info, "section", "")

                node_id = self.add_entity(NODE_TYPE_DATASET, d_name, role=d_role, evidence_text=d_ev, confidence=d_conf)
                if node_id:
                    rel_name = "uses_experimental_dataset" if d_role == "EXPERIMENTAL_DATASET" else "references_dataset"
                    self.add_relationship(paper_node_id, node_id, rel_name, role=d_role, evidence_text=d_ev, confidence=d_conf, section=d_sec)

        elif datasets:
            for item in datasets:
                entity_node_id = self.add_entity(NODE_TYPE_DATASET, item)
                if entity_node_id:
                    self.add_relationship(paper_node_id, entity_node_id, REL_USES_DATASET)

        if algorithms_roles:
            for a_info in algorithms_roles:
                a_name = a_info.get("algorithm") if isinstance(a_info, dict) else getattr(a_info, "algorithm", "")
                a_role = a_info.get("role") if isinstance(a_info, dict) else getattr(a_info, "role", "MENTIONED_MODEL")
                a_ev = a_info.get("evidence_text") if isinstance(a_info, dict) else getattr(a_info, "evidence_text", "")
                a_conf = a_info.get("confidence") if isinstance(a_info, dict) else getattr(a_info, "confidence", 1.0)

                node_id = self.add_entity(NODE_TYPE_ALGORITHM, a_name, role=a_role, evidence_text=a_ev, confidence=a_conf)
                if node_id:
                    rel_name = "proposes_model" if a_role == "PROPOSED_MODEL" else ("compares_model" if a_role == "COMPARISON_MODEL" else "uses_model")
                    self.add_relationship(paper_node_id, node_id, rel_name, role=a_role, evidence_text=a_ev, confidence=a_conf)

        elif algorithms:
            for item in algorithms:
                entity_node_id = self.add_entity(NODE_TYPE_ALGORITHM, item)
                if entity_node_id:
                    self.add_relationship(paper_node_id, entity_node_id, REL_USES_ALGORITHM)

        if domains_roles:
            for dom_info in domains_roles:
                dom_name = dom_info.get("domain") if isinstance(dom_info, dict) else getattr(dom_info, "domain", "")
                dom_role = dom_info.get("role") if isinstance(dom_info, dict) else getattr(dom_info, "role", "MENTIONED_DOMAIN")
                dom_ev = dom_info.get("evidence_text") if isinstance(dom_info, dict) else getattr(dom_info, "evidence_text", "")

                node_id = self.add_entity(NODE_TYPE_DOMAIN, dom_name, role=dom_role, evidence_text=dom_ev)
                if node_id:
                    rel_name = "has_primary_domain" if dom_role == "PRIMARY_DOMAIN" else "mentions_domain"
                    self.add_relationship(paper_node_id, node_id, rel_name, role=dom_role, evidence_text=dom_ev)

        elif application_domains:
            for item in application_domains:
                entity_node_id = self.add_entity(NODE_TYPE_DOMAIN, item)
                if entity_node_id:
                    self.add_relationship(paper_node_id, entity_node_id, REL_HAS_DOMAIN)

        if keywords:
            for item in keywords:
                entity_node_id = self.add_entity(NODE_TYPE_KEYWORD, item)
                if entity_node_id:
                    self.add_relationship(paper_node_id, entity_node_id, REL_HAS_KEYWORD)

        if methodologies:
            for item in methodologies:
                entity_node_id = self.add_entity(NODE_TYPE_METHODOLOGY, item)
                if entity_node_id:
                    self.add_relationship(paper_node_id, entity_node_id, REL_USES_METHODOLOGY)

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
