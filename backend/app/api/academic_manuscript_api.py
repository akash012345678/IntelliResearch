import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.academic_manuscript_schema import (
    ManuscriptGenerateResponse,
    ManuscriptSaveVersionRequest,
    ManuscriptVersionItem,
    ManuscriptVersionCompareResponse
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
    Retrieve or auto-generate evidence-grounded 44-section academic manuscript thesis draft.
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
    Re-generate fresh 44-section academic manuscript draft from current project evidence.
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


@router.get(
    "/{project_id}/academic-manuscript/diagnostics",
    status_code=status.HTTP_200_OK
)
def get_manuscript_diagnostics(
    project_id: int = Path(..., description="ID of the research project"),
    db: Session = Depends(get_db)
):
    """
    Get diagnostic report of manuscript sections, completeness, and source trace.
    """
    try:
        return AcademicManuscriptService.get_manuscript_diagnostics(db, project_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting manuscript diagnostics for project {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get manuscript diagnostics: {str(e)}"
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


@router.post(
    "/{project_id}/academic-manuscript/versions/{version_number}/restore",
    response_model=ManuscriptGenerateResponse,
    status_code=status.HTTP_200_OK
)
def restore_manuscript_version(
    project_id: int = Path(..., description="ID of the research project"),
    version_number: int = Path(..., description="Version number to restore"),
    db: Session = Depends(get_db)
):
    """
    Restore a previously saved manuscript version as a new active version.
    """
    try:
        return AcademicManuscriptService.restore_manuscript_version(db, project_id, version_number)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring manuscript version {version_number} for project {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore manuscript version: {str(e)}"
        )


@router.get(
    "/{project_id}/academic-manuscript/versions/compare",
    response_model=ManuscriptVersionCompareResponse,
    status_code=status.HTTP_200_OK
)
def compare_manuscript_versions(
    project_id: int = Path(..., description="ID of the research project"),
    v1: int = Query(..., description="First version number"),
    v2: int = Query(..., description="Second version number"),
    db: Session = Depends(get_db)
):
    """
    Compare two manuscript versions section by section.
    """
    try:
        return AcademicManuscriptService.compare_manuscript_versions(db, project_id, v1, v2)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing manuscript versions for project {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare manuscript versions: {str(e)}"
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
        from fastapi.responses import Response
        from app.models.project_model import ResearchProject
        from app.services.academic_docx_engine import AcademicDocxEngine
        from app.services.academic_report_pdf_engine import AcademicReportPdfEngine
        from app.services.research_results_analysis_service import ResearchResultsAnalysisService

        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"Research project {project_id} not found")

        fmt = format.lower()
        manuscript_res = AcademicManuscriptService.get_or_generate_manuscript(db, project_id)
        assoc_papers = project.project_papers or []
        papers = [assoc.paper for assoc in assoc_papers if assoc.paper]
        results_summary = ResearchResultsAnalysisService.get_project_results_analysis(db, project_id)

        if fmt == "pdf":
            proposal = project.proposals[-1] if project.proposals else None
            plan = project.saved_directions[0] if project.saved_directions else None
            pdf_engine = AcademicReportPdfEngine(
                report=project,
                project=project,
                papers=papers,
                proposal=proposal,
                plan=plan,
                experiments=project.experiments or [],
                results_analysis=results_summary.model_dump() if hasattr(results_summary, "model_dump") else {},
                manuscript=manuscript_res,
                db=db
            )
            pdf_bytes = pdf_engine.generate_pdf()
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=Academic_Manuscript_Project_{project_id}.pdf"}
            )
        elif fmt == "docx":
            docx_bytes = AcademicDocxEngine.generate_docx(manuscript_res, project, papers, results_summary)
            return Response(
                content=docx_bytes,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={"Content-Disposition": f"attachment; filename=Academic_Manuscript_Project_{project_id}.docx"}
            )
        else:
            return AcademicManuscriptService.export_manuscript(db, project_id, fmt)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting manuscript for project {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export manuscript: {str(e)}"
        )

