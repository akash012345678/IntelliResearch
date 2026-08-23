import logging
from fastapi import APIRouter, Depends, Query, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.research_direction_schema import ResearchDirectionResponse
from app.schemas.proposal_draft_schema import ProposalDraftRequest, ProposalDraftResponse
from app.services.research_direction_service import ResearchDirectionService
from app.services.proposal_export_service import ProposalExportService
from app.services.proposal_draft_service import ProposalDraftService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/research-directions",
    tags=["Actionable Research Directions"]
)


@router.post("/draft", response_model=ProposalDraftResponse, status_code=status.HTTP_200_OK)
def generate_proposal_draft(
    payload: ProposalDraftRequest,
    db: Session = Depends(get_db)
):
    """
    Synthesize a structured research proposal draft from an existing research direction.
    Supports LLM-guided synthesis when configured, with automatic template fallback.
    """
    try:
        logger.info(f"API Endpoint POST /api/research-directions/draft called with direction_id='{payload.direction_id}'")
        result = ProposalDraftService.synthesize_draft(db=db, direction_id=payload.direction_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating proposal draft: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to synthesize proposal draft: {str(e)}"
        )


@router.get("/export")
def export_research_directions(
    format: str = Query(..., description="Export format: md, markdown, json, or pdf"),
    top_k: int = Query(10, ge=1, le=20, description="Maximum number of research directions to export (1-20)"),
    db: Session = Depends(get_db)
):
    """
    Export actionable research proposal directions in Markdown (.md), JSON (.json), or PDF (.pdf) format.
    """
    fmt = format.lower().strip()
    if fmt not in ("md", "markdown", "json", "pdf"):
        logger.warning(f"Invalid export format requested: {format}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported export format. Allowed formats are: md, markdown, json, pdf."
        )

    try:
        logger.info(f"API Endpoint GET /api/research-directions/export called with format={format}, top_k={top_k}")
        directions_resp = ResearchDirectionService.generate_directions(db=db, top_k=top_k)
        filename = ProposalExportService.get_export_filename(fmt)

        if fmt in ("md", "markdown"):
            content = ProposalExportService.export_to_markdown(directions_resp)
            return Response(
                content=content,
                media_type="text/markdown",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'}
            )
        elif fmt == "json":
            content = ProposalExportService.export_to_json(directions_resp)
            return Response(
                content=content,
                media_type="application/json",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'}
            )
        elif fmt == "pdf":
            content_bytes = ProposalExportService.export_to_pdf(directions_resp)
            return Response(
                content=content_bytes,
                media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'}
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting research directions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export research directions: {str(e)}"
        )


@router.get("", response_model=ResearchDirectionResponse)
@router.get("/", response_model=ResearchDirectionResponse)
def get_research_directions(
    top_k: int = Query(10, ge=1, le=20, description="Maximum number of research directions to return (1-20)"),
    db: Session = Depends(get_db)
):
    """
    Fetch actionable, collection-based research proposal directions synthesized from multi-signal evidence.
    """
    try:
        logger.info(f"API Endpoint GET /api/research-directions called with top_k={top_k}")
        result = ResearchDirectionService.generate_directions(db=db, top_k=top_k)
        return result
    except Exception as e:
        logger.error(f"Error in GET /api/research-directions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate research directions: {str(e)}"
        )
