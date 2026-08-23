import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.paper_schema import SemanticSearchRequest, SemanticSearchResponse, RelatedPapersResponse
from app.services.semantic_index_service import SemanticIndexService

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/semantic/search", response_model=SemanticSearchResponse, status_code=status.HTTP_200_OK)
def semantic_search(
    request: SemanticSearchRequest,
    db: Session = Depends(get_db)
):
    """
    Perform semantic similarity search for a natural language text query.
    1. Generates 384-dimensional Sentence-BERT vector embedding.
    2. Searches FAISS IndexFlatIP vector index for nearest neighbors.
    3. Resolves paper IDs and retrieves paper metadata from Supabase PostgreSQL.
    4. Returns ranked result list ordered strictly by FAISS similarity score.
    """
    logger.info(f"Received semantic search request: query='{request.query[:50]}...', top_k={request.top_k}")
    try:
        service = SemanticIndexService()
        search_results = service.search_papers(
            query=request.query,
            top_k=request.top_k,
            db_session=db
        )
        return search_results
    except ValueError as ve:
        logger.warning(f"Semantic search validation error: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Semantic search execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the semantic search request."
        )

@router.get("/semantic/papers/{paper_id}/related", response_model=RelatedPapersResponse, status_code=status.HTTP_200_OK)
def get_related_papers(
    paper_id: int,
    top_k: int = Query(default=5, ge=1, le=20, description="Number of top related research papers to return"),
    db: Session = Depends(get_db)
):
    """
    Retrieve semantically similar research papers for a selected source paper.
    1. Validates source paper existence in Supabase PostgreSQL (returns 404 if missing).
    2. Retrieves vector embedding from FAISS or generates it on the fly.
    3. Searches FAISS vector index for nearest neighbors excluding the source paper itself.
    4. Retrieves complete paper metadata from Supabase PostgreSQL.
    5. Returns ranked list ordered strictly by FAISS similarity score.
    """
    logger.info(f"Received request for related papers for paper ID {paper_id}, top_k={top_k}")
    try:
        service = SemanticIndexService()
        related_results = service.find_related_papers(
            paper_id=paper_id,
            top_k=top_k,
            db_session=db
        )
        return related_results
    except KeyError as ke:
        logger.warning(f"Related papers target paper ID {paper_id} not found: {ke}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ke).strip("'\"")
        )
    except ValueError as ve:
        logger.warning(f"Related papers validation error: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Failed to retrieve related papers for ID {paper_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving related research papers."
        )

