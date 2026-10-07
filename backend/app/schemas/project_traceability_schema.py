from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class PaperTraceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    paper_id: int
    title: str
    authors: Optional[str] = None
    year: Optional[int] = None
    evidence_role: str = "[RECORDED_EVIDENCE]"
    supported_concept: str = "Primary Literature Evidence"


class ConceptTraceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    type: str = "concept"
    evidence_tag: str = "[RECORDED_EVIDENCE]"


class GapTraceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    gap_id: str
    title: str
    description: str
    gap_score: float = 0.8
    confidence: str = "Moderate"
    relationship_evidence: str = "Collection-scoped evidence"
    limitation_statement: Optional[str] = None
    status: str = "IDENTIFIED"


class OpportunityTraceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    direction_id: str
    title: str
    confidence: str = "High"
    classification: str = "EVIDENCE_GROUNDED_OPPORTUNITY"
    direction_score: float = 0.85
    research_question: Optional[str] = None
    description: Optional[str] = None


class QuestionsObjectivesTraceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    research_questions: List[str] = Field(default_factory=list)
    objectives: List[str] = Field(default_factory=list)
    hypotheses: List[str] = Field(default_factory=list)
    evidence_tag: str = "[PROPOSED]"


class PlanTraceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    plan_id: Optional[int] = None
    status: str = "NOT_CREATED"  # SAVED, DRAFT, NOT_CREATED
    methodology_title: Optional[str] = None
    baseline_methods: List[str] = Field(default_factory=list)
    proposed_architecture: Optional[str] = None
    datasets: List[str] = Field(default_factory=list)
    experiment_count: int = 0


class ExperimentTraceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    experiment_id: int
    title: str
    type: str = "BASELINE_COMPARISON"
    execution_status: str = "PLANNED"  # PLANNED, COMPLETED, NOT_EXECUTED
    baseline: str = "Standard Baseline"
    proposed_method: str = "Proposed Architecture"
    configured_metrics: List[str] = Field(default_factory=list)
    result_runs_count: int = 0
    result_rows_count: int = 0
    result_status: str = "MISSING"  # RESULTS_RECORDED, COMPLETED_NO_RESULTS, MISSING


class ResultsTraceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    results_recorded: bool = False
    run_count: int = 0
    result_row_count: int = 0
    experiments_count: int = 0
    completed_experiments_count: int = 0
    experiments_with_results_count: int = 0
    metrics_recorded: List[Dict[str, Any]] = Field(default_factory=list)
    completion_status: str = "RESULTS_NOT_RECORDED"  # ALL_RESULTS_RECORDED, PARTIAL_RESULTS, RESULTS_NOT_RECORDED, COMPLETED_NO_RESULTS
    notice: str = "Experimental measurements have not yet been recorded. [MISSING]"


class VersionTraceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    version_id: int
    version_number: int
    created_at: Optional[str] = None
    source_type: str = "TEMPLATE"  # TEMPLATE, MANUAL, AI_REFINED
    is_current: bool = False


class ProposalTraceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    proposal_id: Optional[int] = None
    proposal_uuid: Optional[str] = None
    title: str = "Proposal Not Created Yet"
    status: str = "NOT_CREATED"  # DRAFT, COMPLETED, NOT_CREATED
    current_version_number: Optional[int] = None
    is_created: bool = False


class ReportTraceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str = "READY_FOR_EXPORT"  # NOT_GENERATED, GENERATED, READY_FOR_EXPORT
    generated_at: Optional[str] = None
    report_title: Optional[str] = None


class TraceabilityChainItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chain_id: str
    opportunity: OpportunityTraceItem
    gap: GapTraceItem
    papers: List[PaperTraceItem] = Field(default_factory=list)
    concepts: List[ConceptTraceItem] = Field(default_factory=list)
    questions_objectives: QuestionsObjectivesTraceItem
    plan: PlanTraceItem
    experiments: List[ExperimentTraceItem] = Field(default_factory=list)
    results: ResultsTraceItem
    proposal: ProposalTraceItem
    versions: List[VersionTraceItem] = Field(default_factory=list)
    report: ReportTraceItem


class TraceabilitySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_papers: int = 0
    total_gaps: int = 0
    total_opportunities: int = 0
    saved_plans: int = 0
    planned_experiments: int = 0
    completed_experiments: int = 0
    recorded_result_runs: int = 0
    recorded_result_rows: int = 0
    created_proposals: int = 0
    final_report_status: str = "READY_FOR_EXPORT"
    stage_statuses: Dict[str, str] = Field(default_factory=dict)


class ProjectTraceabilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    project_id: int
    project_name: str
    summary: TraceabilitySummary
    chains: List[TraceabilityChainItem] = Field(default_factory=list)
