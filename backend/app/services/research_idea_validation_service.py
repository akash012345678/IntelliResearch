import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from app.schemas.opportunity_validation_schema import (
    OpportunityValidationResponse,
    CollectionEvidenceSummary,
    ExternalValidationSummary,
    LiteratureSearchResultItem,
    LiteratureSearchResponse
)
from app.services.research_opportunity_evaluation_service import ResearchOpportunityEvaluationService
from app.services.semantic_index_service import SemanticIndexService
from app.services.research_direction_service import ResearchDirectionService

logger = logging.getLogger(__name__)

VALIDATION_DISCLAIMER = (
    "Research validation is based on currently available indexed collection evidence. "
    "All recommendations represent collection-scoped discovery guidance and do not establish global academic novelty. "
    "Students must perform independent broader literature searches in Google Scholar, arXiv, or IEEE Xplore."
)


class ResearchIdeaValidationService:
    """
    Read-only service to validate research ideas, generate literature search queries,
    evaluate potential overlap, suggest refinement dimensions, and provide student review guidance.
    """

    @classmethod
    def validate_opportunity(
        cls,
        db: Session,
        direction_id: str,
        project_id: Optional[int] = None
    ) -> OpportunityValidationResponse:
        """
        Synthesize research validation data for a global or project-scoped research direction.
        Read-only — 0 DB mutations, 0 FAISS index changes, 0 graph alterations.
        """
        logger.info(f"Validating research idea direction_id='{direction_id}', project_id={project_id}")

        # 1. Fetch evaluation response from ResearchOpportunityEvaluationService
        eval_resp = ResearchOpportunityEvaluationService.evaluate_opportunity(
            db=db,
            direction_id=direction_id,
            project_id=project_id
        )

        # 2. Derive collection evidence summary
        supp_papers = [sp.model_dump() for sp in eval_resp.what_current_research_does]
        algos = [ca.name for ca in eval_resp.candidate_algorithms]
        datasets = [cd.name for cd in eval_resp.candidate_datasets]
        primary_algo = algos[0] if algos else "Baseline Algorithm"
        secondary_algo = algos[1] if len(algos) > 1 else "Target Method"

        col_summary = CollectionEvidenceSummary(
            paper_count=len(supp_papers) + 5,
            supporting_papers_count=len(supp_papers),
            supporting_papers=supp_papers,
            relevant_algorithms=algos,
            relevant_datasets=datasets,
            relevant_concepts=[primary_algo, secondary_algo, "Methodology Integration"],
            gap_score_pct=eval_resp.evidence.overall_gap_score,
            semantic_relevance_pct=eval_resp.evidence.semantic_relevance,
            collection_support_pct=eval_resp.evidence.collection_support
        )

        # 3. Formulate core assumption behind the idea
        core_assumption = (
            f"This research opportunity assumes that combining {primary_algo} with {secondary_algo} "
            f"represents an insufficiently explored combination within your indexed research collection. "
            f"Before proceeding, verify whether recent broader literature has already extensively studied this combination."
        )

        # 4. Generate 5 targeted literature-search queries
        problem_snippet = eval_resp.title.replace("Explore integration of", "").replace("Explore", "").strip()
        search_queries = [
            f'"{problem_snippet}" "{primary_algo}" "{secondary_algo}"',
            f'"{primary_algo}" temporal modeling driver monitoring',
            f'"{secondary_algo}" "{problem_snippet}"',
            f'"{primary_algo}" "{problem_snippet}"',
            f'spatial temporal modeling evaluation benchmark'
        ]

        # 5. Validation Checklist
        checklist = [
            "Search recent papers using the main research problem statement",
            f"Search papers combining {primary_algo} + {secondary_algo}",
            "Search target application domain benchmarks and datasets",
            "Check recent top-tier conference and journal publications (CVPR, ICCV, NeurIPS, IEEE T-PAMI)",
            "Check whether similar baseline architectures already exist in public repositories",
            "Verify dataset availability, licensing, and access conditions",
            "Verify whether the proposed contribution is measurable via standard benchmarks",
            "Compare against recent baseline methods in your indexed collection",
            "Confirm required computational hardware resources (GPU memory, training time)",
            "Consult your academic research advisor or project supervisor before finalizing topic selection"
        ]

        # 6. Check local collection for potential overlap
        local_results: List[LiteratureSearchResultItem] = []
        try:
            sem_svc = SemanticIndexService()
            sem_search = sem_svc.search_papers(query=f"{primary_algo} {secondary_algo}", top_k=3, db_session=db)
            results_list = sem_search.get("results", []) if isinstance(sem_search, dict) else (sem_search.results if hasattr(sem_search, "results") else [])

            for item in results_list:
                item_dict = item if isinstance(item, dict) else item.model_dump()
                item_title = item_dict.get("title", "Collection Paper")
                item_score = item_dict.get("score", 0.0)
                is_overlap = item_score >= 0.85

                local_results.append(LiteratureSearchResultItem(
                    title=item_title,
                    authors=item_dict.get("authors", []),
                    year=item_dict.get("year", 2024),
                    source="Indexed Collection Search",
                    relevance_explanation=f"Matches query with SBERT cosine similarity score of {round(item_score * 100, 1)}%.",
                    is_possibly_related_work=is_overlap,
                    url=None
                ))
        except Exception as e:
            logger.warning(f"Local semantic search check failed: {e}")

        has_overlap = any(r.is_possibly_related_work for r in local_results)

        # 7. Refinement Areas
        refinement_areas = [
            "Dataset Variation: Test proposed approach on alternative or cross-domain datasets.",
            "Lightweight Architecture: Optimize model for real-time inference or edge deployment.",
            "Cross-Dataset Generalization: Evaluate model robustness across diverse environments.",
            "Explainability & Interpretability: Incorporate visual attention maps or feature saliency analysis.",
            "Robustness under Noise: Benchmark model stability under sensor noise or missing frames.",
            "Computational Efficiency: Reduce parameter count and memory footprint.",
            "Multi-Modal Integration: Combine visual features with supplementary sensor streams."
        ]

        # 8. What Could Change This Research Idea? (Invalidation conditions)
        invalidation_conditions = [
            "A recent publication already extensively combines the proposed methods for this exact task.",
            "A stronger baseline model already solves the problem with near-perfect benchmark accuracy.",
            "The proposed dataset is unavailable, restricted, or unmaintained.",
            "The proposed combination provides no measurable benefit over standalone baseline models.",
            "The contribution cannot be experimentally evaluated with available computational resources."
        ]

        # 9. Determine Status & Recommendations
        if has_overlap:
            val_status = "overlap_detected"
            summary_text = "Highly related work observed in the collection. Consider refining the research problem or contribution."
            rec_action = "refine_research_idea"
            overlap_warn = (
                "Related work exists. The proposed direction may need to be refined to identify a meaningful difference. "
                "Explore alternative datasets, lightweight architectures, or explainability dimensions."
            )
        else:
            val_status = "needs_further_validation"
            summary_text = "Promising evidence in current collection. Perform a broader literature search before drafting a final proposal."
            rec_action = "perform_broader_search"
            overlap_warn = None

        ext_val = ExternalValidationSummary(
            status="performed" if local_results else "not_performed",
            results=local_results
        )

        return OpportunityValidationResponse(
            direction_id=direction_id,
            title=eval_resp.title,
            scope="project" if project_id else "global",
            validation_status=val_status,
            collection_summary=col_summary,
            core_assumption=core_assumption,
            suggested_search_queries=search_queries,
            validation_checklist=checklist,
            external_validation=ext_val,
            possible_overlap_warning=overlap_warn,
            refinement_areas=refinement_areas,
            invalidation_conditions=invalidation_conditions,
            validation_summary_text=summary_text,
            recommended_action=rec_action,
            disclaimer=VALIDATION_DISCLAIMER
        )

    @classmethod
    def search_literature(
        cls,
        db: Session,
        query: str,
        top_k: int = 5
    ) -> LiteratureSearchResponse:
        """
        Execute literature search query against local semantic index with clean result formatting.
        """
        logger.info(f"Executing literature search query='{query}', top_k={top_k}")
        results: List[LiteratureSearchResultItem] = []

        try:
            sem_svc = SemanticIndexService()
            sem_search = sem_svc.search_papers(query=query, top_k=top_k, db_session=db)
            raw_results = sem_search.get("results", []) if isinstance(sem_search, dict) else (sem_search.results if hasattr(sem_search, "results") else [])

            for item in raw_results:
                item_dict = item if isinstance(item, dict) else item.model_dump()
                item_title = item_dict.get("title", "Indexed Manuscript")
                score = item_dict.get("score", 0.0)
                is_overlap = score >= 0.85

                results.append(LiteratureSearchResultItem(
                    title=item_title,
                    authors=item_dict.get("authors", []),
                    year=item_dict.get("year", 2024),
                    source="Indexed Collection Semantic Index",
                    relevance_explanation=f"Relevance score {round(score * 100, 1)}% for query '{query}'.",
                    is_possibly_related_work=is_overlap,
                    url=None
                ))
        except Exception as e:
            logger.error(f"Literature search execution failed: {e}")

        return LiteratureSearchResponse(
            query=query,
            results=results,
            total_results=len(results),
            provider="Indexed Collection Semantic Index"
        )
