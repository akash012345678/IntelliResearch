import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.project_schema import (
    ResearchProjectCreate,
    ResearchProjectUpdate,
    ResearchProjectResponse,
    ProjectPaperResponse,
    BulkAddPapersRequest,
    BulkAddPapersResponse,
    AvailablePaperResponse,
    SavedDirectionCreate,
    SavedDirectionResponse,
    ProjectDetailResponse
)
from app.services.research_project_service import ResearchProjectService
from app.services.saved_direction_service import SavedDirectionService

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/projects",
    tags=["Research Projects"]
)


@router.post("", response_model=ResearchProjectResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=ResearchProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ResearchProjectCreate,
    db: Session = Depends(get_db)
):
    """Create a new Research Project."""
    try:
        return ResearchProjectService.create_project(db=db, data=payload)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating project: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("", response_model=List[ResearchProjectResponse])
@router.get("/", response_model=List[ResearchProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    """List all Research Projects."""
    return ResearchProjectService.list_projects(db=db)


@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project_details(project_id: int, db: Session = Depends(get_db)):
    """Fetch detailed information for a single Research Project."""
    return ResearchProjectService.get_project(db=db, project_id=project_id)


@router.patch("/{project_id}", response_model=ResearchProjectResponse)
def update_project(project_id: int, payload: ResearchProjectUpdate, db: Session = Depends(get_db)):
    """Update an existing Research Project."""
    return ResearchProjectService.update_project(db=db, project_id=project_id, data=payload)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """Delete a Research Project and its associations without deleting research papers."""
    ResearchProjectService.delete_project(db=db, project_id=project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Paper Association Endpoints
@router.post("/{project_id}/papers/bulk", response_model=BulkAddPapersResponse)
def bulk_add_papers_to_project(project_id: int, payload: BulkAddPapersRequest, db: Session = Depends(get_db)):
    """Bulk assign multiple ResearchPapers to a ResearchProject."""
    return ResearchProjectService.bulk_add_papers(db=db, project_id=project_id, paper_ids=payload.paper_ids)


@router.post("/{project_id}/papers/{paper_id}", response_model=ProjectPaperResponse, status_code=status.HTTP_201_CREATED)
def add_paper_to_project(project_id: int, paper_id: int, db: Session = Depends(get_db)):
    """Assign a ResearchPaper to a ResearchProject."""
    return ResearchProjectService.add_paper_to_project(db=db, project_id=project_id, paper_id=paper_id)



@router.delete("/{project_id}/papers/{paper_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_paper_from_project(project_id: int, paper_id: int, db: Session = Depends(get_db)):
    """Remove a paper assignment from a ResearchProject."""
    ResearchProjectService.remove_paper_from_project(db=db, project_id=project_id, paper_id=paper_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{project_id}/papers", response_model=List[ProjectPaperResponse])
def get_project_papers(project_id: int, db: Session = Depends(get_db)):
    """List all papers assigned to a ResearchProject with complete paper details."""
    return ResearchProjectService.get_project_papers(db=db, project_id=project_id)


@router.get("/{project_id}/available-papers", response_model=List[AvailablePaperResponse])
def get_available_project_papers(
    project_id: int,
    search: Optional[str] = Query(None, description="Search papers by title (case-insensitive)"),
    keyword: Optional[str] = Query(None, description="Filter by keyword"),
    algorithm: Optional[str] = Query(None, description="Filter by algorithm"),
    dataset: Optional[str] = Query(None, description="Filter by dataset"),
    methodology: Optional[str] = Query(None, description="Filter by methodology"),
    domain: Optional[str] = Query(None, description="Filter by application domain"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Retrieve ResearchPapers available for assignment to a ResearchProject, excluding already assigned papers."""
    return ResearchProjectService.get_available_papers(
        db=db,
        project_id=project_id,
        search=search,
        keyword=keyword,
        algorithm=algorithm,
        dataset=dataset,
        methodology=methodology,
        domain=domain,
        skip=skip,
        limit=limit
    )



# Saved Direction Endpoints
@router.post("/{project_id}/directions", response_model=SavedDirectionResponse, status_code=status.HTTP_201_CREATED)
def save_direction_to_project(project_id: int, payload: SavedDirectionCreate, db: Session = Depends(get_db)):
    """Save an immutable Research Direction snapshot to a project."""
    payload.project_id = project_id
    return SavedDirectionService.save_direction(db=db, data=payload)


@router.get("/{project_id}/directions", response_model=List[SavedDirectionResponse])
def list_project_directions(project_id: int, db: Session = Depends(get_db)):
    """List all saved Research Direction snapshots for a project."""
    return SavedDirectionService.list_project_directions(db=db, project_id=project_id)


@router.delete("/{project_id}/directions/{direction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_direction(project_id: int, direction_id: int, db: Session = Depends(get_db)):
    """Delete a saved Research Direction snapshot."""
    SavedDirectionService.delete_saved_direction(db=db, direction_id=direction_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


from fastapi import Response
