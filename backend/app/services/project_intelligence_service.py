import os
import json
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
from app.services.research_gap_service import ResearchGapService, canonicalize_concept_name
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

    _stored_intelligence_cache: Dict[int, Dict[str, Any]] = {}

    @classmethod
    def _get_cache_dir(cls) -> str:
        cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage", "cache")
        os.makedirs(cache_dir, exist_ok=True)
        return cache_dir

    @classmethod
    def _get_cache_file_path(cls, project_id: int) -> str:
        return os.path.join(cls._get_cache_dir(), f"project_intel_{project_id}.json")

    @classmethod
    def _save_disk_cache(cls, project_id: int, paper_ids: List[int], response: ProjectResearchIntelligenceResponse) -> None:
        try:
            file_path = cls._get_cache_file_path(project_id)
            resp_dict = response.model_dump() if hasattr(response, "model_dump") else response.dict()
            cache_payload = {
                "project_id": project_id,
                "paper_ids": paper_ids,
                "response": resp_dict
            }
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(cache_payload, f, indent=2)
            logger.info(f"Saved disk intelligence cache for project {project_id}")
        except Exception as e:
            logger.warning(f"Failed to save disk cache for project {project_id}: {e}")

    @classmethod
    def _load_disk_cache(cls, project_id: int, paper_ids: List[int]) -> Optional[ProjectResearchIntelligenceResponse]:
        try:
            file_path = cls._get_cache_file_path(project_id)
            if not os.path.exists(file_path):
                return None
            with open(file_path, "r", encoding="utf-8") as f:
                cache_payload = json.load(f)
            if cache_payload.get("paper_ids") == paper_ids:
                resp_data = cache_payload.get("response")
                if resp_data:
                    if hasattr(ProjectResearchIntelligenceResponse, "model_validate"):
                        response = ProjectResearchIntelligenceResponse.model_validate(resp_data)
                    else:
                        response = ProjectResearchIntelligenceResponse.parse_obj(resp_data)
                    return response
        except Exception as e:
            logger.warning(f"Failed to read disk cache for project {project_id}: {e}")
        return None

    @classmethod
    def invalidate_cache(cls, project_id: Optional[int] = None) -> None:
        """
        Invalidate stored intelligence cache for a specific project or all projects.
        """
        if project_id is not None:
            cls._stored_intelligence_cache.pop(project_id, None)
            try:
                file_path = cls._get_cache_file_path(project_id)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.warning(f"Error removing disk cache file for project {project_id}: {e}")
            logger.info(f"Invalidated stored project intelligence cache for project {project_id}.")
        else:
            cls._stored_intelligence_cache.clear()
            try:
                cache_dir = cls._get_cache_dir()
                if os.path.exists(cache_dir):
                    for fname in os.listdir(cache_dir):
                        if fname.startswith("project_intel_") and fname.endswith(".json"):
                            try:
                                os.remove(os.path.join(cache_dir, fname))
                            except Exception:
                                pass
            except Exception as e:
                logger.warning(f"Error clearing disk cache directory: {e}")
            logger.info("Cleared all stored project intelligence caches.")

    @classmethod
    def analyze_project(
        cls,
        project_id: int,
        db: Session,
        refresh: bool = False,
        max_relationships: int = 10,
        max_gaps: int = 10,
        max_underrepresented: int = 10,
        max_directions: int = 5
    ) -> ProjectResearchIntelligenceResponse:
        """
        Analyze ONLY papers assigned to the specified Research Project.
        Uses fast-read stored project intelligence if available and not explicitly refreshed.
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
        project_paper_ids = sorted(list(set([
            pp.paper_id for pp in db.query(ProjectPaper).filter(ProjectPaper.project_id == project_id).all()
        ])))

        # Check for valid stored intelligence cache (memory or disk)
        cached_response = None
        if not refresh:
            if project_id in cls._stored_intelligence_cache:
                cached = cls._stored_intelligence_cache[project_id]
                if cached.get("paper_ids") == project_paper_ids:
                    logger.info(f"Fast read (memory): Returning stored project intelligence for project {project_id}")
                    cached_response = cached["response"]

            if not cached_response:
                cached_response = cls._load_disk_cache(project_id, project_paper_ids)
                if cached_response:
                    logger.info(f"Fast read (disk): Loaded stored project intelligence for project {project_id}")
                    cls._stored_intelligence_cache[project_id] = {
                        "paper_ids": project_paper_ids,
                        "response": cached_response
                    }

        if cached_response:
            # Refresh dynamic proposal traceability from DB in < 1ms
            proposals_db = db.query(Proposal).filter(Proposal.project_id == project_id).all()
            traceability_list = []
            for prop in proposals_db:
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
            cached_response.proposal_traceability = traceability_list
            return cached_response

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

        # 1. Build Paper Landscape Items with Evidence-Grounded Re-evaluation
        from app.services.metadata_extractor import (
            MetadataExtractor,
            DatasetExtractor,
            ApplicationDomainExtractor,
            AlgorithmExtractor,
            MethodologyExtractor
        )

        landscape_items = []
        for p in papers:
            authors_val = getattr(p, 'authors', [])
            full_txt = getattr(p, 'full_text', '') or ''
            
            # Use stored database metadata if present to avoid re-parsing full_text on every request
            has_db_meta = any([
                isinstance(p.keywords, list) and len(p.keywords) > 0,
                isinstance(p.algorithms, list) and len(p.algorithms) > 0,
                isinstance(p.datasets, list) and len(p.datasets) > 0,
                isinstance(p.methodologies, list) and len(p.methodologies) > 0,
                isinstance(p.application_domains, list) and len(p.application_domains) > 0
            ])

            # Extract or retrieve clean metadata
            clean_meta = MetadataExtractor.extract(p.title, p.abstract, full_txt)
            db_keywords = getattr(p, 'keywords', []) or []
            db_algos = getattr(p, 'algorithms', []) or []
            db_datasets = getattr(p, 'datasets', []) or []
            db_methods = getattr(p, 'methodologies', []) or []
            db_domains = getattr(p, 'application_domains', []) or []

            keywords_val = list(dict.fromkeys((clean_meta["keywords"] or []) + (db_keywords if isinstance(db_keywords, list) else [])))
            algorithms_val = list(dict.fromkeys((clean_meta["algorithms"] or []) + (db_algos if isinstance(db_algos, list) else [])))
            datasets_val = list(dict.fromkeys((clean_meta["datasets"] or []) + (db_datasets if isinstance(db_datasets, list) else [])))
            methodologies_val = list(dict.fromkeys((clean_meta["methodologies"] or []) + (db_methods if isinstance(db_methods, list) else [])))
            domains_val = list(dict.fromkeys((clean_meta["application_domains"] or []) + (db_domains if isinstance(db_domains, list) else [])))
            metrics_val = clean_meta.get("metrics", [])
            tasks_val = clean_meta.get("tasks", [])
            apps_val = clean_meta.get("applications", [])

            keyword_details_val = getattr(p, 'keyword_details', None) or clean_meta.get("keyword_details", [])
            algorithm_details_val = getattr(p, 'algorithm_details', None) or clean_meta.get("algorithm_details", [])
            dataset_details_val = getattr(p, 'dataset_details', None) or clean_meta.get("dataset_details", [])
            methodology_details_val = getattr(p, 'methodology_details', None) or clean_meta.get("methodology_details", [])

            # Attach clean extracted metadata to paper object for graph & analysis
            p.keywords = keywords_val
            p.algorithms = algorithms_val
            p.datasets = datasets_val
            p.methodologies = methodologies_val
            p.application_domains = domains_val
            p.metrics = metrics_val
            p.tasks = tasks_val
            p.applications = apps_val
            p.keyword_details = keyword_details_val
            p.algorithm_details = algorithm_details_val
            p.dataset_details = dataset_details_val
            p.methodology_details = methodology_details_val

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
                application_domains=domains_val,
                keyword_details=keyword_details_val,
                algorithm_details=algorithm_details_val,
                dataset_details=dataset_details_val,
                methodology_details=methodology_details_val
            ))

        # 2. Build Isolated In-Memory Project Knowledge Graph with Role Awareness
        kg_service = KnowledgeGraphService()
        for p in papers:
            try:
                kg_service.add_paper(p)
            except Exception as err:
                logger.warning(f"Error adding paper ID {p.id} to project knowledge graph: {err}")

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

        # 4. Calculate Project Shared Concepts & Coverage with Strict Cross-Category Separation
        concept_maps: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
            "algorithms": {},
            "datasets": {},
            "methodologies": {},
            "domains": {},
            "metrics": {},
            "tasks": {},
            "applications": {},
            "keywords": {}
        }

        # Populate non-keyword categories first (Entity Precedence: DATASET -> ALGORITHM -> METHODOLOGY -> METRIC -> DOMAIN -> TASK -> APPLICATION)
        non_kw_attr_mapping = {
            "algorithms": "algorithms",
            "datasets": "datasets",
            "methodologies": "methodologies",
            "domains": "application_domains",
            "metrics": "metrics",
            "tasks": "tasks",
            "applications": "applications"
        }

        non_keyword_names_lower = set()

        # Include static taxonomy terms in non_keyword_names_lower to guarantee keyword exclusion
        from app.services.metadata_extractor import (
            DatasetExtractor,
            MetricExtractor,
            MethodologyExtractor,
            AlgorithmExtractor,
            TaskExtractor,
            ApplicationExtractor,
            ApplicationDomainExtractor,
            normalize_research_concept
        )
        for d_k in DatasetExtractor.KNOWN_DATASETS.keys():
            non_keyword_names_lower.add(d_k.lower())
        for m_k in MetricExtractor.METRIC_MAP.keys():
            non_keyword_names_lower.add(m_k.lower())
        for meth_k in MethodologyExtractor.METHODOLOGY_ALIAS_MAP.keys():
            non_keyword_names_lower.add(meth_k.lower())
        for a_k in AlgorithmExtractor.ALGORITHMS_MAP.keys():
            non_keyword_names_lower.add(a_k.lower())
        for t_k in TaskExtractor.TASK_ALIAS_MAP.keys():
            non_keyword_names_lower.add(t_k.lower())
        for app_k in ApplicationExtractor.APPLICATION_ALIAS_MAP.keys():
            non_keyword_names_lower.add(app_k.lower())
        for dom_k in ApplicationDomainExtractor.DOMAIN_KEYWORDS.keys():
            non_keyword_names_lower.add(dom_k.lower())

        for category, attr_name in non_kw_attr_mapping.items():
            for p in papers:
                items = getattr(p, attr_name, []) or []
                if isinstance(items, list):
                    for item in items:
                        if item and isinstance(item, str) and item.strip():
                            c_name = item.strip()
                            if category == "metrics":
                                c_name = MetricExtractor.METRIC_MAP.get(c_name.lower(), c_name)
                            if category == "tasks" and c_name.lower() not in TaskExtractor.TASK_ALIAS_MAP:
                                continue
                            if category == "methodologies" and c_name.lower() not in MethodologyExtractor.METHODOLOGY_ALIAS_MAP:
                                continue
                            # Check generic noise filter (metrics are exempt because metric terms like F1 are in METRIC_NOISE_TERMS)
                            if category != "metrics" and not MetadataExtractor.is_valid_research_concept(c_name):
                                continue
                            non_keyword_names_lower.add(c_name.lower())
                            if c_name not in concept_maps[category]:
                                concept_maps[category][c_name] = []
                            if not any(entry["paper_id"] == p.id for entry in concept_maps[category][c_name]):
                                concept_maps[category][c_name].append({"paper_id": p.id, "title": p.title})

        # Populate keywords category ONLY with residual terms not present in other categories and valid as research concepts
        for p in papers:
            items = getattr(p, "keywords") or []
            if isinstance(items, list):
                for item in items:
                    if item and isinstance(item, str) and item.strip():
                        norm_item = normalize_research_concept(item.strip())
                        c_lower = norm_item.lower()
                        # Strictly reject terms that belong to other specific categories or generic noise/fragments
                        if c_lower in non_keyword_names_lower or any(c_lower == nk or c_lower in nk for nk in non_keyword_names_lower if len(nk) >= 3):
                            continue
                        if not MetadataExtractor.is_valid_research_concept(norm_item):
                            continue
                        if norm_item not in concept_maps["keywords"]:
                            concept_maps["keywords"][norm_item] = []
                        concept_maps["keywords"][norm_item].append({"paper_id": p.id, "title": p.title})

        shared_concepts_result: Dict[str, List[ProjectSharedConcept]] = {
            "keywords": [], "algorithms": [], "datasets": [], "methodologies": [], "domains": [], "metrics": [], "tasks": [], "applications": []
        }
        underrepresented_list: List[ProjectUnderrepresentedConcept] = []

        total_k = len(concept_maps["keywords"])
        total_a = len(concept_maps["algorithms"])
        total_ds = len(concept_maps["datasets"])
        total_m = len(concept_maps["methodologies"])
        total_dom = len(concept_maps["domains"])
        total_met = len(concept_maps["metrics"])

        # Pre-extract paper roles ONCE per paper across categories to prevent N x M full-text re-parsing
        paper_roles_cache = {}
        for p in papers:
            p_txt = getattr(p, 'full_text', '') or ''
            paper_roles_cache[p.id] = {
                "algorithms": {r["name"].lower(): r["role"] for r in AlgorithmExtractor.extract_with_roles(p_txt, title=p.title, abstract=p.abstract) if "name" in r and "role" in r},
                "datasets": {r["name"].lower(): r["role"] for r in DatasetExtractor.extract_with_roles(p_txt, title=p.title, abstract=p.abstract) if "name" in r and "role" in r},
                "domains": {r["domain"].lower(): r["role"] for r in ApplicationDomainExtractor.extract_with_roles(p_txt, title=p.title, abstract=p.abstract) if "domain" in r and "role" in r},
                "methodologies": {r["name"].lower(): r["role"] for r in MethodologyExtractor.extract_with_roles(p_txt, title=p.title, abstract=p.abstract) if "name" in r and "role" in r},
            }

        # Determine concept roles
        for category, c_dict in concept_maps.items():
            for c_name, paper_list in c_dict.items():
                p_count = len(paper_list)
                cov_pct = round((p_count / total_papers) * 100, 1)
                classification = "COMMON" if p_count > 1 else "UNDERREPRESENTED"

                roles_set = set()
                c_name_lower = c_name.lower()
                for p in papers:
                    if p.id in paper_roles_cache and category in paper_roles_cache[p.id]:
                        role_match = paper_roles_cache[p.id][category].get(c_name_lower)
                        if role_match:
                            roles_set.add(role_match)
                    if category == "metrics":
                        roles_set.add("EVALUATION_METRIC")
                    elif category == "keywords":
                        roles_set.add("RESEARCH_CONCEPT")

                roles_list = list(roles_set)
                if not roles_list:
                    if category == "datasets":
                        roles_list = ["EXPERIMENTAL_DATASET"]
                    elif category == "domains":
                        roles_list = ["PRIMARY_DOMAIN"]
                    elif category == "algorithms":
                        roles_list = ["USED_MODEL"]
                    elif category == "methodologies":
                        roles_list = ["PRIMARY_METHODOLOGY"]
                    elif category == "metrics":
                        roles_list = ["EVALUATION_METRIC"]
                    else:
                        roles_list = ["RESEARCH_CONCEPT"]

                item = ProjectSharedConcept(
                    name=c_name,
                    type=category[:-1] if category.endswith("s") else category,
                    paper_count=p_count,
                    coverage_percentage=cov_pct,
                    classification=classification,
                    roles=roles_list,
                    papers=paper_list
                )
                shared_concepts_result[category].append(item)

                if classification == "UNDERREPRESENTED" and category != "metrics":
                    # Exclude metrics and generic keywords from underrepresented gaps candidates
                    if category == "keywords" and ResearchGapService._is_generic_concept(c_name):
                        continue
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

        # 5. Project Research Gaps (Scoped & Aggregated to Project Evidence)
        gap_service = ResearchGapService(graph_service=kg_service, embedding_service=embedding_service)
        raw_gaps = gap_service.detect_gaps(db_session=db, top_k=max_gaps, papers=papers, project_name=project.name)

        project_gaps = []
        for idx, item in enumerate(raw_gaps[:max_gaps], start=1):
            src_papers = item.get("source_papers", [])
            primary_src_id = item.get("source_paper_id", 0)
            primary_src_title = item.get("source_paper_title", "Project Papers")

            exp_list = item.get("explanation", [])
            exp_str = " ".join(exp_list) if isinstance(exp_list, list) else str(exp_list)

            project_gaps.append(ProjectGap(
                gap_id=f"gap_{idx}",
                gap_type=item.get("gap_type", "CROSS_PAPER_COMPARISON"),
                title=item.get("title", f"Unassessed Relationship #{idx}"),
                description=item.get("description", exp_str),
                source_paper_id=primary_src_id,
                source_paper_title=primary_src_title,
                source_papers=src_papers,
                supported_paper_count=item.get("supported_paper_count", len(src_papers)),
                related_concepts=item.get("related_concepts", []),
                missing_concept=item.get("missing_concept", "Unassessed Relationship"),
                concept_type=item.get("concept_type", "algorithm"),
                relationship_type=item.get("relationship_type", "unassessed_relationship"),
                gap_score=round(float(item.get("gap_score", 0.8)), 4),
                confidence=str(item.get("confidence", "Moderate")).capitalize(),
                eligibility_status=item.get("eligibility_status") or item.get("evidence", {}).get("eligibility_status", "QUALIFIED_POTENTIAL_GAP"),
                evidence=item.get("evidence", {}),
                gap_reasoning=item.get("gap_reasoning", {}),
                explanation=exp_str
            ))



        # 6. Project Research Directions (Scoped to Project Evidence)
        raw_directions_resp = ResearchDirectionService.generate_directions(
            db=db,
            top_k=max_directions,
            project_id=project_id,
            project_name=project.name,
            project_papers=papers
        )
        raw_directions = raw_directions_resp.directions if hasattr(raw_directions_resp, "directions") else []

        project_directions = []
        for d in raw_directions:
            d_dict = d.model_dump() if hasattr(d, "model_dump") else (d.dict() if hasattr(d, "dict") else (d if isinstance(d, dict) else {}))
            project_directions.append(ProjectResearchDirection(
                direction_id=d_dict.get("direction_id", "dir_1"),
                opportunity_family_id=d_dict.get("opportunity_family_id"),
                parent_gap_id=d_dict.get("parent_gap_id"),
                gap_relationship_key=d_dict.get("gap_relationship_key"),
                gap_type=d_dict.get("gap_type"),
                gap_evidence_class=d_dict.get("gap_evidence_class"),
                gap_evidence_score=d_dict.get("gap_evidence_score"),
                source_paper_ids=d_dict.get("source_paper_ids", []),
                title=d_dict.get("title", "Project Direction"),
                research_question=d_dict.get("research_question"),
                description=d_dict.get("description", d_dict.get("proposed_direction", "Proposed direction based on project evidence.")),
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

        total_tsk = len(concept_maps["tasks"])
        total_app = len(concept_maps["applications"])

        # Collection Summary
        summary = ProjectCollectionSummary(
            total_papers=total_papers,
            total_nodes=total_nodes,
            total_edges=total_edges,
            total_keywords=total_k,
            total_algorithms=total_a,
            total_datasets=total_ds,
            total_methodologies=total_m,
            total_domains=total_dom,
            total_metrics=total_met,
            total_tasks=total_tsk,
            total_applications=total_app
        )

        # Insight Summary Synthesis
        most_common_algo = shared_concepts_result["algorithms"][0].name if shared_concepts_result["algorithms"] else "Machine Learning"
        insight_summary = (
            f"This research project contains {total_papers} assigned paper(s) forming a project knowledge graph of "
            f"{total_nodes} nodes and {total_edges} connections. Most frequently referenced algorithms include {most_common_algo}. "
            f"There are {len(underrepresented_list)} underrepresented concept(s) and {len(project_gaps)} potential research gap(s) "
            f"identified strictly within this project collection, supporting {len(project_directions)} candidate research direction(s)."
        )

        response = ProjectResearchIntelligenceResponse(
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

        cls._stored_intelligence_cache[project_id] = {
            "paper_ids": project_paper_ids,
            "response": response
        }
        cls._save_disk_cache(project_id, project_paper_ids, response)

        return response

    @classmethod
    def reindex_project(cls, project_id: int, db: Session) -> ProjectResearchIntelligenceResponse:
        """
        Safe REINDEX Operation (Rule #26):
        1. Keeps assigned research papers intact.
        2. Clears stale DB metadata stored on assigned papers.
        3. Re-extracts clean, role-annotated entities from scratch via MetadataExtractor.
        4. Saves fresh metadata to DB.
        5. Re-runs project intelligence analysis and returns clean response.
        """
        cls.invalidate_cache(project_id)
        project_paper_ids = list(set([
            pp.paper_id for pp in db.query(ProjectPaper).filter(ProjectPaper.project_id == project_id).all()
        ]))

        if project_paper_ids:
            papers = db.query(ResearchPaper).filter(ResearchPaper.id.in_(project_paper_ids)).all()
            from app.services.metadata_extractor import MetadataExtractor
            for p in papers:
                full_txt = getattr(p, 'full_text', '') or ''
                fresh_meta = MetadataExtractor.extract(title=p.title, abstract=p.abstract, full_text=full_txt)
                p.keywords = fresh_meta.get("keywords", [])
                p.algorithms = fresh_meta.get("algorithms", [])
                p.datasets = fresh_meta.get("datasets", [])
                p.methodologies = fresh_meta.get("methodologies", [])
                p.application_domains = fresh_meta.get("application_domains", [])
                p.metrics = fresh_meta.get("metrics", [])
                p.tasks = fresh_meta.get("tasks", [])
                p.applications = fresh_meta.get("applications", [])
                p.keyword_details = fresh_meta.get("keyword_details", [])
                p.algorithm_details = fresh_meta.get("algorithm_details", [])
                p.dataset_details = fresh_meta.get("dataset_details", [])
                p.methodology_details = fresh_meta.get("methodology_details", [])
            db.commit()

        logger.info(f"Successfully re-indexed research project id={project_id} across {len(project_paper_ids)} assigned papers.")
        return cls.analyze_project(project_id=project_id, db=db, refresh=True)

