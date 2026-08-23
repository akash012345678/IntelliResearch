import logging
from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.research_journey_schema import ResearchJourneyResponse
from app.services.research_journey_service import ResearchJourneyService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/projects",
    tags=["Unified Student Research Journey & Workflow"]
)


@router.get(
    "/{project_id}/research-journey",
    response_model=ResearchJourneyResponse,
    status_code=status.HTTP_200_OK
)
def get_project_research_journey(
    project_id: int = Path(..., description="ID of the research project"),
    db: Session = Depends(get_db)
):
    """
    Retrieve unified student research journey state, 10-stage progress, next-action recommendation, and milestone feed.
    Read-only aggregation over existing project intelligence.
    """
    try:
        return ResearchJourneyService.get_research_journey(db, project_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching research journey for project {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch research journey: {str(e)}"
        )
