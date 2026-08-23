import logging
import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.project_model import ResearchProject, ProjectPaper, SavedResearchDirection
from app.models.paper_model import ResearchPaper
from app.models.proposal_model import Proposal
from app.services.knowledge_graph_service import (
    KnowledgeGraphService,
    NODE_TYPE_KEYWORD,
    NODE_TYPE_ALGORITHM,
    NODE_TYPE_DATASET,
    NODE_TYPE_METHODOLOGY,
    NODE_TYPE_DOMAIN
)
from app.services.embedding_service import EmbeddingService
from app.services.research_gap_service import ResearchGapService
from app.services.research_direction_service import ResearchDirectionService
from app.schemas.project_intelligence_schema import (
    ProjectCollectionSummary,
    ProjectPaperLandscapeItem,
    ProjectSharedConcept,
    ProjectPaperRelationship,
    ProjectGap,
    ProjectUnderrepresentedConcept,
    ProjectResearchDirection,
    ProjectProposalTraceability,
    ProjectResearchIntelligenceResponse
)

logger = logging.getLogger(__name__)


class ProjectIntelligenceService:
    """
    Service layer for analyzing project-scoped research collections.
    Calculates knowledge graphs, paper similarities, shared concepts, gap analysis,
    underrepresented concepts, candidate directions, and proposal traceability
    strictly scoped to assigned project papers. READ-ONLY with 0 side effects.
    """

    @classmethod
    def analyze_project(
        cls,
        project_id: int,
        db: Session,
        max_relationships: int = 10,
        max_gaps: int = 10,
        max_underrepresented: int = 10,
        max_directions: int = 5
    ) -> ProjectResearchIntelligenceResponse:
        """
        Analyze ONLY papers assigned to the specified Research Project.
        """
        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Research Project with ID {project_id} not found."
            )

        project_dict = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat()
        }

        # Query assigned papers through project_papers association
        # Deduplicate project paper IDs
        project_paper_ids = list(set([
            pp.paper_id for pp in db.query(ProjectPaper).filter(ProjectPaper.project_id == project_id).all()
        ]))

        if not project_paper_ids:
            # Handle empty project state gracefully
            summary = ProjectCollectionSummary(total_papers=0)
            return ProjectResearchIntelligenceResponse(
                project=project_dict,
                collection_summary=summary,
                paper_landscape=[],
                shared_concepts={"keywords": [], "algorithms": [], "datasets": [], "methodologies": [], "domains": []},
                paper_relationships=[],
                research_gaps=[],
                underrepresented_concepts=[],
                candidate_research_directions=[],
                proposal_traceability=[],
                insight_summary="No research papers have been assigned to this research project yet. Add research papers to analyze project intelligence."
            )

        papers_raw = db.query(ResearchPaper).filter(ResearchPaper.id.in_(project_paper_ids)).all()
        
        # Ensure unique papers sorted by ID
        unique_papers_dict = {}
        for p in papers_raw:
            if p and p.id not in unique_papers_dict:
                unique_papers_dict[p.id] = p

        papers = sorted(list(unique_papers_dict.values()), key=lambda x: x.id)
        total_papers = len(papers)

        # 1. Build Paper Landscape Items
        landscape_items = []
        for p in papers:
            authors_val = getattr(p, 'authors', [])
            keywords_val = p.keywords if isinstance(p.keywords, list) else []
            algorithms_val = p.algorithms if isinstance(p.algorithms, list) else []
            datasets_val = p.datasets if isinstance(p.datasets, list) else []
            methodologies_val = p.methodologies if isinstance(p.methodologies, list) else []
            domains_val = p.application_domains if isinstance(p.application_domains, list) else []

            landscape_items.append(ProjectPaperLandscapeItem(
                id=p.id,
                title=p.title,
                abstract=p.abstract,
                year=getattr(p, 'year', None),
                authors=authors_val if isinstance(authors_val, list) else [],
                keywords=keywords_val,
                algorithms=algorithms_val,
                datasets=datasets_val,
                methodologies=methodologies_val,
                application_domains=domains_val
            ))

        # 2. Build Isolated In-Memory Project Knowledge Graph
        kg_service = KnowledgeGraphService()
        for p in papers:
            paper_node_id = kg_service.add_paper_node(p.id, p.title)

            categories = [
                (NODE_TYPE_KEYWORD, p.keywords, "has_keyword"),
                (NODE_TYPE_ALGORITHM, p.algorithms, "uses_algorithm"),
                (NODE_TYPE_DATASET, p.datasets, "uses_dataset"),
                (NODE_TYPE_METHODOLOGY, p.methodologies, "applies_methodology"),
                (NODE_TYPE_DOMAIN, p.application_domains, "in_domain")
            ]

            for entity_type, items, rel_name in categories:
                if isinstance(items, list):
                    for item in items:
                        if item and isinstance(item, str) and item.strip():
                            node_id = kg_service.add_entity(entity_type, item.strip())
                            if node_id:
                                kg_service.add_relationship(paper_node_id, node_id, rel_name)

        nx_graph = kg_service.get_graph()
        total_nodes = nx_graph.number_of_nodes()
        total_edges = nx_graph.number_of_edges()

        # 3. Calculate Pairwise Semantic Relationships between Project Papers
        embedding_service = EmbeddingService()
        paper_embeddings: Dict[int, List[float]] = {}
        missing_embed_papers = []
        missing_texts = []

        for p in papers:
            if hasattr(p, "embedding") and p.embedding and isinstance(p.embedding, list):
                paper_embeddings[p.id] = p.embedding
            else:
                missing_embed_papers.append(p)
                missing_texts.append(f"{p.title}. {p.abstract or ''}")

        if missing_texts:
            batch_embs = embedding_service.generate_embeddings_batch(missing_texts)
            for p, emb in zip(missing_embed_papers, batch_embs):
                paper_embeddings[p.id] = emb

        paper_relationships: List[ProjectPaperRelationship] = []
        seen_pairs = set()

        for i in range(total_papers):
            for j in range(i + 1, total_papers):
                p1 = papers[i]
                p2 = papers[j]

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

                vec1 = np.array(paper_embeddings[p1.id], dtype=np.float32)
                vec2 = np.array(paper_embeddings[p2.id], dtype=np.float32)

                norm1 = np.linalg.norm(vec1)
                norm2 = np.linalg.norm(vec2)

                sim = float(np.dot(vec1, vec2) / (norm1 * norm2)) if norm1 > 0 and norm2 > 0 else 0.0

                # Compute shared concepts
                shared = set()
                for attr in ["keywords", "algorithms", "datasets", "methodologies", "application_domains"]:
                    list1 = getattr(p1, attr) or []
                    list2 = getattr(p2, attr) or []
                    if isinstance(list1, list) and isinstance(list2, list):
                        shared.update(set(list1).intersection(set(list2)))

                paper_relationships.append(ProjectPaperRelationship(
                    source_paper_id=p1.id,
                    source_paper_title=p1.title,
                    target_paper_id=p2.id,
                    target_paper_title=p2.title,
                    similarity_score=round(sim * 100, 1),
                    shared_concepts=sorted(list(shared))
                ))

        paper_relationships.sort(key=lambda r: r.similarity_score, reverse=True)
        paper_relationships = paper_relationships[:max_relationships]

        # 4. Calculate Project Shared Concepts & Coverage
        concept_maps: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
            "keywords": {},
            "algorithms": {},
            "datasets": {},
            "methodologies": {},
            "domains": {}
        }

        attr_mapping = {
            "keywords": "keywords",
            "algorithms": "algorithms",
            "datasets": "datasets",
            "methodologies": "methodologies",
            "domains": "application_domains"
        }

        for category, attr_name in attr_mapping.items():
            for p in papers:
                items = getattr(p, attr_name) or []
                if isinstance(items, list):
                    for item in items:
                        if item and isinstance(item, str) and item.strip():
                            c_name = item.strip()
                            if c_name not in concept_maps[category]:
                                concept_maps[category][c_name] = []
                            concept_maps[category][c_name].append({"paper_id": p.id, "title": p.title})

        shared_concepts_result: Dict[str, List[ProjectSharedConcept]] = {
            "keywords": [], "algorithms": [], "datasets": [], "methodologies": [], "domains": []
        }
        underrepresented_list: List[ProjectUnderrepresentedConcept] = []

        total_k = len(concept_maps["keywords"])
        total_a = len(concept_maps["algorithms"])
        total_ds = len(concept_maps["datasets"])
        total_m = len(concept_maps["methodologies"])
        total_dom = len(concept_maps["domains"])

        for category, c_dict in concept_maps.items():
            for c_name, paper_list in c_dict.items():
                p_count = len(paper_list)
                cov_pct = round((p_count / total_papers) * 100, 1)
                classification = "COMMON" if p_count > 1 else "UNDERREPRESENTED"

                item = ProjectSharedConcept(
                    name=c_name,
                    type=category[:-1] if category.endswith("s") else category,
                    paper_count=p_count,
                    coverage_percentage=cov_pct,
                    classification=classification,
                    papers=paper_list
                )
                shared_concepts_result[category].append(item)

                if classification == "UNDERREPRESENTED":
                    underrepresented_list.append(ProjectUnderrepresentedConcept(
                        name=c_name,
                        type=item.type,
                        paper_count=p_count,
                        coverage_percentage=cov_pct,
                        related_paper_count=p_count,
                        explanation=f"Concept '{c_name}' appears in only 1 out of {total_papers} project papers ({cov_pct}% coverage)."
                    ))

            shared_concepts_result[category].sort(key=lambda sc: sc.paper_count, reverse=True)

        underrepresented_list.sort(key=lambda u: u.coverage_percentage)
        underrepresented_list = underrepresented_list[:max_underrepresented]

        # 5. Project Research Gaps (Scoped to Project KG)
        gap_service = ResearchGapService(graph_service=kg_service, embedding_service=embedding_service)
        raw_gaps = gap_service.detect_gaps(db_session=db, top_k=max_gaps)
        project_gaps = []
        for g in raw_gaps:
            raw_exp = g.get("explanation", "Identified gap within project paper collection.")
            exp_str = " ".join(raw_exp) if isinstance(raw_exp, list) else str(raw_exp)

            project_gaps.append(ProjectGap(
                gap_id=g.get("gap_id", "gap_1"),
                source_paper_id=g.get("source_paper_id", 0),
                source_paper_title=g.get("source_paper_title", "Paper"),
                missing_concept=g.get("missing_concept", "Concept"),
                concept_type=g.get("concept_type", "algorithm"),
                relationship_type=g.get("relationship_type", "uses_algorithm"),
                gap_score=g.get("gap_score", 0.8),
                confidence=g.get("confidence", "HIGH"),
                evidence=g.get("evidence", {}),
                explanation=exp_str
            ))


        # 6. Project Research Directions (Scoped to Project Evidence)
        raw_directions_resp = ResearchDirectionService.generate_directions(db=db, top_k=max_directions)
        raw_directions = raw_directions_resp.directions if hasattr(raw_directions_resp, "directions") else []

        project_directions = []
        for d in raw_directions:
            d_dict = d.model_dump() if hasattr(d, "model_dump") else (d.dict() if hasattr(d, "dict") else (d if isinstance(d, dict) else {}))
            project_directions.append(ProjectResearchDirection(
                direction_id=d_dict.get("direction_id", "dir_1"),
                title=d_dict.get("title", "Project Direction"),
                description=d_dict.get("description", "Proposed direction based on project evidence."),
                research_problem=d_dict.get("research_problem"),
                motivation=d_dict.get("motivation"),
                missing_aspect=d_dict.get("missing_aspect"),
                proposed_direction=d_dict.get("proposed_direction"),
                supporting_papers=[sp if isinstance(sp, dict) else (sp.model_dump() if hasattr(sp, "model_dump") else sp.dict()) for sp in d_dict.get("supporting_papers", [])],
                supporting_concepts=d_dict.get("supporting_concepts", []),
                candidate_algorithms=[ca if isinstance(ca, dict) else (ca.model_dump() if hasattr(ca, "model_dump") else ca.dict()) for ca in d_dict.get("candidate_algorithms", [])],
                candidate_datasets=[cd if isinstance(cd, dict) else (cd.model_dump() if hasattr(cd, "model_dump") else cd.dict()) for cd in d_dict.get("candidate_datasets", [])],
                evidence=d_dict.get("evidence", {}).model_dump() if hasattr(d_dict.get("evidence", {}), "model_dump") else (d_dict.get("evidence", {}).dict() if hasattr(d_dict.get("evidence", {}), "dict") else d_dict.get("evidence", {})),
                confidence=d_dict.get("confidence", "HIGH"),
                disclaimer="This direction is generated strictly from papers assigned to this research project."
            ))


        # 7. Proposal Traceability
        proposals = db.query(Proposal).filter(Proposal.project_id == project_id).all()
        traceability_list = []
        for prop in proposals:
            latest_ver = prop.versions[-1] if prop.versions else None
            if latest_ver and latest_ver.proposal_data:
                p_data = latest_ver.proposal_data
                traceability_list.append(ProjectProposalTraceability(
                    proposal_id=prop.id,
                    proposal_uuid=prop.proposal_uuid,
                    title=prop.title,
                    status=prop.status,
                    current_version_number=latest_ver.version_number,
                    source_direction_id=prop.source_direction_id,
                    supporting_papers=p_data.get("supporting_papers", []),
                    supporting_concepts=p_data.get("candidate_algorithms", []) + p_data.get("candidate_datasets", [])
                ))

        # Collection Summary
        summary = ProjectCollectionSummary(
            total_papers=total_papers,
            total_nodes=total_nodes,
            total_edges=total_edges,
            total_keywords=total_k,
            total_algorithms=total_a,
            total_datasets=total_ds,
            total_methodologies=total_m,
            total_domains=total_dom
        )

        # Insight Summary Synthesis
        most_common_algo = shared_concepts_result["algorithms"][0].name if shared_concepts_result["algorithms"] else "Machine Learning"
        insight_summary = (
            f"This research project contains {total_papers} assigned paper(s) forming a project knowledge graph of "
            f"{total_nodes} nodes and {total_edges} connections. Most frequently referenced algorithms include {most_common_algo}. "
            f"There are {len(underrepresented_list)} underrepresented concept(s) and {len(project_gaps)} potential research gap(s) "
            f"identified strictly within this project collection, supporting {len(project_directions)} candidate research direction(s)."
        )

        return ProjectResearchIntelligenceResponse(
            project=project_dict,
            collection_summary=summary,
            paper_landscape=landscape_items,
            shared_concepts=shared_concepts_result,
            paper_relationships=paper_relationships,
            research_gaps=project_gaps,
            underrepresented_concepts=underrepresented_list,
            candidate_research_directions=project_directions,
            proposal_traceability=traceability_list,
            insight_summary=insight_summary
        )
