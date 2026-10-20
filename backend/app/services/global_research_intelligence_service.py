import math
import logging
from typing import Dict, Any, List, Optional, Set, Tuple
from sqlalchemy.orm import Session
import numpy as np

from app.services.knowledge_graph_service import (
    KnowledgeGraphService,
    NODE_TYPE_PAPER,
    NODE_TYPE_KEYWORD,
    NODE_TYPE_ALGORITHM,
    NODE_TYPE_DATASET,
    NODE_TYPE_METHODOLOGY,
    NODE_TYPE_DOMAIN
)
from app.services.knowledge_graph_builder import KnowledgeGraphBuilder
from app.services.link_prediction_service import LinkPredictionService
from app.services.research_gap_service import ResearchGapService
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

GLOBAL_DISCLAIMER = (
    "All findings are derived from the currently indexed research-paper collection "
    "and may change as additional papers are added. Research-gap and research-direction "
    "outputs represent collection-based analytical opportunities and do not establish global academic novelty."
)


class GlobalResearchIntelligenceService:
    """
    Service responsible for analyzing the ENTIRE research paper collection as a unified landscape,
    synthesizing Knowledge Graph metrics, pairwise paper relationships, aggregated research gaps,
    underrepresented concepts, and candidate research directions.
    Completely read-only.
    """

    def __init__(
        self,
        graph_service: Optional[KnowledgeGraphService] = None,
        link_prediction_service: Optional[LinkPredictionService] = None,
        research_gap_service: Optional[ResearchGapService] = None,
        embedding_service: Optional[EmbeddingService] = None
    ):
        self.graph_service = graph_service or KnowledgeGraphService()
        self.link_prediction_service = link_prediction_service or LinkPredictionService(graph_service=self.graph_service)
        self.research_gap_service = research_gap_service or ResearchGapService(
            graph_service=self.graph_service,
            link_prediction_service=self.link_prediction_service,
            embedding_service=embedding_service
        )
        self.embedding_service = embedding_service or EmbeddingService()

    def analyze_collection(
        self,
        db_session: Session,
        max_paper_relationships: int = 50,
        max_gaps: int = 20,
        max_underrepresented: int = 20,
        max_directions: int = 10
    ) -> Dict[str, Any]:
        if db_session is None or not hasattr(db_session, "query"):
            logger.error("Invalid database session provided to analyze_collection.")
            raise ValueError("A valid database session must be provided.")

        from app.models.paper_model import ResearchPaper
        papers = db_session.query(ResearchPaper).all()
        total_papers = len(papers)

        # Build / inspect knowledge graph
        builder = KnowledgeGraphBuilder(graph_service=self.graph_service)
        graph_stats = builder.build_from_database(db_session)
        graph = self.graph_service.get_graph()

        if total_papers == 0:
            return self._build_empty_response()

        paper_map = {p.id: p for p in papers}

        # 1. Paper Landscape (Part 2)
        paper_landscape = [
            {
                "paper_id": p.id,
                "title": p.title,
                "abstract": p.abstract or "",
                "keywords": p.keywords or [],
                "algorithms": p.algorithms or [],
                "datasets": p.datasets or [],
                "methodologies": p.methodologies or [],
                "application_domains": p.application_domains or []
            }
            for p in sorted(papers, key=lambda x: x.id)
        ]

        # 2. Shared Research Concepts (Part 3)
        shared_concepts = self._calculate_shared_concepts(graph, total_papers)

        # 3. Paper-to-Paper Relationships (Part 4)
        paper_relationships = self._calculate_paper_relationships(
            papers=papers,
            max_relationships=max_paper_relationships
        )

        # 4. Link Predictions & Research Gaps Aggregation (Part 5)
        link_candidates = self.link_prediction_service.predict_links(graph=graph, top_k=100)
        total_link_candidates = len(link_candidates)

        detected_gaps = self.research_gap_service.detect_gaps(db_session=db_session, top_k=max_gaps)
        total_gaps = len(detected_gaps)

        high_conf = sum(1 for g in detected_gaps if g["confidence"] == "High")
        mod_conf = sum(1 for g in detected_gaps if g["confidence"] == "Moderate")
        low_conf = sum(1 for g in detected_gaps if g["confidence"] == "Low")

        gap_summary = {
            "total_gaps": total_gaps,
            "high_confidence": high_conf,
            "moderate_confidence": mod_conf,
            "low_confidence": low_conf
        }

        # 5. Underrepresented Concepts (Part 6)
        underrepresented_concepts = self._calculate_underrepresented_concepts(
            graph=graph,
            total_papers=total_papers,
            max_underrepresented=max_underrepresented
        )

        # 6. Candidate Research Directions (Part 7)
        candidate_directions = self._generate_candidate_directions(
            gaps=detected_gaps,
            underrepresented=underrepresented_concepts,
            total_papers=total_papers,
            max_directions=max_directions
        )

        # 7. Collection Summary (Part 1)
        collection_summary = {
            "total_papers": total_papers,
            "total_graph_nodes": graph_stats.get("total_nodes", 0),
            "total_graph_edges": graph_stats.get("total_edges", 0),
            "total_keywords": graph_stats.get("keyword_nodes", 0),
            "total_algorithms": graph_stats.get("algorithm_nodes", 0),
            "total_datasets": graph_stats.get("dataset_nodes", 0),
            "total_methodologies": graph_stats.get("methodology_nodes", 0),
            "total_domains": graph_stats.get("domain_nodes", 0),
            "total_potential_gaps": total_gaps,
            "total_link_prediction_candidates": total_link_candidates
        }

        return {
            "collection_summary": collection_summary,
            "paper_landscape": paper_landscape,
            "shared_concepts": shared_concepts,
            "paper_relationships": paper_relationships,
            "research_gap_summary": gap_summary,
            "gaps": detected_gaps,
            "underrepresented_concepts": underrepresented_concepts,
            "candidate_research_directions": candidate_directions,
            "collection_disclaimer": GLOBAL_DISCLAIMER
        }

    def _calculate_shared_concepts(self, graph, total_papers: int) -> Dict[str, List[Dict[str, Any]]]:
        if total_papers == 0 or graph is None:
            return {"keywords": [], "algorithms": [], "datasets": [], "methodologies": [], "domains": []}

        type_map = {
            NODE_TYPE_KEYWORD: "keywords",
            NODE_TYPE_ALGORITHM: "algorithms",
            NODE_TYPE_DATASET: "datasets",
            NODE_TYPE_METHODOLOGY: "methodologies",
            NODE_TYPE_DOMAIN: "domains"
        }

        grouped: Dict[str, List[Tuple[str, int]]] = {v: [] for v in type_map.values()}

        for node_id, attrs in graph.nodes(data=True):
            n_type = attrs.get("type")
            if n_type in type_map:
                key = type_map[n_type]
                label = attrs.get("label", node_id)
                count = graph.in_degree(node_id)
                grouped[key].append((label, count))

        result = {}
        for category, items in grouped.items():
            items.sort(key=lambda x: (-x[1], x[0]))
            result[category] = [
                {
                    "name": label,
                    "paper_count": count,
                    "coverage_percentage": round((count / total_papers) * 100.0, 1)
                }
                for label, count in items
            ]

        return result

    def _calculate_paper_relationships(self, papers, max_relationships: int) -> List[Dict[str, Any]]:
        if not papers or len(papers) < 2:
            return []

        # Deduplicate paper objects by paper.id first
        unique_papers_dict = {}
        for p in papers:
            if p and hasattr(p, "id") and p.id not in unique_papers_dict:
                unique_papers_dict[p.id] = p

        sorted_papers = sorted(list(unique_papers_dict.values()), key=lambda x: x.id)
        n = len(sorted_papers)
        if n < 2:
            return []

        texts = [f"Title: {p.title}\nAbstract: {p.abstract or ''}" for p in sorted_papers]
        raw_embs = self.embedding_service.generate_embeddings_batch(texts)
        emb_matrix = np.array(raw_embs, dtype=np.float32)

        # Compute all pairwise L2 norm vectors for safety
        norms = np.linalg.norm(emb_matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        normalized_matrix = emb_matrix / norms
        sim_matrix = np.dot(normalized_matrix, normalized_matrix.T)

        relationships = []
        seen_pairs = set()

        for i in range(n):
            for j in range(i + 1, n):
                p1 = sorted_papers[i]
                p2 = sorted_papers[j]

                # Rule 1: Exclude self-relationships
                if p1.id == p2.id:
                    continue

                # Rule 2: Canonical Pair Key min(id1, id2):max(id1, id2)
                low_id = min(p1.id, p2.id)
                high_id = max(p1.id, p2.id)
                pair_key = f"{low_id}:{high_id}"

                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                sim = float(sim_matrix[i, j])
                relationships.append({
                    "source_paper_id": p1.id,
                    "source_title": p1.title,
                    "target_paper_id": p2.id,
                    "target_title": p2.title,
                    "similarity_score": round(sim, 4)
                })

        # Sort: highest similarity first, then source_paper_id ASC, target_paper_id ASC
        relationships.sort(key=lambda x: (-x["similarity_score"], x["source_paper_id"], x["target_paper_id"]))
        return relationships[:max_relationships]

    def _calculate_underrepresented_concepts(self, graph, total_papers: int, max_underrepresented: int) -> List[Dict[str, Any]]:
        if total_papers == 0 or graph is None:
            return []

        undirected = graph.to_undirected()
        underrepresented = []

        for node_id, attrs in graph.nodes(data=True):
            n_type = attrs.get("type")
            if n_type == NODE_TYPE_PAPER:
                continue

            paper_count = graph.in_degree(node_id)
            # Underrepresented if present in at least 1 paper and used by fewer than 40% of papers in collection
            if 1 <= paper_count < max(2, math.ceil(total_papers * 0.4)):
                label = attrs.get("label", node_id)
                
                # Calculate related papers (2-hop paper neighbors connected through common concepts)
                concept_neighbors = set(undirected.neighbors(node_id))
                related_papers = set()
                for p_node in concept_neighbors:
                    for c_node in undirected.neighbors(p_node):
                        for r_paper in undirected.neighbors(c_node):
                            if r_paper.startswith("paper_") and r_paper not in concept_neighbors:
                                related_papers.add(r_paper)

                cov_pct = round((paper_count / total_papers) * 100.0, 1)
                underrepresented.append({
                    "name": label,
                    "type": n_type,
                    "paper_count": paper_count,
                    "coverage_percentage": cov_pct,
                    "related_paper_count": len(related_papers),
                    "reason": f"Concept '{label}' is used by only {paper_count} paper(s) ({cov_pct}% coverage) within the current collection."
                })

        # Sort by paper_count ASC (most rare first), then related_paper_count DESC, then name ASC
        underrepresented.sort(key=lambda x: (x["paper_count"], -x["related_paper_count"], x["name"]))
        return underrepresented[:max_underrepresented]

    def _generate_candidate_directions(
        self,
        gaps: List[Dict[str, Any]],
        underrepresented: List[Dict[str, Any]],
        total_papers: int,
        max_directions: int
    ) -> List[Dict[str, Any]]:
        if not gaps:
            return []

        import string
        directions_by_key: Dict[str, Dict[str, Any]] = {}
        for g in gaps:
            target_label = g.get("target_label", "")
            target_type = g.get("target_type", "").lower()
            source_title = g.get("source_paper_title", "")
            source_p_id = g.get("source_paper_id")
            gap_score = g.get("gap_score", 0.0)
            ev = g.get("evidence", {})
            semantic_evidence = ev.get("semantic_evidence", 0.0)
            link_score = ev.get("link_prediction_score", 0.0)
            confidence = g.get("confidence", "Moderate")

            # Canonical opportunity key based on target concept and source context
            norm_target = " ".join(target_label.lower().translate(str.maketrans("", "", string.punctuation)).split())
            norm_src = " ".join(source_title.lower().translate(str.maketrans("", "", string.punctuation)).split())
            opp_key = f"{norm_target}___{norm_src}"

            cand_algos = [{"name": target_label, "supporting_paper_count": 1, "reason": "Identified target concept"}] if target_type == 'algorithm' else []
            cand_datasets = [{"name": target_label, "supporting_paper_count": 1, "reason": "Identified candidate dataset"}] if target_type == 'dataset' else []

            title = f"Explore integration of {target_label} with {source_title}"
            desc = (
                f"Collection analysis indicates a potential research opportunity in applying {target_label} "
                f"({target_type}) to research surrounding '{source_title}'. "
                f"This combination exhibits strong structural similarity ({link_score}) "
                f"and semantic relevance ({semantic_evidence})."
            )
            research_problem = f"Current papers surrounding '{source_title}' do not incorporate {target_label} ({target_type})."
            motivation = f"Collection analysis reveals strong semantic similarity ({semantic_evidence}) and gap score ({gap_score}) for integrating {target_label}."
            missing_aspect = f"Integration of {target_label} with baseline approaches in '{source_title}' remains underrepresented."
            proposed_direction = f"Investigate combining {target_label} with baseline techniques to evaluate potential performance and methodology enhancements."

            supporting_paper = {"paper_id": source_p_id, "title": source_title, "role": "Source paper context"}

            if opp_key in directions_by_key:
                # Merge with existing
                ex = directions_by_key[opp_key]
                ex["evidence"]["gap_score"] = round(max(ex["evidence"]["gap_score"], gap_score), 4)
                ex["evidence"]["semantic_evidence"] = round(max(ex["evidence"]["semantic_evidence"], semantic_evidence), 4)
                # Deduplicate supporting papers
                existing_sp_ids = {p["paper_id"] for p in ex["supporting_papers"]}
                if source_p_id not in existing_sp_ids:
                    ex["supporting_papers"].append(supporting_paper)
                ex["evidence"]["collection_coverage"] = round((len(ex["supporting_papers"]) / max(1, total_papers)) * 100.0, 1)
                # Pick higher confidence
                conf_order = {"HIGH": 3, "MODERATE": 2, "LOW": 1}
                if conf_order.get(confidence.upper(), 1) > conf_order.get(ex["confidence"].upper(), 1):
                    ex["confidence"] = confidence
            else:
                directions_by_key[opp_key] = {
                    "direction_id": "temp",
                    "title": title,
                    "description": desc,
                    "research_problem": research_problem,
                    "motivation": motivation,
                    "missing_aspect": missing_aspect,
                    "proposed_direction": proposed_direction,
                    "supporting_papers": [supporting_paper],
                    "supporting_concepts": [target_label],
                    "candidate_algorithms": cand_algos,
                    "candidate_datasets": cand_datasets,
                    "evidence": {
                        "gap_score": gap_score,
                        "semantic_evidence": semantic_evidence,
                        "collection_coverage": round((1 / max(1, total_papers)) * 100.0, 1)
                    },
                    "confidence": confidence,
                    "disclaimer": "This is a collection-based research direction and is not a claim of global academic novelty."
                }

        unique_dirs = list(directions_by_key.values())
        unique_dirs.sort(key=lambda x: (-x["evidence"]["gap_score"], x["title"]))
        final_dirs = []
        for idx, d in enumerate(unique_dirs[:max_directions], start=1):
            d["direction_id"] = f"dir_{idx}"
            final_dirs.append(d)
        return final_dirs

    def _build_empty_response(self) -> Dict[str, Any]:
        return {
            "collection_summary": {
                "total_papers": 0,
                "total_graph_nodes": 0,
                "total_graph_edges": 0,
                "total_keywords": 0,
                "total_algorithms": 0,
                "total_datasets": 0,
                "total_methodologies": 0,
                "total_domains": 0,
                "total_potential_gaps": 0,
                "total_link_prediction_candidates": 0
            },
            "paper_landscape": [],
            "shared_concepts": {
                "keywords": [],
                "algorithms": [],
                "datasets": [],
                "methodologies": [],
                "domains": []
            },
            "paper_relationships": [],
            "research_gap_summary": {
                "total_gaps": 0,
                "high_confidence": 0,
                "moderate_confidence": 0,
                "low_confidence": 0
            },
            "gaps": [],
            "underrepresented_concepts": [],
            "candidate_research_directions": [],
            "collection_disclaimer": GLOBAL_DISCLAIMER
        }
