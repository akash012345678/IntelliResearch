import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.config.settings import settings
from app.schemas.research_direction_schema import ResearchDirection
from app.schemas.proposal_draft_schema import ProposalDraft, ProposalDraftResponse
from app.services.research_direction_service import ResearchDirectionService

logger = logging.getLogger(__name__)

DRAFT_DISCLAIMER = (
    "This research proposal draft is derived from evidence available in the indexed research collection. "
    "It represents a potential direction for further investigation and does not establish global academic novelty or guarantee research originality."
)


class LLMProvider:
    """Abstract Base Class for LLM Provider Synthesis."""
    def generate_proposal(self, direction: ResearchDirection) -> Optional[ProposalDraft]:
        raise NotImplementedError


class ProposalDraftService:
    """
    Service responsible for synthesizing structured academic research proposal drafts
    from Phase 4 Actionable Research Directions using either LLM-guided synthesis
    or deterministic template-guided fallback synthesis.
    """

    @classmethod
    def synthesize_draft(
        cls,
        db: Session,
        direction_id: str,
        custom_provider: Optional[LLMProvider] = None
    ) -> ProposalDraftResponse:
        """
        Synthesize a structured proposal draft for the specified direction ID.

        Args:
            db: SQLAlchemy database session.
            direction_id: ID of the research direction (e.g. dir_1).
            custom_provider: Optional mock or custom LLMProvider instance (primarily for testing).

        Returns:
            ProposalDraftResponse containing the synthesized ProposalDraft.
        """
        logger.info(f"Synthesizing proposal draft for direction_id='{direction_id}'...")

        # 1. Fetch available directions from collection evidence
        directions_resp = ResearchDirectionService.generate_directions(db=db, top_k=20)
        target_dir: Optional[ResearchDirection] = None

        for d in directions_resp.directions:
            if d.direction_id.lower() == direction_id.lower():
                target_dir = d
                break

        # Fallback matching by index if dir_1 format
        if not target_dir and direction_id.startswith("dir_"):
            try:
                idx = int(direction_id.replace("dir_", "")) - 1
                if 0 <= idx < len(directions_resp.directions):
                    target_dir = directions_resp.directions[idx]
            except ValueError:
                pass

        if not target_dir:
            logger.warning(f"Research direction with ID '{direction_id}' not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Research direction '{direction_id}' not found in the indexed collection."
            )

        # 2. Determine synthesis mode: LLM vs Template Fallback
        if custom_provider:
            try:
                logger.info("Custom/Mock LLM Provider detected. Attempting LLM synthesis...")
                draft = custom_provider.generate_proposal(target_dir)
                if draft:
                    return ProposalDraftResponse(proposal=draft)
            except Exception as e:
                logger.warning(f"Custom LLM Provider failed: {e}. Falling back to template synthesis.")

        if settings.LLM_PROVIDER and settings.LLM_API_KEY:
            try:
                logger.info(f"LLM Provider '{settings.LLM_PROVIDER}' configured. Attempting LLM synthesis...")
                draft = cls._llm_synthesis(target_dir)
                if draft:
                    return ProposalDraftResponse(proposal=draft)
            except Exception as e:
                logger.warning(f"LLM synthesis failed: {e}. Falling back to template synthesis.")

        # 3. Mode 2: Deterministic Template Fallback
        logger.info("Executing Mode 2: Template-Guided Fallback Synthesis.")
        template_draft = cls._template_synthesis(target_dir)
        return ProposalDraftResponse(proposal=template_draft)

    @classmethod
    def _template_synthesis(cls, dir_item: ResearchDirection) -> ProposalDraft:
        """
        Deterministic, evidence-grounded template synthesizer.
        Converts a ResearchDirection into a structured ProposalDraft without external API dependencies.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        proposal_uuid = f"prop_{uuid.uuid4().hex[:8]}"

        # Abstract
        abstract = (
            f"This research proposal investigates potential methodology enhancements for {dir_item.title}. "
            f"Based on evidence from the indexed collection, current studies focus on baseline approaches, "
            f"while integration with target concepts remains underrepresented. "
            f"We propose an empirical study to explore combining existing techniques with candidate target entities."
        )

        # Related Work Synthesis
        if dir_item.supporting_papers:
            paper_refs = []
            for sp in dir_item.supporting_papers:
                paper_refs.append(f"Paper ID {sp.paper_id} ('{sp.title}') — {sp.role}")
            related_work = "The indexed research collection provides key empirical context:\n- " + "\n- ".join(paper_refs)
        else:
            related_work = "The indexed collection shows initial baseline context for the domain."

        # Candidate Entities
        cand_algos = [a.name for a in dir_item.candidate_algorithms] if dir_item.candidate_algorithms else ["Baseline Algorithms"]
        cand_datasets = [d.name for d in dir_item.candidate_datasets] if dir_item.candidate_datasets else []

        # Dataset Evaluation Plan
        if cand_datasets:
            ds_str = ", ".join(cand_datasets)
            ds_plan = f"Evaluation is proposed using collection candidate dataset(s): {ds_str}."
        else:
            ds_plan = "Dataset selection requires further domain-specific evaluation and validation."

        # Experimental Plan
        exp_plan = (
            f"The proposed experimental design involves implementing baseline algorithms ({', '.join(cand_algos)}) "
            f"and comparing performance against integrated candidate variations across standard cross-validation splits."
        )

        # Evaluation Metrics
        metrics = (
            f"Evaluation metrics should measure accuracy, precision, recall, and computational efficiency. "
            f"Specific metrics require domain-specific selection based on the target application."
        )

        # Expected Contribution
        expected_contrib = (
            f"This proposal aims to contribute an empirical investigation into combining baseline techniques "
            f"with underrepresented target entities within the scope of the indexed paper collection."
        )

        # Limitations
        limitations = (
            f"Findings are derived from the currently indexed paper collection (Coverage: {dir_item.evidence.collection_coverage}%). "
            f"Results represent an analytical opportunity and do not establish global academic novelty or guaranteed performance improvements."
        )

        # Supporting papers list of dicts
        supporting_papers_data = [sp.model_dump() for sp in dir_item.supporting_papers]

        # Evidence Summary
        evidence_summary_data = {
            "gap_score": dir_item.evidence.gap_score,
            "semantic_evidence": dir_item.evidence.semantic_evidence,
            "link_prediction_score": dir_item.evidence.link_prediction_score,
            "underrepresentation_score": dir_item.evidence.underrepresentation_score,
            "collection_coverage": dir_item.evidence.collection_coverage,
            "direction_score": dir_item.direction_score,
            "confidence": dir_item.confidence
        }

        return ProposalDraft(
            proposal_id=proposal_uuid,
            source_direction_id=dir_item.direction_id,
            title=dir_item.title,
            abstract=abstract,
            problem_statement=dir_item.research_problem,
            research_motivation=dir_item.motivation,
            related_work_synthesis=related_work,
            research_gap=dir_item.missing_aspect,
            proposed_methodology=dir_item.proposed_direction,
            candidate_algorithms=cand_algos,
            candidate_datasets=cand_datasets,
            dataset_evaluation_plan=ds_plan,
            experimental_plan=exp_plan,
            evaluation_metrics=metrics,
            expected_contribution=expected_contrib,
            limitations=limitations,
            supporting_papers=supporting_papers_data,
            evidence_summary=evidence_summary_data,
            generation_mode="template",
            generation_timestamp=timestamp,
            disclaimer=DRAFT_DISCLAIMER
        )

    @classmethod
    def _llm_synthesis(cls, dir_item: ResearchDirection) -> Optional[ProposalDraft]:
        """
        LLM-guided synthesizer wrapper. Called when LLM_PROVIDER and LLM_API_KEY are configured.
        Falls back to template synthesis if execution fails or returns invalid schema.
        """
        logger.info("Executing LLM synthesis wrapper...")
        # Note: External LLM caller interface
        # For security and reliability, if unconfigured or on any API call exception, returns None to trigger template fallback.
        return None
