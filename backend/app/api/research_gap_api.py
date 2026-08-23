import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.research_gap_service import ResearchGapService

logger = logging.getLogger(__name__)

router = APIRouter()

COLLECTION_DISCLAIMER = "Gap analysis is based on the currently indexed research-paper collection and may change as more papers are added."


@router.get("/research-gaps", status_code=status.HTTP_200_OK)
def get_research_gaps(
    top_k: int = Query(default=10, ge=1, le=50, description="Number of top potential research gaps to return"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Detect and return ranked potential research gaps using multi-signal evidence evaluation.
    """
    logger.info(f"Received request for research gap detection with top_k={top_k}")
    try:
        gap_service = ResearchGapService()
        gaps = gap_service.detect_gaps(db_session=db, top_k=top_k)

        return {
            "total_candidates": len(gaps),
            "collection_disclaimer": COLLECTION_DISCLAIMER,
            "gaps": gaps
        }
    except ValueError as ve:
        logger.warning(f"Research gap detection parameter validation error: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Failed to detect potential research gaps: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while detecting potential research gaps."
        )
