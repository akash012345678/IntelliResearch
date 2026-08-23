import logging
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.project_model import ResearchProject, SavedResearchDirection
from app.schemas.project_schema import SavedDirectionCreate, SavedDirectionResponse

logger = logging.getLogger(__name__)


class SavedDirectionService:
    """
    Service layer for saving and managing immutable snapshots of Actionable Research Directions.
    """

    @classmethod
    def save_direction(cls, db: Session, data: SavedDirectionCreate) -> SavedDirectionResponse:
        """Save an immutable snapshot of a Research Direction under a Research Project."""
        project = db.query(ResearchProject).filter(ResearchProject.id == data.project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Research Project with ID {data.project_id} not found."
            )

        direction = SavedResearchDirection(
            project_id=data.project_id,
            source_direction_id=data.source_direction_id,
            title=data.title.strip(),
            description=data.description.strip() if data.description else None,
            confidence=data.confidence,
            direction_data=data.direction_data
        )
        db.add(direction)
        db.commit()
        db.refresh(direction)
        logger.info(f"Saved Research Direction snapshot id={direction.id} for project_id={data.project_id}")
        return cls._to_response(direction)

    @classmethod
    def get_saved_direction(cls, db: Session, direction_id: int) -> SavedDirectionResponse:
        """Fetch a single saved Research Direction snapshot."""
        direction = db.query(SavedResearchDirection).filter(SavedResearchDirection.id == direction_id).first()
        if not direction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Saved Research Direction with ID {direction_id} not found."
            )
        return cls._to_response(direction)

    @classmethod
    def list_project_directions(cls, db: Session, project_id: int) -> List[SavedDirectionResponse]:
        """List all saved Research Directions for a given project."""
        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Research Project with ID {project_id} not found."
            )
        directions = db.query(SavedResearchDirection).filter(
            SavedResearchDirection.project_id == project_id
        ).order_by(SavedResearchDirection.created_at.desc()).all()
        return [cls._to_response(d) for d in directions]

    @classmethod
    def delete_saved_direction(cls, db: Session, direction_id: int) -> None:
        """Delete a saved Research Direction snapshot."""
        direction = db.query(SavedResearchDirection).filter(SavedResearchDirection.id == direction_id).first()
        if not direction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Saved Research Direction with ID {direction_id} not found."
            )
        db.delete(direction)
        db.commit()
        logger.info(f"Deleted saved direction id={direction_id}")

    @classmethod
    def _to_response(cls, d: SavedResearchDirection) -> SavedDirectionResponse:
        return SavedDirectionResponse(
            id=d.id,
            project_id=d.project_id,
            source_direction_id=d.source_direction_id,
            title=d.title,
            description=d.description,
            confidence=d.confidence,
            direction_data=d.direction_data,
            created_at=d.created_at.isoformat()
        )
