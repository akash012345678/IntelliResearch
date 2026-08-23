from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class NextStepRecommendation(BaseModel):
    stage_id: str
    stage_title: str
    recommended_action_title: str
    why_this_matters: str
    completed_prerequisites: List[str] = []
    action_button_label: str
    target_tab: str
    expected_outcome: str


class ProjectHealthSummary(BaseModel):
    evidence_completeness_percentage: int
    citation_completeness_percentage: int
    experiment_completeness_percentage: int
    reproducibility_percentage: int
    document_readiness_percentage: int
    overall_readiness_score: int
    calculation_explanation: str


class SubmissionReadinessItem(BaseModel):
    check_name: str
    status: str  # 'PASSED' | 'WARNING' | 'FAILED'
    badge_text: str
    explanation: str


class ProjectDashboardAggregateResponse(BaseModel):
    project_id: int
    project_title: str
    status: str
    paper_count: int
    current_stage_id: str
    current_stage_title: str
    progress_percentage: int
    next_step: NextStepRecommendation
    health: ProjectHealthSummary
    submission_readiness: List[SubmissionReadinessItem] = []
    completed_milestones: List[str] = []
    upcoming_milestones: List[str] = []
