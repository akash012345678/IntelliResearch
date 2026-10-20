from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class ExperimentResultCreate(BaseModel):
    metric_name: str
    metric_value: str
    unit: Optional[str] = None
    method_type: str = "proposed"  # 'baseline' | 'proposed' | 'ablation'
    notes: Optional[str] = None


class ExperimentResultResponse(BaseModel):
    id: int
    run_id: int
    metric_name: str
    metric_value: str
    unit: Optional[str] = None
    method_type: str
    notes: Optional[str] = None
    created_at: str


class ExperimentRunCreate(BaseModel):
    seed: Optional[int] = 42
    duration_seconds: Optional[int] = None
    notes: Optional[str] = None
    results: List[ExperimentResultCreate] = []


class ExperimentRunResponse(BaseModel):
    id: int
    experiment_id: int
    run_number: int
    seed: Optional[int] = 42
    duration_seconds: Optional[int] = None
    notes: Optional[str] = None
    created_at: str
    results: List[ExperimentResultResponse] = []


class ExperimentCreate(BaseModel):
    direction_id: Optional[str] = None
    name: str
    purpose: Optional[str] = None
    experiment_type: str = "BASELINE_COMPARISON"  # BASELINE_COMPARISON, ABLATION, DATASET_COMPARISON, etc.
    status: str = "PLANNED"  # PLANNED, READY, IN_PROGRESS, COMPLETED, BLOCKED, CANCELLED
    research_question: Optional[str] = None
    hypothesis_h0: Optional[str] = None
    hypothesis_h1: Optional[str] = None
    dataset_config: Optional[Dict[str, Any]] = None
    baseline_config: Optional[Dict[str, Any]] = None
    proposed_config: Optional[Dict[str, Any]] = None
    environment_config: Optional[Dict[str, Any]] = None
    execution_config: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    limitations: Optional[str] = None
    reproducibility_checklist: Optional[List[str]] = None


class ExperimentUpdate(BaseModel):
    name: Optional[str] = None
    purpose: Optional[str] = None
    experiment_type: Optional[str] = None
    status: Optional[str] = None
    research_question: Optional[str] = None
    hypothesis_h0: Optional[str] = None
    hypothesis_h1: Optional[str] = None
    dataset_config: Optional[Dict[str, Any]] = None
    baseline_config: Optional[Dict[str, Any]] = None
    proposed_config: Optional[Dict[str, Any]] = None
    environment_config: Optional[Dict[str, Any]] = None
    execution_config: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    limitations: Optional[str] = None
    reproducibility_checklist: Optional[List[str]] = None


class ExperimentResponse(BaseModel):
    id: int
    project_id: int
    direction_id: Optional[str] = None
    name: str
    purpose: Optional[str] = None
    experiment_type: str
    status: str
    research_question: Optional[str] = None
    hypothesis_h0: Optional[str] = None
    hypothesis_h1: Optional[str] = None
    dataset_config: Optional[Dict[str, Any]] = None
    baseline_config: Optional[Dict[str, Any]] = None
    proposed_config: Optional[Dict[str, Any]] = None
    environment_config: Optional[Dict[str, Any]] = None
    execution_config: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    limitations: Optional[str] = None
    reproducibility_checklist: Optional[List[str]] = None
    created_at: str
    updated_at: str
    runs: List[ExperimentRunResponse] = []


class ExperimentSummaryResponse(BaseModel):
    total_planned: int
    not_started_count: int
    in_progress_count: int
    completed_count: int
    results_recorded_count: int
    needs_attention_count: int
    experiments: List[ExperimentResponse] = []


class ImportPlanExperimentsRequest(BaseModel):
    direction_id: str


class ImportPlanExperimentsResponse(BaseModel):
    project_id: int
    research_plan_id: Optional[str] = None
    opportunity_id: Optional[str] = None
    imported_count: int
    skipped_count: int
    message: str
    experiments: List[ExperimentResponse] = []

