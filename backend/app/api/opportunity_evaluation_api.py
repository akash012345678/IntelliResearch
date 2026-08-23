import logging
from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.opportunity_evaluation_schema import OpportunityEvaluationResponse
from app.services.research_opportunity_evaluation_service import ResearchOpportunityEvaluationService

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Research Opportunity Feasibility & Evaluation"]
)


@router.get(
    "/research-directions/{direction_id}/evaluate",
    response_model=OpportunityEvaluationResponse,
    status_code=status.HTTP_200_OK
)
def evaluate_global_opportunity(
    direction_id: str = Path(..., description="Unique ID of the candidate research direction or gap"),
    db: Session = Depends(get_db)
):
    """
    Evaluate evidence strength, feasibility, build steps, dataset considerations,
    experiment plans, and scorecard for a global research opportunity direction.
    Read-only service.
    """
    try:
        logger.info(f"API GET /api/research-directions/{direction_id}/evaluate called")
        return ResearchOpportunityEvaluationService.evaluate_opportunity(
            db=db,
            direction_id=direction_id,
            project_id=None
        )
    except Exception as e:
        logger.error(f"Error evaluating opportunity {direction_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate research opportunity: {str(e)}"
        )


@router.get(
    "/projects/{project_id}/research-directions/{direction_id}/evaluate",
    response_model=OpportunityEvaluationResponse,
    status_code=status.HTTP_200_OK
)
def evaluate_project_opportunity(
    project_id: int = Path(..., description="ID of the research project"),
    direction_id: str = Path(..., description="Unique ID of the candidate research direction within the project"),
    db: Session = Depends(get_db)
):
    """
    Evaluate evidence strength, feasibility, build steps, dataset considerations,
    experiment plans, and scorecard for a project-scoped research opportunity direction.
    Read-only service — strictly uses papers assigned to the project.
    """
    try:
        logger.info(f"API GET /api/projects/{project_id}/research-directions/{direction_id}/evaluate called")
        return ResearchOpportunityEvaluationService.evaluate_opportunity(
            db=db,
            direction_id=direction_id,
            project_id=project_id
        )
    except Exception as e:
        logger.error(f"Error evaluating project opportunity {direction_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate project research opportunity: {str(e)}"
        )
