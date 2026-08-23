import logging
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.paper_model import ResearchPaper
from app.models.project_model import ProjectPaper
from app.schemas.paper_schema import PaperResponse, PaperDetailResponse, PaperMetadataResponse
from app.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/papers", response_model=List[PaperResponse])
def get_papers(
    title: Optional[str] = Query(None, description="Search papers by title (case-insensitive)"),
    db: Session = Depends(get_db)
):
    """
    Retrieve all papers, optionally filtering by title.
    """
    try:
        query = db.query(ResearchPaper)
        if title:
            logger.info(f"Filtering papers with title query: {title}")
            query = query.filter(ResearchPaper.title.ilike(f"%{title}%"))
        
        # Order by upload time descending to show newest uploads first
        papers = query.order_by(ResearchPaper.uploaded_at.desc()).all()
        return papers
    except Exception as e:
        logger.error(f"Error listing papers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve research papers from the database."
        )

@router.get("/paper/{paper_id}", response_model=PaperDetailResponse)
def get_paper(
    paper_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve details of a specific paper by its ID.
    """
    logger.info(f"Retrieving paper with ID: {paper_id}")
    paper = db.query(ResearchPaper).filter(ResearchPaper.id == paper_id).first()
    
    if not paper:
        logger.warning(f"Paper with ID {paper_id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research paper with ID {paper_id} does not exist."
        )
    
    return paper

@router.get("/paper/{paper_id}/metadata", response_model=PaperMetadataResponse)
def get_paper_metadata(
    paper_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve only the extracted metadata (keywords, algorithms, datasets, 
    methodologies, application domains) of a specific paper by its ID.
    """
    logger.info(f"Retrieving metadata for paper ID: {paper_id}")
    paper = db.query(ResearchPaper).filter(ResearchPaper.id == paper_id).first()
    
    if not paper:
        logger.warning(f"Paper with ID {paper_id} not found for metadata retrieval.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research paper with ID {paper_id} does not exist."
        )
    
    return paper

@router.delete("/paper/{paper_id}")
def delete_paper(
    paper_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a specific paper by its ID from the database and remove associated files from disk.
    """
    logger.info(f"Request to delete paper with ID: {paper_id}")
    paper = db.query(ResearchPaper).filter(ResearchPaper.id == paper_id).first()
    
    if not paper:
        logger.warning(f"Delete target: Paper with ID {paper_id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research paper with ID {paper_id} does not exist."
        )
    
    # Keep track of file details for clean up
    filename = paper.filename
    pdf_path = settings.ORIGINAL_PAPERS_DIR / filename
    txt_path = settings.EXTRACTED_TEXT_DIR / f"{Path(filename).stem}.txt"

    # 1. Delete from Database first (along with project linkages)
    try:
        db.query(ProjectPaper).filter(ProjectPaper.paper_id == paper_id).delete()
        db.delete(paper)
        db.commit()
        logger.info(f"Successfully deleted paper ID {paper_id} from database.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete paper ID {paper_id} from database: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete paper metadata from database."
        )

    # 2. Remove paper from FAISS Vector Store (fail-safe)
    try:
        from app.services.semantic_index_service import SemanticIndexService
        SemanticIndexService().remove_paper(paper_id)
        logger.info(f"Successfully removed paper ID {paper_id} from FAISS Vector Store.")
    except Exception as se:
        logger.warning(f"Could not remove paper ID {paper_id} from FAISS Vector Store (non-fatal): {se}")

    # 3. Delete physical files from disk (fail-safe)
    files_deleted = []
    files_failed = []
    
    for path in [pdf_path, txt_path]:
        if path.exists():
            try:
                path.unlink()
                files_deleted.append(path.name)
            except Exception as e:
                logger.error(f"Failed to delete file {path}: {e}")
                files_failed.append(path.name)
        else:
            logger.warning(f"File not found on disk during cleanup: {path}")

    # Log clean up result
    if files_deleted:
        logger.info(f"Cleaned up physical files: {files_deleted}")
    if files_failed:
        logger.warning(f"Could not clean up physical files: {files_failed}")

    return {
        "message": "Paper and associated files deleted successfully",
        "paper_id": paper_id,
        "cleaned_files": files_deleted
    }


@router.post("/semantic/reindex")
def reindex_semantic_store(db: Session = Depends(get_db)):
    """
    Administrative endpoint to safely re-index all papers stored in Supabase PostgreSQL into FAISS.
    """
    logger.info("Admin request received to reindex all research papers.")
    try:
        from app.services.semantic_index_service import SemanticIndexService
        semantic_service = SemanticIndexService()
        summary = semantic_service.rebuild_index(db_session=db)
        return summary
    except Exception as e:
        logger.error(f"Failed to reindex semantic store: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reindex operation failed: {str(e)}"
        )
