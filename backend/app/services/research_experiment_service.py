import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.project_model import ResearchProject, ResearchExperiment, ExperimentRun, ExperimentResult
from app.schemas.experiment_schema import (
    ExperimentCreate,
    ExperimentUpdate,
    ExperimentResponse,
    ExperimentRunCreate,
    ExperimentRunResponse,
    ExperimentResultCreate,
    ExperimentResultResponse,
    ExperimentSummaryResponse
)
from app.services.research_methodology_service import ResearchMethodologyService

logger = logging.getLogger(__name__)


class ResearchExperimentService:
    """
    Service layer for managing Research Experiments, Runs, and Empirical Results.
    """

    @classmethod
    def _build_result_response(cls, res: ExperimentResult) -> ExperimentResultResponse:
        return ExperimentResultResponse(
            id=res.id,
            run_id=res.run_id,
            metric_name=res.metric_name,
            metric_value=str(res.metric_value),
            unit=res.unit,
            method_type=res.method_type,
            notes=res.notes,
            created_at=res.created_at.isoformat()
        )

    @classmethod
    def _build_run_response(cls, run: ExperimentRun) -> ExperimentRunResponse:
        results_resp = [cls._build_result_response(r) for r in run.results]
        return ExperimentRunResponse(
            id=run.id,
            experiment_id=run.experiment_id,
            run_number=run.run_number,
            seed=run.seed,
            duration_seconds=run.duration_seconds,
            notes=run.notes,
            created_at=run.created_at.isoformat(),
            results=results_resp
        )

    @classmethod
    def _build_experiment_response(cls, exp: ResearchExperiment) -> ExperimentResponse:
        runs_resp = [cls._build_run_response(r) for r in exp.runs]
        return ExperimentResponse(
            id=exp.id,
            project_id=exp.project_id,
            direction_id=exp.direction_id,
            name=exp.name,
            purpose=exp.purpose,
            experiment_type=exp.experiment_type,
            status=exp.status,
            research_question=exp.research_question,
            hypothesis_h0=exp.hypothesis_h0,
            hypothesis_h1=exp.hypothesis_h1,
            dataset_config=exp.dataset_config or {},
            baseline_config=exp.baseline_config or {},
            proposed_config=exp.proposed_config or {},
            environment_config=exp.environment_config or {},
            execution_config=exp.execution_config or {},
            notes=exp.notes,
            limitations=exp.limitations,
            reproducibility_checklist=exp.reproducibility_checklist or [],
            created_at=exp.created_at.isoformat(),
            updated_at=exp.updated_at.isoformat(),
            runs=runs_resp
        )

    @classmethod
    def get_experiments(cls, db: Session, project_id: int) -> List[ExperimentResponse]:
        """
        Retrieve all experiments for a given project.
        """
        exps = db.query(ResearchExperiment).filter(ResearchExperiment.project_id == project_id).order_by(ResearchExperiment.created_at.asc()).all()
        return [cls._build_experiment_response(e) for e in exps]

    @classmethod
    def create_experiment(cls, db: Session, project_id: int, payload: ExperimentCreate) -> ExperimentResponse:
        """
        Create a new research experiment record under a project.
        """
        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"Research project {project_id} not found")

        exp = ResearchExperiment(
            project_id=project_id,
            direction_id=payload.direction_id,
            name=payload.name,
            purpose=payload.purpose,
            experiment_type=payload.experiment_type,
            status=payload.status,
            research_question=payload.research_question,
            hypothesis_h0=payload.hypothesis_h0,
            hypothesis_h1=payload.hypothesis_h1,
            dataset_config=payload.dataset_config or {},
            baseline_config=payload.baseline_config or {},
            proposed_config=payload.proposed_config or {},
            environment_config=payload.environment_config or {},
            execution_config=payload.execution_config or {},
            notes=payload.notes,
            limitations=payload.limitations,
            reproducibility_checklist=payload.reproducibility_checklist or []
        )
        db.add(exp)
        db.commit()
        db.refresh(exp)
        return cls._build_experiment_response(exp)

    @classmethod
    def import_plan_experiments(cls, db: Session, project_id: int, direction_id: str) -> List[ExperimentResponse]:
        """
        Import planned experiments directly from the Research Methodology Plan into experiment records.
        """
        plan_resp = ResearchMethodologyService.get_methodology_plan(db, direction_id, project_id)
        imported_exps = []

        # Check existing experiments to prevent duplicates
        existing_names = set(
            e.name for e in db.query(ResearchExperiment).filter(
                ResearchExperiment.project_id == project_id,
                ResearchExperiment.direction_id == direction_id
            ).all()
        )

        for plan_exp in plan_resp.experiments:
            exp_name = plan_exp.title
            if exp_name in existing_names:
                continue

            exp = ResearchExperiment(
                project_id=project_id,
                direction_id=direction_id,
                name=exp_name,
                purpose=plan_exp.purpose,
                experiment_type="BASELINE_COMPARISON" if plan_exp.experiment_number == 1 else "ABLATION" if "Ablation" in exp_name else "CUSTOM",
                status="PLANNED",
                research_question=f"RQ{plan_exp.experiment_number}: Evaluate {exp_name}",
                hypothesis_h0=plan_resp.hypotheses.null_hypothesis,
                hypothesis_h1=plan_resp.hypotheses.alternative_hypothesis,
                dataset_config={"dataset_name": plan_resp.dataset_plan[0].name if plan_resp.dataset_plan else "Default Benchmark"},
                baseline_config={"algorithm": plan_exp.baseline},
                proposed_config={"architecture": plan_resp.proposed_method.get("architecture_name", "Proposed Model")},
                environment_config={"seed": 42},
                execution_config={},
                notes="Imported from Research Methodology Plan.",
                reproducibility_checklist=plan_resp.reproducibility_checklist
            )
            db.add(exp)
            imported_exps.append(exp)

        db.commit()
        for e in imported_exps:
            db.refresh(e)

        return cls.get_experiments(db, project_id)

    @classmethod
    def get_experiment(cls, db: Session, project_id: int, experiment_id: int) -> ExperimentResponse:
        exp = db.query(ResearchExperiment).filter(
            ResearchExperiment.id == experiment_id,
            ResearchExperiment.project_id == project_id
        ).first()
        if not exp:
            raise HTTPException(status_code=404, detail=f"Experiment {experiment_id} not found in project {project_id}")
        return cls._build_experiment_response(exp)

    @classmethod
    def update_experiment(cls, db: Session, project_id: int, experiment_id: int, payload: ExperimentUpdate) -> ExperimentResponse:
        exp = db.query(ResearchExperiment).filter(
            ResearchExperiment.id == experiment_id,
            ResearchExperiment.project_id == project_id
        ).first()
        if not exp:
            raise HTTPException(status_code=404, detail=f"Experiment {experiment_id} not found")

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(exp, field, value)

        db.commit()
        db.refresh(exp)
        return cls._build_experiment_response(exp)

    @classmethod
    def delete_experiment(cls, db: Session, project_id: int, experiment_id: int):
        exp = db.query(ResearchExperiment).filter(
            ResearchExperiment.id == experiment_id,
            ResearchExperiment.project_id == project_id
        ).first()
        if not exp:
            raise HTTPException(status_code=404, detail=f"Experiment {experiment_id} not found")
        db.delete(exp)
        db.commit()
        return {"message": f"Experiment {experiment_id} deleted successfully."}

    @classmethod
    def create_run(cls, db: Session, project_id: int, experiment_id: int, payload: ExperimentRunCreate) -> ExperimentRunResponse:
        exp = db.query(ResearchExperiment).filter(
            ResearchExperiment.id == experiment_id,
            ResearchExperiment.project_id == project_id
        ).first()
        if not exp:
            raise HTTPException(status_code=404, detail=f"Experiment {experiment_id} not found")

        run_num = len(exp.runs) + 1
        run = ExperimentRun(
            experiment_id=experiment_id,
            run_number=run_num,
            seed=payload.seed,
            duration_seconds=payload.duration_seconds,
            notes=payload.notes
        )
        db.add(run)
        db.flush()

        for r_create in payload.results:
            r = ExperimentResult(
                run_id=run.id,
                metric_name=r_create.metric_name,
                metric_value=r_create.metric_value,
                unit=r_create.unit,
                method_type=r_create.method_type,
                notes=r_create.notes
            )
            db.add(r)

        db.commit()
        db.refresh(run)
        return cls._build_run_response(run)

    @classmethod
    def record_results(cls, db: Session, project_id: int, run_id: int, results_payload: List[ExperimentResultCreate]) -> List[ExperimentResultResponse]:
        run = db.query(ExperimentRun).join(ResearchExperiment).filter(
            ExperimentRun.id == run_id,
            ResearchExperiment.project_id == project_id
        ).first()
        if not run:
            raise HTTPException(status_code=404, detail=f"Experiment run {run_id} not found")

        created_results = []
        for r_create in results_payload:
            r = ExperimentResult(
                run_id=run_id,
                metric_name=r_create.metric_name,
                metric_value=r_create.metric_value,
                unit=r_create.unit,
                method_type=r_create.method_type,
                notes=r_create.notes
            )
            db.add(r)
            created_results.append(r)

        db.commit()
        for r in created_results:
            db.refresh(r)

        return [cls._build_result_response(r) for r in created_results]

    @classmethod
    def get_summary(cls, db: Session, project_id: int) -> ExperimentSummaryResponse:
        exps = cls.get_experiments(db, project_id)
        
        not_started = sum(1 for e in exps if e.status == "PLANNED")
        in_progress = sum(1 for e in exps if e.status == "IN_PROGRESS")
        completed = sum(1 for e in exps if e.status == "COMPLETED")
        results_recorded = sum(1 for e in exps if any(len(r.results) > 0 for r in e.runs))
        needs_attention = sum(1 for e in exps if e.status in ["BLOCKED", "CANCELLED"])

        return ExperimentSummaryResponse(
            total_planned=len(exps),
            not_started_count=not_started,
            in_progress_count=in_progress,
            completed_count=completed,
            results_recorded_count=results_recorded,
            needs_attention_count=needs_attention,
            experiments=exps
        )
