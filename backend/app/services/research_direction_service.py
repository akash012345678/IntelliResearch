import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from app.schemas.research_direction_schema import (
    ResearchDirection,
    ResearchDirectionEvidence,
    SupportingPaper,
    CandidateAlgorithm,
    CandidateDataset,
    CandidateMethodology,
    ResearchDirectionResponse
)
from app.services.research_gap_service import ResearchGapService
from app.services.global_research_intelligence_service import GlobalResearchIntelligenceService

logger = logging.getLogger(__name__)

COLLECTION_DISCLAIMER = (
    "All findings are derived from the currently indexed research-paper collection and "
    "may change as additional papers are added. Research-gap and research-direction outputs "
    "represent collection-based analytical opportunities and do not establish global academic novelty."
)

DIRECTION_DISCLAIMER = (
    "This research direction is derived from the currently indexed research-paper collection. "
    "It represents a potential collection-based opportunity and does not establish global academic novelty."
)


class ResearchDirectionService:
    """
    Service to synthesize multi-signal collection evidence (gaps, semantic similarities,
    knowledge graph links, and underrepresented entities) into structured, actionable
    research proposal directions.
    """

    @classmethod
    def generate_directions(cls, db: Session, top_k: int = 10) -> ResearchDirectionResponse:
        """
        Generate ranked actionable research directions from indexed collection evidence.

        Args:
            db: SQLAlchemy Session connected to Supabase PostgreSQL.
            top_k: Maximum number of research directions to return (1 <= top_k <= 20).

        Returns:
            ResearchDirectionResponse containing directions and collection disclaimer.
        """
        logger.info(f"Generating top {top_k} research directions from collection evidence...")

        # 1. Fetch collection intelligence & research gap outputs
        intelligence_svc = GlobalResearchIntelligenceService()
        analysis = intelligence_svc.analyze_collection(db_session=db)
        gap_svc = ResearchGapService()
        gaps = gap_svc.detect_gaps(db_session=db, top_k=20)


        paper_landscape = analysis.get("paper_landscape", []) if isinstance(analysis, dict) else getattr(analysis, "paper_landscape", [])
        total_papers = analysis.get("collection_summary", {}).get("total_papers", 0) if isinstance(analysis, dict) else (analysis.collection_summary.total_papers if hasattr(analysis, "collection_summary") else 0)

        if total_papers == 0:
            return ResearchDirectionResponse(
                total_directions=0,
                directions=[],
                collection_disclaimer=COLLECTION_DISCLAIMER
            )

        paper_map = {}
        for p in paper_landscape:
            p_id = p.get("paper_id") if isinstance(p, dict) else getattr(p, "paper_id")
            paper_map[p_id] = p

        directions: List[ResearchDirection] = []
        seen_pairs = set()

        for gap in gaps:
            gap_src_id = gap.get("source_paper_id") if isinstance(gap, dict) else getattr(gap, "source_paper_id")
            gap_target_label = gap.get("target_label") if isinstance(gap, dict) else getattr(gap, "target_label")
            gap_target_type = gap.get("target_type") if isinstance(gap, dict) else getattr(gap, "target_type")
            gap_ev = gap.get("evidence", {}) if isinstance(gap, dict) else getattr(gap, "evidence")
            gap_explanation = gap.get("explanation", []) if isinstance(gap, dict) else getattr(gap, "explanation")

            gap_score = gap_ev.get("gap_score", 0.0) if isinstance(gap_ev, dict) else getattr(gap_ev, "gap_score", 0.0)
            semantic_evidence = gap_ev.get("semantic_evidence", 0.0) if isinstance(gap_ev, dict) else getattr(gap_ev, "semantic_evidence", 0.0)
            link_prediction_score = gap_ev.get("link_prediction_score", 0.0) if isinstance(gap_ev, dict) else getattr(gap_ev, "link_prediction_score", 0.0)
            underrepresentation_score = gap_ev.get("underrepresentation_score", 0.0) if isinstance(gap_ev, dict) else getattr(gap_ev, "underrepresentation_score", 0.0)

            source_paper = paper_map.get(gap_src_id)
            if not source_paper:
                continue

            pair_key = (gap_src_id, gap_target_label.lower())
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            # Signal check: Must have at least 2 active signals (> 0.1)
            active_signals = [
                1 for val in [
                    gap_score,
                    semantic_evidence,
                    link_prediction_score,
                    underrepresentation_score
                ] if val > 0.1
            ]
            if len(active_signals) < 2:
                continue

            dir_score = round(
                0.35 * gap_score +
                0.25 * semantic_evidence +
                0.20 * link_prediction_score +
                0.20 * underrepresentation_score, 2
            )
            dir_score = round(min(1.0, max(0.0, dir_score)), 2)

            if dir_score >= 0.75:
                confidence = "High"
            elif dir_score >= 0.50:
                confidence = "Moderate"
            else:
                confidence = "Low"

            p_title = source_paper.get("title") if isinstance(source_paper, dict) else getattr(source_paper, "title")
            p_algos = source_paper.get("algorithms", []) if isinstance(source_paper, dict) else getattr(source_paper, "algorithms", [])
            p_datasets = source_paper.get("datasets", []) if isinstance(source_paper, dict) else getattr(source_paper, "datasets", [])
            p_methodologies = source_paper.get("methodologies", []) if isinstance(source_paper, dict) else getattr(source_paper, "methodologies", [])
            p_domains = source_paper.get("application_domains", []) if isinstance(source_paper, dict) else getattr(source_paper, "application_domains", [])
            p_keywords = source_paper.get("keywords", []) if isinstance(source_paper, dict) else getattr(source_paper, "keywords", [])

            primary_algo = p_algos[0] if p_algos else "existing techniques"
            domain_name = p_domains[0] if p_domains else "the domain"

            supporting_papers: List[SupportingPaper] = [
                SupportingPaper(
                    paper_id=gap_src_id,
                    title=p_title,
                    role=f"Provides primary domain context ({domain_name}) and baseline concepts."
                )
            ]

            for other_p in paper_landscape:
                op_id = other_p.get("paper_id") if isinstance(other_p, dict) else getattr(other_p, "paper_id")
                if op_id == gap_src_id:
                    continue
                op_title = other_p.get("title") if isinstance(other_p, dict) else getattr(other_p, "title")
                op_keywords = other_p.get("keywords", []) if isinstance(other_p, dict) else getattr(other_p, "keywords", [])
                op_algos = other_p.get("algorithms", []) if isinstance(other_p, dict) else getattr(other_p, "algorithms", [])
                op_datasets = other_p.get("datasets", []) if isinstance(other_p, dict) else getattr(other_p, "datasets", [])
                op_methods = other_p.get("methodologies", []) if isinstance(other_p, dict) else getattr(other_p, "methodologies", [])
                op_domains = other_p.get("application_domains", []) if isinstance(other_p, dict) else getattr(other_p, "application_domains", [])

                all_op_concepts = [c.lower() for c in (op_keywords + op_algos + op_datasets + op_methods + op_domains)]
                if gap_target_label.lower() in all_op_concepts:
                    supporting_papers.append(SupportingPaper(
                        paper_id=op_id,
                        title=op_title,
                        role=f"Provides empirical evidence for concept '{gap_target_label}'."
                    ))
                    if len(supporting_papers) >= 3:
                        break

            supp_concepts_set = set(p_keywords[:3])
            supp_concepts_set.add(gap_target_label)
            supporting_concepts = list(supp_concepts_set)

            cand_algos: List[CandidateAlgorithm] = []
            for algo in p_algos:
                cand_algos.append(CandidateAlgorithm(
                    name=algo,
                    supporting_paper_count=1,
                    reason=f"Baseline algorithm utilized in Paper ID {gap_src_id}."
                ))
            if gap_target_type == "ALGORITHM" and gap_target_label not in [a.name for a in cand_algos]:
                cand_algos.append(CandidateAlgorithm(
                    name=gap_target_label,
                    supporting_paper_count=1,
                    reason="Identified underrepresented target algorithm candidate."
                ))

            cand_datasets: List[CandidateDataset] = []
            for ds in p_datasets:
                cand_datasets.append(CandidateDataset(
                    name=ds,
                    supporting_paper_count=1,
                    reason=f"Benchmark dataset evaluated in Paper ID {gap_src_id}."
                ))
            if gap_target_type == "DATASET" and gap_target_label not in [d.name for d in cand_datasets]:
                cand_datasets.append(CandidateDataset(
                    name=gap_target_label,
                    supporting_paper_count=1,
                    reason="Identified target dataset candidate for cross-evaluation."
                ))

            cand_methodologies: List[CandidateMethodology] = []
            for m in p_methodologies:
                cand_methodologies.append(CandidateMethodology(
                    name=m,
                    paper_count=1,
                    coverage_percentage=round((1 / max(1, total_papers)) * 100, 1)
                ))

            research_problem = (
                f"Current papers in the collection investigate {domain_name} primarily using {primary_algo}, "
                f"while integration with {gap_target_label} ({gap_target_type.lower()}) remains underrepresented."
            )

            motivation = (
                f"The indexed collection contains {len(supporting_papers)} paper(s) referencing related concepts, "
                f"but combination of '{primary_algo}' and '{gap_target_label}' has a gap score of {gap_score}."
            )

            missing_aspect = (
                f"Integration of {gap_target_type.lower()} '{gap_target_label}' with baseline methodology "
                f"in {domain_name} is underrepresented across the current collection."
            )

            proposed_direction = (
                f"Investigate whether combining {primary_algo} with {gap_target_label} could explore "
                f"potential methodology enhancements for {domain_name}."
            )

            title = f"Explore {primary_algo} + {gap_target_label} for {domain_name}"
            cov_pct = round((len(supporting_papers) / max(1, total_papers)) * 100, 1)

            direction_obj = ResearchDirection(
                direction_id=f"dir_{len(directions) + 1}",
                title=title,
                research_problem=research_problem,
                motivation=motivation,
                existing_evidence=gap_explanation,
                missing_aspect=missing_aspect,
                proposed_direction=proposed_direction,
                supporting_papers=supporting_papers,
                supporting_concepts=supporting_concepts,
                candidate_algorithms=cand_algos,
                candidate_datasets=cand_datasets,
                candidate_methodologies=cand_methodologies,
                evidence=ResearchDirectionEvidence(
                    gap_score=gap_score,
                    semantic_evidence=semantic_evidence,
                    link_prediction_score=link_prediction_score,
                    collection_coverage=cov_pct,
                    underrepresentation_score=underrepresentation_score
                ),
                direction_score=dir_score,
                confidence=confidence,
                disclaimer=DIRECTION_DISCLAIMER
            )
            directions.append(direction_obj)

        # 3. Sort directions deterministically by direction_score DESC, direction_id ASC
        directions.sort(key=lambda d: (-d.direction_score, d.direction_id))
        final_directions = directions[:top_k]

        return ResearchDirectionResponse(
            total_directions=len(final_directions),
            directions=final_directions,
            collection_disclaimer=COLLECTION_DISCLAIMER
        )
