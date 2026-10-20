import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.project_model import ResearchExperiment
from app.schemas.results_analysis_schema import (
    SingleExperimentAnalysisResponse,
    ProjectResultsAnalysisSummaryResponse
)
from app.services.research_results_analysis_service import ResearchResultsAnalysisService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/projects",
    tags=["Research Results Analysis & Evidence Engine"]
)


@router.get(
    "/{project_id}/results-analysis",
    response_model=ProjectResultsAnalysisSummaryResponse,
    status_code=status.HTTP_200_OK
)
def get_project_results_analysis(
    project_id: int = Path(..., description="ID of the research project"),
    direction_id: Optional[str] = Query(None, description="Optional Opportunity/Direction ID to scope analysis"),
    db: Session = Depends(get_db)
):
    """
    Retrieve project-level empirical results analysis, metric trade-offs, hypothesis assessment, and safe conclusion.
    Read-only intelligence layer over student-entered experiment records.
    """
    try:
        return ResearchResultsAnalysisService.get_project_results_analysis(db, project_id, direction_id=direction_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating results analysis for project {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate results analysis: {str(e)}"
        )


@router.get(
    "/{project_id}/experiments/{experiment_id}/results-analysis",
    response_model=SingleExperimentAnalysisResponse,
    status_code=status.HTTP_200_OK
)
def get_single_experiment_analysis(
    project_id: int = Path(..., description="ID of the research project"),
    experiment_id: int = Path(..., description="ID of the experiment"),
    db: Session = Depends(get_db)
):
    """
    Retrieve detailed analysis for a single research experiment.
    """
    try:
        exp = db.query(ResearchExperiment).filter(
            ResearchExperiment.id == experiment_id,
            ResearchExperiment.project_id == project_id
        ).first()
        if not exp:
            raise HTTPException(status_code=404, detail=f"Experiment {experiment_id} not found in project {project_id}")

        return ResearchResultsAnalysisService._analyze_single_experiment(exp)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching experiment analysis {experiment_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch experiment analysis: {str(e)}"
        )


@router.get(
    "/{project_id}/results-analysis/conclusion",
    status_code=status.HTTP_200_OK
)
def get_project_safe_conclusion(
    project_id: int = Path(..., description="ID of the research project"),
    db: Session = Depends(get_db)
):
    """
    Retrieve plain-language evidence-grounded conclusion and next steps guidance.
    """
    try:
        summary = ResearchResultsAnalysisService.get_project_results_analysis(db, project_id)
        return {
            "project_id": project_id,
            "overall_conclusion": summary.project_overall_conclusion,
            "decision_guidance": summary.decision_guidance,
            "has_recorded_results": summary.has_recorded_results
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching safe conclusion for project {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch safe conclusion: {str(e)}"
        )
