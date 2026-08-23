from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.project_report_schema import ProjectResearchReportResponse
from app.services.project_research_report_service import ProjectResearchReportService

router = APIRouter(prefix="/projects", tags=["Project Research Reports"])


@router.get(
    "/{project_id}/research-report",
    response_model=ProjectResearchReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Project-Scoped Research Report & Evidence Traceability"
)
def get_project_research_report(
    project_id: int,
    include_proposals: bool = Query(True, description="Include project research proposal summaries"),
    include_relationships: bool = Query(True, description="Include paper-to-paper relationship analytics"),
    include_gaps: bool = Query(True, description="Include project research gaps"),
    include_directions: bool = Query(True, description="Include candidate research directions"),
    db: Session = Depends(get_db)
):
    """
    Generate ONE consolidated project-level Research Report and Evidence Traceability chain
    based ONLY on papers assigned to the specified Research Project via ProjectPaper.
    Performs 0 database writes and 0 global index mutations.
    """
    return ProjectResearchReportService.generate_project_report(
        project_id=project_id,
        db=db,
        include_proposals=include_proposals,
        include_relationships=include_relationships,
        include_gaps=include_gaps,
        include_directions=include_directions
    )


@router.get(
    "/{project_id}/research-report/export",
    summary="Export Project Research Report in Markdown, JSON, or PDF format"
)
def export_project_research_report(
    project_id: int,
    format: str = Query("markdown", description="Export format: 'markdown', 'md', 'json', or 'pdf'"),
    include_proposals: bool = Query(True, description="Include proposal summaries in export"),
    include_relationships: bool = Query(True, description="Include paper relationships in export"),
    include_gaps: bool = Query(True, description="Include research gaps in export"),
    include_directions: bool = Query(True, description="Include research directions in export"),
    db: Session = Depends(get_db)
):
    """
    Export the consolidated Project Research Report into downloadable Markdown (.md),
    JSON (.json), or PDF (.pdf) file format. READ-ONLY operation.
    """
    fmt = format.lower().strip()
    if fmt not in ("md", "markdown", "json", "pdf"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported export format '{format}'. Supported formats: 'markdown', 'json', 'pdf'."
        )

    # Generate full report
    report = ProjectResearchReportService.generate_project_report(
        project_id=project_id,
        db=db,
        include_proposals=include_proposals,
        include_relationships=include_relationships,
        include_gaps=include_gaps,
        include_directions=include_directions
    )

    filename = ProjectResearchReportService.get_export_filename(fmt, project_id)

    if fmt in ("md", "markdown"):
        content = ProjectResearchReportService.export_report_to_markdown(report)
        return Response(
            content=content.encode("utf-8"),
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    elif fmt == "json":
        content = ProjectResearchReportService.export_report_to_json(report)
        return Response(
            content=content.encode("utf-8"),
            media_type="application/json; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    elif fmt == "pdf":
        pdf_bytes = ProjectResearchReportService.export_report_to_pdf(report)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
