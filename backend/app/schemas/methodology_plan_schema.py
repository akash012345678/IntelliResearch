from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class PipelineStepItem(BaseModel):
    step_number: int
    stage: str
    title: str
    description: str


class DatasetPlanItem(BaseModel):
    name: str
    status: str  # 'Observed in current collection' | 'Candidate benchmark dataset' | 'Observed dataset (Requires Verification / Adaptation)'
    suitability: str
    limitations: str
    licensing: str
    supporting_paper: Optional[str] = None
    evidence_task: Optional[str] = None
    annotation_type: Optional[str] = None
    suitability_class: Optional[str] = None  # 'DIRECTLY_SUITABLE' | 'REQUIRES_VERIFICATION' | 'NOT_SUITABLE'


class ExperimentParameterItem(BaseModel):
    parameter: str
    value: str
    category: str  # 'MODEL' | 'DATASET' | 'SPLIT' | 'SEED' | 'HYPERPARAMETER' | 'RESULT'
    provenance_status: str  # 'RECORDED_EVIDENCE' | 'PROPOSED' | 'MISSING'
    source_evidence: Optional[str] = None


class BaselineMethodItem(BaseModel):
    algorithm: str
    supporting_paper_count: int
    role: str
    reason: str


class ExperimentPlanItem(BaseModel):
    experiment_number: int
    title: str
    purpose: str
    variables: str
    baseline: str
    metrics: List[str]


class MetricCategoryItem(BaseModel):
    category: str  # 'Classification' | 'Regression' | 'Detection' | 'Efficiency'
    metrics: List[str]


class AblationStepItem(BaseModel):
    step_name: str
    component_removed: str
    purpose: str


class ExpectedOutputItem(BaseModel):
    output_type: str  # 'Table' | 'Figure' | 'Report'
    title: str
    description: str


class HypothesesItem(BaseModel):
    null_hypothesis: str
    alternative_hypothesis: str


class MethodologyPlanResponse(BaseModel):
    direction_id: str
    title: str
    scope: str  # 'global' | 'project'
    validation_status: str
    
    # 24 Structured Sections
    research_problem: str
    problem_context: str
    supporting_papers: List[Dict[str, Any]] = []
    objectives: List[str] = []
    research_questions: List[Dict[str, str]] = []  # [{'rq_id': 'RQ1', 'question': '...'}]
    pipeline: List[PipelineStepItem] = []
    dataset_plan: List[DatasetPlanItem] = []
    data_preparation: List[str] = []
    baseline_methods: List[BaselineMethodItem] = []
    proposed_method: Dict[str, Any] = {}
    experiments: List[ExperimentPlanItem] = []
    metrics: List[MetricCategoryItem] = []
    ablation_plan: List[AblationStepItem] = []
    variables: Dict[str, List[str]] = {}  # {'independent': [], 'dependent': [], 'control': []}
    experiment_parameters: List[ExperimentParameterItem] = []
    expected_outputs: List[ExpectedOutputItem] = []
    success_criteria: List[str] = []
    risks: List[str] = []
    reproducibility_checklist: List[str] = []
    timeline: List[Dict[str, str]] = []  # [{'week': 'Week 1-2', 'task': '...'}]
    implementation_checklist: List[str] = []
    potential_contribution: str
    hypotheses: HypothesesItem
    traceability: Dict[str, Any] = {}
    disclaimer: str


class SaveResearchPlanRequest(BaseModel):
    direction_id: str
    plan_data: Dict[str, Any]
    notes: Optional[str] = None
