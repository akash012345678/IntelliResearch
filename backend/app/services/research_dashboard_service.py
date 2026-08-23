import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.project_model import ResearchProject
from app.schemas.research_dashboard_schema import (
    NextStepRecommendation,
    ProjectHealthSummary,
    SubmissionReadinessItem,
    ProjectDashboardAggregateResponse
)
from app.services.research_journey_service import ResearchJourneyService
from app.services.academic_quality_service import AcademicQualityService
from app.services.academic_document_validator import AcademicDocumentValidator

logger = logging.getLogger(__name__)


class ResearchDashboardService:
    """
    Read-only service that aggregates project journey milestones, health scores, next-step recommendations,
    and final submission readiness for the student dashboard.
    """

    @classmethod
    def get_dashboard_aggregate(cls, db: Session, project_id: int) -> ProjectDashboardAggregateResponse:
        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"Research project {project_id} not found")

        journey = ResearchJourneyService.get_research_journey(db, project_id)
        quality = AcademicQualityService.get_manuscript_quality(db, project_id)
        validation = AcademicDocumentValidator.validate_document(db, project_id)

        current_stage_key = journey.progress.current_stage_key
        current_stage_id_str = f"S{journey.progress.current_stage_id}_{current_stage_key}"
        
        active_stage_item = next((s for s in journey.stages if s.stage_key == current_stage_key), None)
        current_stage_title = active_stage_item.title if active_stage_item else current_stage_key

        # 1. Next Step Recommendation
        next_step_info = cls._compute_next_step(current_stage_key, journey)

        # 2. Health Scores
        health = ProjectHealthSummary(
            evidence_completeness_percentage=quality.evidence_coverage_percentage,
            citation_completeness_percentage=quality.citation_traceability_score,
            experiment_completeness_percentage=quality.result_consistency_score,
            reproducibility_percentage=quality.dataset_verification_score,
            document_readiness_percentage=journey.progress.progress_percentage,
            overall_readiness_score=int((journey.progress.progress_percentage + quality.evidence_coverage_percentage) / 2),
            calculation_explanation="Weighted average of empirical evidence coverage, citation traceability, and document completeness."
        )

        # 3. Submission Readiness Items
        gaps_completed = any(m.key == "gaps" and m.completed for m in journey.milestones)
        experiments_completed = any(m.key == "experiments" and m.completed for m in journey.milestones)
        manuscript_completed = any(m.key == "manuscript" and m.completed for m in journey.milestones)

        readiness_items = [
            SubmissionReadinessItem(
                check_name="Project Literature Papers",
                status="PASSED" if journey.paper_count > 0 else "FAILED",
                badge_text="🟢 PASSED" if journey.paper_count > 0 else "🔴 NO PAPERS",
                explanation=f"{journey.paper_count} papers assigned to project."
            ),
            SubmissionReadinessItem(
                check_name="Research Gap Identification",
                status="PASSED" if gaps_completed else "WARNING",
                badge_text="🟢 PASSED" if gaps_completed else "🟡 PENDING",
                explanation="Collection-scoped research gaps identified." if gaps_completed else "Pending gap identification."
            ),
            SubmissionReadinessItem(
                check_name="Empirical Experiments",
                status="PASSED" if experiments_completed else "WARNING",
                badge_text="🟢 PASSED" if experiments_completed else "🟡 PENDING",
                explanation="Controlled experiments recorded." if experiments_completed else "Pending experiment runs."
            ),
            SubmissionReadinessItem(
                check_name="Academic Manuscript",
                status="PASSED" if manuscript_completed else "FAILED",
                badge_text="🟢 GENERATED" if manuscript_completed else "🔴 NOT GENERATED",
                explanation="29-section academic manuscript synthesized." if manuscript_completed else "Manuscript draft pending."
            ),
            SubmissionReadinessItem(
                check_name="Document Validation",
                status="PASSED" if validation.is_valid_for_submission else "WARNING",
                badge_text="🟢 VALIDATED" if validation.is_valid_for_submission else f"🟡 {validation.errors_count} ERRORS",
                explanation="Structural completeness and placeholder check."
            )
        ]

        completed_milestones = [m.title for m in journey.milestones if m.completed]
        upcoming_milestones = [m.title for m in journey.milestones if not m.completed]

        return ProjectDashboardAggregateResponse(
            project_id=project.id,
            project_title=project.name,
            status=project.status,
            paper_count=journey.paper_count,
            current_stage_id=current_stage_id_str,
            current_stage_title=current_stage_title,
            progress_percentage=journey.progress.progress_percentage,
            next_step=next_step_info,
            health=health,
            submission_readiness=readiness_items,
            completed_milestones=completed_milestones,
            upcoming_milestones=upcoming_milestones
        )

    @classmethod
    def _compute_next_step(cls, current_stage_key: str, journey) -> NextStepRecommendation:
        next_action = journey.next_action

        return NextStepRecommendation(
            stage_id=current_stage_key,
            stage_title=next_action.title,
            recommended_action_title=next_action.title,
            why_this_matters=next_action.why_explanation,
            completed_prerequisites=[m.title for m in journey.milestones if m.completed],
            action_button_label=next_action.action_label,
            target_tab=next_action.target_tab,
            expected_outcome=next_action.description
        )
