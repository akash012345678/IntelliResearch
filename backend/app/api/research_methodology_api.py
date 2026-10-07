import logging
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.methodology_plan_schema import MethodologyPlanResponse, SaveResearchPlanRequest
from app.services.research_methodology_service import ResearchMethodologyService
from app.services.research_project_service import ResearchProjectService

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Research Methodology & Experiment Planner"]
)


@router.get(
    "/research-directions/{direction_id}/methodology-plan",
    response_model=MethodologyPlanResponse,
    status_code=status.HTTP_200_OK
)
def get_global_methodology_plan(
    direction_id: str = Path(..., description="Unique ID of the research direction"),
    db: Session = Depends(get_db)
):
    """
    Retrieve global research methodology and experiment plan.
    Read-only service.
    """
    try:
        logger.info(f"API GET /api/research-directions/{direction_id}/methodology-plan called")
        return ResearchMethodologyService.get_methodology_plan(
            db=db,
            direction_id=direction_id,
            project_id=None
        )
    except Exception as e:
        logger.error(f"Error fetching methodology plan {direction_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate research methodology plan: {str(e)}"
        )


@router.get(
    "/projects/{project_id}/research-directions/{direction_id}/methodology-plan",
    response_model=MethodologyPlanResponse,
    status_code=status.HTTP_200_OK
)
def get_project_methodology_plan(
    project_id: int = Path(..., description="ID of the research project"),
    direction_id: str = Path(..., description="Unique ID of the research direction within project"),
    db: Session = Depends(get_db)
):
    """
    Retrieve project-scoped research methodology and experiment plan.
    Read-only service — strictly uses papers assigned to the project.
    """
    try:
        logger.info(f"API GET /api/projects/{project_id}/research-directions/{direction_id}/methodology-plan called")
        return ResearchMethodologyService.get_methodology_plan(
            db=db,
            direction_id=direction_id,
            project_id=project_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project methodology plan {direction_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate project research methodology plan: {str(e)}"
        )


from app.models.project_model import ResearchProject, SavedResearchDirection

@router.post(
    "/projects/{project_id}/research-plan/save",
    status_code=status.HTTP_200_OK
)
def save_project_research_plan(
    project_id: int = Path(..., description="ID of the research project"),
    payload: SaveResearchPlanRequest = ...,
    db: Session = Depends(get_db)
):
    """
    Save research methodology plan into project saved research directions.
    Explicit user save action only.
    """
    try:
        logger.info(f"API POST /api/projects/{project_id}/research-plan/save called")
        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        saved_dir = db.query(SavedResearchDirection).filter(
            SavedResearchDirection.project_id == project_id,
            SavedResearchDirection.source_direction_id == payload.direction_id
        ).first()

        if not saved_dir:
            saved_dir = SavedResearchDirection(
                project_id=project_id,
                source_direction_id=payload.direction_id,
                title=payload.plan_data.get("title", "Saved Research Methodology Plan"),
                description=payload.plan_data.get("research_problem", ""),
                confidence="HIGH",
                direction_data={"methodology_plan": payload.plan_data, "notes": payload.notes}
            )
            db.add(saved_dir)
        else:
            d_data = dict(saved_dir.direction_data or {})
            d_data["methodology_plan"] = payload.plan_data
            d_data["notes"] = payload.notes
            saved_dir.direction_data = d_data

        db.commit()

        return {
            "message": "Research methodology plan saved successfully to project.",
            "project_id": project_id,
            "direction_id": payload.direction_id
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving project research plan: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save research methodology plan: {str(e)}"
        )
