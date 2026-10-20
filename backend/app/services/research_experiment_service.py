import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.project_model import ResearchProject, ResearchExperiment, ExperimentRun, ExperimentResult, SavedResearchDirection
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

        exec_cfg = dict(payload.execution_config or {})
        if "origin" not in exec_cfg:
            exec_cfg["origin"] = "CUSTOM"

        exp = ResearchExperiment(
            project_id=project_id,
            direction_id=payload.direction_id,
            name=payload.name,
            purpose=payload.purpose,
            experiment_type=payload.experiment_type,
            status=payload.status or "NOT_STARTED",
            research_question=payload.research_question,
            hypothesis_h0=payload.hypothesis_h0,
            hypothesis_h1=payload.hypothesis_h1,
            dataset_config=payload.dataset_config or {},
            baseline_config=payload.baseline_config or {},
            proposed_config=payload.proposed_config or {},
            environment_config=payload.environment_config or {},
            execution_config=exec_cfg,
            notes=payload.notes,
            limitations=payload.limitations,
            reproducibility_checklist=payload.reproducibility_checklist or []
        )
        db.add(exp)
        db.commit()
        db.refresh(exp)
        return cls._build_experiment_response(exp)

    @classmethod
    def import_plan_experiments(cls, db: Session, project_id: int, direction_id: str) -> Dict[str, Any]:
        """
        Import planned experiments directly from the Research Methodology Plan into experiment records.
        Prevents duplicate imports.
        """
        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"Research project {project_id} not found")

        saved_dir = db.query(SavedResearchDirection).filter(
            SavedResearchDirection.project_id == project_id,
            SavedResearchDirection.source_direction_id == direction_id
        ).first()

        plan_data = None
        if saved_dir and saved_dir.direction_data and "methodology_plan" in saved_dir.direction_data:
            plan_data = saved_dir.direction_data["methodology_plan"]

        if not plan_data:
            plan_resp = ResearchMethodologyService.get_methodology_plan(db, direction_id, project_id)
            plan_data = plan_resp.model_dump() if hasattr(plan_resp, "model_dump") else plan_resp.dict()

        plan_title = plan_data.get("title", f"Research Methodology Plan ({direction_id})")

        if not saved_dir:
            saved_dir = SavedResearchDirection(
                project_id=project_id,
                source_direction_id=direction_id,
                title=plan_title,
                confidence="High",
                direction_data={"direction_id": direction_id, "methodology_plan": plan_data}
            )
            db.add(saved_dir)
            db.commit()
            db.refresh(saved_dir)

        planned_experiments = plan_data.get("experiments", [])
        
        dataset_plan = plan_data.get("dataset_plan", [])
        if isinstance(dataset_plan, list) and len(dataset_plan) > 0:
            first_ds = dataset_plan[0]
            dataset_str = first_ds.get("name") if isinstance(first_ds, dict) else str(first_ds)
            all_dataset_names = [d.get("name") if isinstance(d, dict) else str(d) for d in dataset_plan]
        else:
            dataset_str = "Standard Evaluation Split"
            all_dataset_names = [dataset_str]

        proposed_method = plan_data.get("proposed_method", {})
        proposed_arch = proposed_method.get("architecture_name", "Proposed Model") if isinstance(proposed_method, dict) else "Proposed Model"

        hypotheses = plan_data.get("hypotheses", {})
        if isinstance(hypotheses, dict):
            null_hypo = hypotheses.get("null_hypothesis", "")
            alt_hypo = hypotheses.get("alternative_hypothesis", "")
        else:
            null_hypo = getattr(hypotheses, "null_hypothesis", "") if hypotheses else ""
            alt_hypo = getattr(hypotheses, "alternative_hypothesis", "") if hypotheses else ""

        reproducibility = plan_data.get("reproducibility_checklist", [])
        experiment_parameters = plan_data.get("experiment_parameters", [])

        existing_exps = db.query(ResearchExperiment).filter(
            ResearchExperiment.project_id == project_id
        ).all()

        existing_names_for_dir = set(
            e.name.strip().lower() for e in existing_exps if e.direction_id == direction_id and e.name
        )

        imported_exps = []
        skipped_count = 0

        for plan_exp in planned_experiments:
            if isinstance(plan_exp, dict):
                exp_number = plan_exp.get("experiment_number", 1)
                exp_title = plan_exp.get("title", f"Exp {exp_number}")
                exp_purpose = plan_exp.get("purpose", "")
                exp_variables = plan_exp.get("variables", "")
                exp_baseline = plan_exp.get("baseline", "Baseline Model")
                exp_metrics = plan_exp.get("metrics", [])
            else:
                exp_number = plan_exp.experiment_number
                exp_title = plan_exp.title
                exp_purpose = plan_exp.purpose
                exp_variables = plan_exp.variables
                exp_baseline = plan_exp.baseline
                exp_metrics = plan_exp.metrics

            if exp_title.strip().lower() in existing_names_for_dir:
                skipped_count += 1
                continue

            exp_title_lower = exp_title.strip().lower()
            exp_type_raw = ""
            if isinstance(plan_exp, dict):
                exp_type_raw = (plan_exp.get("type") or plan_exp.get("experiment_type") or "").upper()
            else:
                exp_type_raw = (getattr(plan_exp, "type", None) or getattr(plan_exp, "experiment_type", None) or "").upper()

            if exp_type_raw in ["BASELINE_COMPARISON", "PROPOSED_METHOD", "ABLATION", "LATENCY_EFFICIENCY", "CUSTOM"]:
                exp_type = exp_type_raw
            elif "baseline" in exp_title_lower or exp_number == 1:
                exp_type = "BASELINE_COMPARISON"
            elif "proposed" in exp_title_lower or "integrated" in exp_title_lower or exp_number == 2:
                exp_type = "PROPOSED_METHOD"
            elif "ablation" in exp_title_lower:
                exp_type = "ABLATION"
            elif any(k in exp_title_lower for k in ["latency", "fps", "throughput", "benchmarking", "efficiency"]):
                exp_type = "LATENCY_EFFICIENCY"
            else:
                exp_type = "CUSTOM"

            exp = ResearchExperiment(
                project_id=project_id,
                direction_id=direction_id,
                name=exp_title,
                purpose=exp_purpose,
                experiment_type=exp_type,
                status="NOT_STARTED",
                research_question=f"RQ{exp_number}: Evaluate {exp_title}",
                hypothesis_h0=null_hypo,
                hypothesis_h1=alt_hypo,
                dataset_config={
                    "dataset_name": dataset_str,
                    "all_datasets": all_dataset_names
                },
                baseline_config={"algorithm": exp_baseline},
                proposed_config={"architecture": proposed_arch},
                environment_config={"seed": 42},
                execution_config={
                    "origin": "PLANNED",
                    "experiment_number": exp_number,
                    "variables": exp_variables,
                    "metrics": exp_metrics,
                    "source_plan_title": plan_title,
                    "source_opportunity_id": direction_id,
                    "experiment_parameters": experiment_parameters
                },
                notes=f"Imported from Research Methodology Plan ({plan_title}).",
                reproducibility_checklist=reproducibility
            )
            db.add(exp)
            imported_exps.append(exp)

        db.commit()
        for e in imported_exps:
            db.refresh(e)

        all_project_exps = cls.get_experiments(db, project_id)

        if len(imported_exps) > 0:
            msg = f"{len(imported_exps)} planned experiment(s) imported successfully."
        elif skipped_count > 0:
            msg = f"All {skipped_count} planned experiment(s) for opportunity '{direction_id}' are already imported."
        else:
            msg = "No planned experiments found to import."

        return {
            "project_id": project_id,
            "research_plan_id": direction_id,
            "opportunity_id": direction_id,
            "imported_count": len(imported_exps),
            "skipped_count": skipped_count,
            "message": msg,
            "experiments": all_project_exps
        }

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
        
        not_started = sum(1 for e in exps if e.status in ["NOT_STARTED", "PLANNED", "READY"])
        in_progress = sum(1 for e in exps if e.status == "IN_PROGRESS")
        completed = sum(1 for e in exps if e.status == "COMPLETED")
        results_recorded = sum(1 for e in exps if any(len(r.results) > 0 for r in e.runs))
        needs_attention = sum(1 for e in exps if e.status in ["BLOCKED", "CANCELLED", "NEEDS_ATTENTION"])

        return ExperimentSummaryResponse(
            total_planned=len(exps),
            not_started_count=not_started,
            in_progress_count=in_progress,
            completed_count=completed,
            results_recorded_count=results_recorded,
            needs_attention_count=needs_attention,
            experiments=exps
        )
