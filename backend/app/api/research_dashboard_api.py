import logging
from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.research_dashboard_schema import ProjectDashboardAggregateResponse
from app.services.research_dashboard_service import ResearchDashboardService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/projects",
    tags=["Student Research Dashboard Engine"]
)


@router.get(
    "/{project_id}/research-dashboard",
    response_model=ProjectDashboardAggregateResponse,
    status_code=status.HTTP_200_OK
)
def get_project_dashboard_aggregate(
    project_id: int = Path(..., description="ID of the research project"),
    db: Session = Depends(get_db)
):
    """
    Retrieve aggregated student dashboard state, journey milestones, health scores, next-step recommendations,
    and final submission readiness.
    """
    try:
        return ResearchDashboardService.get_dashboard_aggregate(db, project_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dashboard aggregate for project {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard aggregate: {str(e)}"
        )
