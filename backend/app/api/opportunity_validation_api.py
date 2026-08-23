import logging
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.opportunity_validation_schema import (
    OpportunityValidationResponse,
    LiteratureSearchRequest,
    LiteratureSearchResponse
)
from app.services.research_idea_validation_service import ResearchIdeaValidationService

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Research Idea Validation & Literature Expansion"]
)


@router.get(
    "/research-directions/{direction_id}/validate",
    response_model=OpportunityValidationResponse,
    status_code=status.HTTP_200_OK
)
def validate_global_opportunity(
    direction_id: str = Path(..., description="Unique ID of the candidate research direction or gap"),
    db: Session = Depends(get_db)
):
    """
    Validate a global research direction against indexed collection evidence,
    generate literature search queries, evaluate potential overlap, and suggest refinement areas.
    Read-only service.
    """
    try:
        logger.info(f"API GET /api/research-directions/{direction_id}/validate called")
        return ResearchIdeaValidationService.validate_opportunity(
            db=db,
            direction_id=direction_id,
            project_id=None
        )
    except Exception as e:
        logger.error(f"Error validating opportunity {direction_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate research opportunity: {str(e)}"
        )


@router.get(
    "/projects/{project_id}/research-directions/{direction_id}/validate",
    response_model=OpportunityValidationResponse,
    status_code=status.HTTP_200_OK
)
def validate_project_opportunity(
    project_id: int = Path(..., description="ID of the research project"),
    direction_id: str = Path(..., description="Unique ID of the candidate research direction within the project"),
    db: Session = Depends(get_db)
):
    """
    Validate a project-scoped research direction against project-assigned papers,
    generate literature search queries, evaluate potential overlap, and suggest refinement areas.
    Read-only service — strictly uses papers assigned to the project.
    """
    try:
        logger.info(f"API GET /api/projects/{project_id}/research-directions/{direction_id}/validate called")
        return ResearchIdeaValidationService.validate_opportunity(
            db=db,
            direction_id=direction_id,
            project_id=project_id
        )
    except Exception as e:
        logger.error(f"Error validating project opportunity {direction_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate project research opportunity: {str(e)}"
        )


@router.post(
    "/research-directions/literature-search",
    response_model=LiteratureSearchResponse,
    status_code=status.HTTP_200_OK
)
def search_literature(
    payload: LiteratureSearchRequest,
    db: Session = Depends(get_db)
):
    """
    Execute a literature search query against local semantic collection index.
    Returns ranked result list with relevance explanations.
    """
    try:
        logger.info(f"API POST /api/research-directions/literature-search called query='{payload.query}'")
        return ResearchIdeaValidationService.search_literature(
            db=db,
            query=payload.query,
            top_k=payload.top_k
        )
    except Exception as e:
        logger.error(f"Error executing literature search for query '{payload.query}': {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute literature search: {str(e)}"
        )
