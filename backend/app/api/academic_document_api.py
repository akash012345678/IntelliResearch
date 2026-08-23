import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Body, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.academic_document_schema import (
    DocumentFormatConfig,
    DocumentValidationResponse,
    DocumentPreviewResponse
)
from app.services.academic_document_validator import AcademicDocumentValidator
from app.services.academic_document_service import AcademicDocumentService
from app.services.submission_package_service import SubmissionPackageService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/projects",
    tags=["Academic Document Formatting & Submission Package"]
)


@router.get(
    "/{project_id}/academic-document/validate",
    response_model=DocumentValidationResponse,
    status_code=status.HTTP_200_OK
)
def validate_academic_document(
    project_id: int = Path(..., description="ID of the research project"),
    db: Session = Depends(get_db)
):
    """
    Validate document for placeholder strings, broken citation links, result mismatches, and structural completeness.
    """
    try:
        return AcademicDocumentValidator.validate_document(db, project_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating document for project {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate document: {str(e)}"
        )


@router.post(
    "/{project_id}/academic-document/preview",
    response_model=DocumentPreviewResponse,
    status_code=status.HTTP_200_OK
)
def get_document_preview(
    project_id: int = Path(..., description="ID of the research project"),
    config: Optional[DocumentFormatConfig] = Body(None),
    db: Session = Depends(get_db)
):
    """
    Generate page-by-page interactive document preview layout with TOC, lists of figures/tables, and appendices.
    """
    try:
        return AcademicDocumentService.get_document_preview(db, project_id, config)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating document preview for project {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate document preview: {str(e)}"
        )


@router.get(
    "/{project_id}/submission-package",
    status_code=status.HTTP_200_OK
)
def download_submission_package(
    project_id: int = Path(..., description="ID of the research project"),
    db: Session = Depends(get_db)
):
    """
    Generate and download the complete final submission package ZIP archive containing /paper/, /evidence/, /references/, and /report/.
    """
    try:
        return SubmissionPackageService.generate_submission_package_zip(db, project_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating submission package for project {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate submission package: {str(e)}"
        )
