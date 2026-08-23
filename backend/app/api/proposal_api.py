import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.proposal_persistence_schema import (
    ProposalCreate,
    ProposalResponse,
    ProposalVersionCreate,
    ProposalVersionResponse,
    ProposalVersionListResponse
)
from app.schemas.proposal_edit_schema import (
    ProposalEditRequest,
    ProposalComparisonResponse
)
from app.services.proposal_persistence_service import ProposalPersistenceService

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Proposal Persistence & Versioning"]
)


@router.post("/proposals", response_model=ProposalResponse, status_code=status.HTTP_201_CREATED)
def create_proposal(payload: ProposalCreate, db: Session = Depends(get_db)):
    """Persist a generated ProposalDraft under a Research Project (Version 1)."""
    try:
        return ProposalPersistenceService.create_proposal(db=db, data=payload)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating proposal: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/proposals/{proposal_id}", response_model=ProposalResponse)
def get_proposal(proposal_id: int, db: Session = Depends(get_db)):
    """Fetch details of a single saved Proposal."""
    return ProposalPersistenceService.get_proposal(db=db, proposal_id=proposal_id)


@router.get("/projects/{project_id}/proposals", response_model=List[ProposalResponse])
def list_project_proposals(project_id: int, db: Session = Depends(get_db)):
    """List all saved Proposals for a Research Project."""
    return ProposalPersistenceService.list_project_proposals(db=db, project_id=project_id)


@router.delete("/proposals/{proposal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_proposal(proposal_id: int, db: Session = Depends(get_db)):
    """Delete a saved Proposal and all its version entries."""
    ProposalPersistenceService.delete_proposal(db=db, proposal_id=proposal_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Version History & Editing Endpoints
@router.patch("/proposals/{proposal_id}", response_model=ProposalVersionResponse)
def edit_proposal(proposal_id: int, payload: ProposalEditRequest, db: Session = Depends(get_db)):
    """Edit structured sections of the latest proposal version and persist as a NEW version entry."""
    return ProposalPersistenceService.edit_proposal(db=db, proposal_id=proposal_id, data=payload)


@router.get("/proposals/{proposal_id}/versions", response_model=ProposalVersionListResponse)
def get_proposal_versions(proposal_id: int, db: Session = Depends(get_db)):
    """List all version history entries for a saved Proposal (sorted version_number DESC)."""
    return ProposalPersistenceService.get_proposal_versions(db=db, proposal_id=proposal_id)


@router.get("/proposals/{proposal_id}/compare", response_model=ProposalComparisonResponse)
def compare_proposal_versions(
    proposal_id: int,
    version_a: int = Query(..., description="First version number to compare"),
    version_b: int = Query(..., description="Second version number to compare"),
    db: Session = Depends(get_db)
):
    """Compare two proposal versions section-by-section and surface section diffs."""
    return ProposalPersistenceService.compare_versions(
        db=db, proposal_id=proposal_id, version_a=version_a, version_b=version_b
    )


@router.get("/proposals/{proposal_id}/versions/{version_number}", response_model=ProposalVersionResponse)
def get_proposal_version(proposal_id: int, version_number: int, db: Session = Depends(get_db)):
    """Fetch a specific version number of a saved Proposal."""
    return ProposalPersistenceService.get_proposal_version(db=db, proposal_id=proposal_id, version_number=version_number)


@router.post("/proposals/{proposal_id}/versions", response_model=ProposalVersionResponse, status_code=status.HTTP_201_CREATED)
def create_proposal_version(proposal_id: int, payload: ProposalVersionCreate, db: Session = Depends(get_db)):
    """Save a new version under an existing Proposal."""
    return ProposalPersistenceService.save_proposal_version(db=db, proposal_id=proposal_id, data=payload)


@router.post("/proposals/{proposal_id}/restore/{version_number}", response_model=ProposalVersionResponse, status_code=status.HTTP_201_CREATED)
def restore_proposal_version(proposal_id: int, version_number: int, db: Session = Depends(get_db)):
    """Restore a historical proposal version by creating a NEW ProposalVersion entry."""
    return ProposalPersistenceService.restore_version(db=db, proposal_id=proposal_id, version_number=version_number)
