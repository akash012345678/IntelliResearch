import logging
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.project_intelligence_schema import ProjectResearchIntelligenceResponse
from app.services.project_intelligence_service import ProjectIntelligenceService

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Project Research Intelligence"]
)


@router.get(
    "/projects/{project_id}/research-intelligence",
    response_model=ProjectResearchIntelligenceResponse,
    status_code=status.HTTP_200_OK
)
def get_project_research_intelligence(
    project_id: int,
    max_relationships: int = Query(10, ge=1, le=50, description="Max pairwise paper relationships to return"),
    max_gaps: int = Query(10, ge=1, le=50, description="Max research gaps to return"),
    max_underrepresented: int = Query(10, ge=1, le=50, description="Max underrepresented concepts to return"),
    max_directions: int = Query(5, ge=1, le=20, description="Max candidate research directions to return"),
    db: Session = Depends(get_db)
):
    """
    Retrieve project-scoped research intelligence for papers explicitly assigned to the project.
    Strictly READ-ONLY with 0 side effects on global database, FAISS, or global graph.
    """
    try:
        return ProjectIntelligenceService.analyze_project(
            project_id=project_id,
            db=db,
            max_relationships=max_relationships,
            max_gaps=max_gaps,
            max_underrepresented=max_underrepresented,
            max_directions=max_directions
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error computing project intelligence for project {project_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to compute project research intelligence: {str(e)}"
        )
