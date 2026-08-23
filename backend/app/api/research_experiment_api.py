import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.experiment_schema import (
    ExperimentCreate,
    ExperimentUpdate,
    ExperimentResponse,
    ExperimentRunCreate,
    ExperimentRunResponse,
    ExperimentResultCreate,
    ExperimentResultResponse,
    ExperimentSummaryResponse,
    ImportPlanExperimentsRequest
)
from app.services.research_experiment_service import ResearchExperimentService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/projects",
    tags=["Research Experiment Workspace & Result Tracking"]
)


@router.get(
    "/{project_id}/experiments",
    response_model=List[ExperimentResponse],
    status_code=status.HTTP_200_OK
)
def get_project_experiments(
    project_id: int = Path(..., description="ID of the research project"),
    db: Session = Depends(get_db)
):
    """
    Retrieve all research experiments for a project.
    """
    try:
        return ResearchExperimentService.get_experiments(db, project_id)
    except Exception as e:
        logger.error(f"Error fetching experiments for project {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch experiments: {str(e)}"
        )


@router.post(
    "/{project_id}/experiments",
    response_model=ExperimentResponse,
    status_code=status.HTTP_201_CREATED
)
def create_project_experiment(
    project_id: int = Path(..., description="ID of the research project"),
    payload: ExperimentCreate = ...,
    db: Session = Depends(get_db)
):
    """
    Create a new custom research experiment under a project.
    """
    try:
        return ResearchExperimentService.create_experiment(db, project_id, payload)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating experiment for project {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create experiment: {str(e)}"
        )


@router.post(
    "/{project_id}/experiments/import-plan",
    response_model=List[ExperimentResponse],
    status_code=status.HTTP_200_OK
)
def import_methodology_plan_experiments(
    project_id: int = Path(..., description="ID of the research project"),
    payload: ImportPlanExperimentsRequest = ...,
    db: Session = Depends(get_db)
):
    """
    Import planned experiments from a Research Methodology Plan into experiment records.
    Prevents creation of duplicate experiments.
    """
    try:
        return ResearchExperimentService.import_plan_experiments(db, project_id, payload.direction_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing methodology experiments for project {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import methodology experiments: {str(e)}"
        )


@router.get(
    "/{project_id}/experiments/summary",
    response_model=ExperimentSummaryResponse,
    status_code=status.HTTP_200_OK
)
def get_project_experiment_summary(
    project_id: int = Path(..., description="ID of the research project"),
    db: Session = Depends(get_db)
):
    """
    Retrieve workspace dashboard metric summary for a project's experiments.
    """
    try:
        return ResearchExperimentService.get_summary(db, project_id)
    except Exception as e:
        logger.error(f"Error fetching experiment summary for project {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch experiment summary: {str(e)}"
        )


@router.get(
    "/{project_id}/experiments/{experiment_id}",
    response_model=ExperimentResponse,
    status_code=status.HTTP_200_OK
)
def get_project_experiment_detail(
    project_id: int = Path(..., description="ID of the research project"),
    experiment_id: int = Path(..., description="ID of the experiment"),
    db: Session = Depends(get_db)
):
    """
    Retrieve single research experiment detail view.
    """
    try:
        return ResearchExperimentService.get_experiment(db, project_id, experiment_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching experiment {experiment_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch experiment detail: {str(e)}"
        )


@router.patch(
    "/{project_id}/experiments/{experiment_id}",
    response_model=ExperimentResponse,
    status_code=status.HTTP_200_OK
)
def update_project_experiment(
    project_id: int = Path(..., description="ID of the research project"),
    experiment_id: int = Path(..., description="ID of the experiment"),
    payload: ExperimentUpdate = ...,
    db: Session = Depends(get_db)
):
    """
    Update an existing research experiment record.
    """
    try:
        return ResearchExperimentService.update_experiment(db, project_id, experiment_id, payload)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating experiment {experiment_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update experiment: {str(e)}"
        )


@router.delete(
    "/{project_id}/experiments/{experiment_id}",
    status_code=status.HTTP_200_OK
)
def delete_project_experiment(
    project_id: int = Path(..., description="ID of the research project"),
    experiment_id: int = Path(..., description="ID of the experiment"),
    db: Session = Depends(get_db)
):
    """
    Delete a research experiment record.
    """
    try:
        return ResearchExperimentService.delete_experiment(db, project_id, experiment_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting experiment {experiment_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete experiment: {str(e)}"
        )


@router.post(
    "/{project_id}/experiments/{experiment_id}/runs",
    response_model=ExperimentRunResponse,
    status_code=status.HTTP_201_CREATED
)
def create_experiment_run(
    project_id: int = Path(..., description="ID of the research project"),
    experiment_id: int = Path(..., description="ID of the experiment"),
    payload: ExperimentRunCreate = ...,
    db: Session = Depends(get_db)
):
    """
    Create a new experiment execution run.
    """
    try:
        return ResearchExperimentService.create_run(db, project_id, experiment_id, payload)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating run for experiment {experiment_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create experiment run: {str(e)}"
        )


@router.post(
    "/{project_id}/experiments/runs/{run_id}/results",
    response_model=List[ExperimentResultResponse],
    status_code=status.HTTP_201_CREATED
)
def record_experiment_results(
    project_id: int = Path(..., description="ID of the research project"),
    run_id: int = Path(..., description="ID of the experiment run"),
    payload: List[ExperimentResultCreate] = ...,
    db: Session = Depends(get_db)
):
    """
    Record real student-entered empirical results for an experiment run.
    """
    try:
        return ResearchExperimentService.record_results(db, project_id, run_id, payload)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording results for run {run_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record empirical experiment results: {str(e)}"
        )
