import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.academic_manuscript_schema import (
    ManuscriptGenerateResponse,
    ManuscriptSaveVersionRequest,
    ManuscriptVersionItem
)
from app.services.academic_manuscript_service import AcademicManuscriptService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/projects",
    tags=["Evidence-Grounded Academic Manuscript Generator"]
)


@router.get(
    "/{project_id}/academic-manuscript",
    response_model=ManuscriptGenerateResponse,
    status_code=status.HTTP_200_OK
)
def get_project_manuscript(
    project_id: int = Path(..., description="ID of the research project"),
    db: Session = Depends(get_db)
):
    """
    Retrieve or auto-generate evidence-grounded 29-section academic manuscript draft.
    """
    try:
        return AcademicManuscriptService.get_or_generate_manuscript(db, project_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting manuscript for project {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get academic manuscript: {str(e)}"
        )


@router.post(
    "/{project_id}/academic-manuscript/generate",
    response_model=ManuscriptGenerateResponse,
    status_code=status.HTTP_200_OK
)
def generate_fresh_manuscript(
    project_id: int = Path(..., description="ID of the research project"),
    db: Session = Depends(get_db)
):
    """
    Re-generate fresh 29-section academic manuscript draft from current project evidence.
    """
    try:
        return AcademicManuscriptService.generate_fresh_manuscript(db, project_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating fresh manuscript for project {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate fresh manuscript: {str(e)}"
        )


@router.post(
    "/{project_id}/academic-manuscript/versions",
    response_model=ManuscriptGenerateResponse,
    status_code=status.HTTP_201_CREATED
)
def save_manuscript_version(
    req: ManuscriptSaveVersionRequest,
    project_id: int = Path(..., description="ID of the research project"),
    db: Session = Depends(get_db)
):
    """
    Save student revisions as a new manuscript version. Non-destructive to empirical DB results.
    """
    try:
        return AcademicManuscriptService.save_manuscript_version(db, project_id, req)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving manuscript version for project {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save manuscript version: {str(e)}"
        )


@router.get(
    "/{project_id}/academic-manuscript/versions",
    response_model=List[ManuscriptVersionItem],
    status_code=status.HTTP_200_OK
)
def get_manuscript_versions(
    project_id: int = Path(..., description="ID of the research project"),
    db: Session = Depends(get_db)
):
    """
    List all saved versions of the academic manuscript.
    """
    try:
        return AcademicManuscriptService.get_manuscript_versions(db, project_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting manuscript versions for project {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get manuscript versions: {str(e)}"
        )


@router.get(
    "/{project_id}/academic-manuscript/export",
    status_code=status.HTTP_200_OK
)
def export_academic_manuscript(
    project_id: int = Path(..., description="ID of the research project"),
    format: str = Query("markdown", description="Export format: markdown | pdf | docx | json"),
    db: Session = Depends(get_db)
):
    """
    Export academic manuscript in Markdown, PDF, DOCX, or JSON format.
    """
    try:
        return AcademicManuscriptService.export_manuscript(db, project_id, format)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting manuscript for project {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export manuscript: {str(e)}"
        )
