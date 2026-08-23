import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.global_research_intelligence_service import GlobalResearchIntelligenceService
from app.schemas.intelligence_schema import GlobalResearchIntelligenceResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/research-intelligence", response_model=GlobalResearchIntelligenceResponse, status_code=status.HTTP_200_OK)
def get_global_research_intelligence(
    max_paper_relationships: int = Query(default=50, ge=1, le=200, description="Max paper pairwise relationships to return"),
    max_gaps: int = Query(default=20, ge=1, le=100, description="Max potential research gaps to return"),
    max_underrepresented: int = Query(default=20, ge=1, le=100, description="Max underrepresented concepts to return"),
    max_directions: int = Query(default=10, ge=1, le=50, description="Max candidate research directions to return"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Perform read-only global research landscape aggregation across the entire indexed paper collection.
    """
    logger.info(
        f"Received request for global research intelligence analysis: "
        f"max_paper_relationships={max_paper_relationships}, max_gaps={max_gaps}, "
        f"max_underrepresented={max_underrepresented}, max_directions={max_directions}"
    )
    try:
        service = GlobalResearchIntelligenceService()
        analysis = service.analyze_collection(
            db_session=db,
            max_paper_relationships=max_paper_relationships,
            max_gaps=max_gaps,
            max_underrepresented=max_underrepresented,
            max_directions=max_directions
        )
        return analysis
    except ValueError as ve:
        logger.warning(f"Parameter validation error in global research intelligence: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Failed to perform global research intelligence analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while analyzing the research paper collection."
        )
