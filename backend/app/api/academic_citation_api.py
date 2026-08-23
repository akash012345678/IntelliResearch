import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.citation_schema import (
    ReferenceItem,
    AcademicQualityResponse
)
from app.services.academic_citation_service import AcademicCitationService
from app.services.academic_quality_service import AcademicQualityService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/projects",
    tags=["Academic Citation & Quality Engine"]
)


@router.get(
    "/{project_id}/academic-manuscript/citations",
    response_model=List[ReferenceItem],
    status_code=status.HTTP_200_OK
)
def get_project_citations(
    project_id: int = Path(..., description="ID of the research project"),
    db: Session = Depends(get_db)
):
    """
    Retrieve project references formatted in IEEE, APA, and Harvard styles without metadata fabrication.
    """
    try:
        return AcademicCitationService.get_project_references(db, project_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting citations for project {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get citations: {str(e)}"
        )


@router.get(
    "/{project_id}/academic-manuscript/quality",
    response_model=AcademicQualityResponse,
    status_code=status.HTTP_200_OK
)
def get_manuscript_quality(
    project_id: int = Path(..., description="ID of the research project"),
    db: Session = Depends(get_db)
):
    """
    Audit manuscript citation traceability, metric consistency against DB ExperimentResult records, and novelty warnings.
    """
    try:
        return AcademicQualityService.get_manuscript_quality(db, project_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running quality audit for project {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run quality audit: {str(e)}"
        )


@router.post(
    "/{project_id}/academic-manuscript/validate",
    response_model=AcademicQualityResponse,
    status_code=status.HTTP_200_OK
)
def validate_manuscript(
    project_id: int = Path(..., description="ID of the research project"),
    db: Session = Depends(get_db)
):
    """
    Re-evaluate quality audit and metric consistency check for current project manuscript draft.
    """
    try:
        return AcademicQualityService.get_manuscript_quality(db, project_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating manuscript for project {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate manuscript: {str(e)}"
        )
