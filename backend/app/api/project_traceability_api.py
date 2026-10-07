import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.project_traceability_schema import ProjectTraceabilityResponse
from app.services.project_traceability_service import ProjectTraceabilityService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/projects/{project_id}/traceability",
    response_model=ProjectTraceabilityResponse,
    summary="Fetch complete end-to-end evidence traceability chains for a research project",
    description="Provides deterministic lineage across Papers, Concepts, Gaps, Opportunities, Plans, Experiments, Results, Proposals, Versions, and Reports."
)
def get_project_traceability(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Get full dynamic project-scoped evidence provenance & lifecycle stage status.
    """
    return ProjectTraceabilityService.get_project_traceability(project_id=project_id, db=db)
