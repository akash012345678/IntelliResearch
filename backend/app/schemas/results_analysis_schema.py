from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class MetricAnalysisItem(BaseModel):
    metric_name: str
    baseline_value: Optional[str] = None
    proposed_value: Optional[str] = None
    unit: Optional[str] = None
    abs_difference: Optional[float] = None
    rel_difference_pct: Optional[str] = None
    direction: str = "higher_is_better"  # 'higher_is_better' | 'lower_is_better'
    is_improved: Optional[bool] = None
    interpretation: str


class TradeoffAnalysisItem(BaseModel):
    tradeoff_type: str  # e.g. "Accuracy vs Latency"
    description: str
    impact_assessment: str


class MultiRunStatsItem(BaseModel):
    metric_name: str
    run_count: int
    mean: float
    std_dev: float
    min_val: float
    max_val: float
    range_val: float
    consistency_rating: str  # 'LOW_VARIATION' | 'MODERATE_VARIATION' | 'HIGH_VARIATION'
    notes: str


class AblationAnalysisItem(BaseModel):
    full_model: str
    component_removed: str
    ablation_variant: str
    metric_name: str
    full_val: str
    ablation_val: str
    abs_difference: float
    interpretation: str


class HypothesisAssessmentItem(BaseModel):
    research_question: Optional[str] = None
    hypothesis_h0: Optional[str] = None
    hypothesis_h1: Optional[str] = None
    observed_result_summary: str
    assessment_status: str  # 'CONSISTENT_WITH_H1' | 'CONSISTENT_WITH_H0' | 'INCONCLUSIVE' | 'INSUFFICIENT_DATA'
    academic_explanation: str


class EvidenceStrengthItem(BaseModel):
    rating: str  # 'STRONGER' | 'MODERATE' | 'LIMITED' | 'INSUFFICIENT'
    score: int   # 0 to 100
    factors: List[str] = []
    explanation: str


class ReproducibilitySummaryItem(BaseModel):
    checklist_score: int  # X / 10
    completed_items: List[str] = []
    missing_items: List[str] = []
    reproducibility_level: str


class SingleExperimentAnalysisResponse(BaseModel):
    experiment_id: int
    experiment_name: str
    experiment_type: str
    status: str
    dataset_name: str
    baseline_alg: str
    proposed_arch: str
    run_count: int
    metrics_count: int
    metrics_analysis: List[MetricAnalysisItem] = []
    tradeoffs: List[TradeoffAnalysisItem] = []
    multi_run_stats: List[MultiRunStatsItem] = []
    ablation_analysis: List[AblationAnalysisItem] = []
    hypothesis_assessment: HypothesisAssessmentItem
    evidence_strength: EvidenceStrengthItem
    reproducibility: ReproducibilitySummaryItem
    recorded_limitations: Optional[str] = None
    safe_conclusion: str
    recommended_next_steps: List[str] = []


class ProjectResultsAnalysisSummaryResponse(BaseModel):
    total_experiments: int
    completed_experiments: int
    results_recorded_count: int
    baseline_comparisons_count: int
    ablation_experiments_count: int
    multi_run_experiments_count: int
    hypotheses_evaluated_count: int
    limitations_recorded_count: int
    has_recorded_results: bool
    notice: str
    experiments_analysis: List[SingleExperimentAnalysisResponse] = []
    project_overall_conclusion: str
    decision_guidance: List[str] = []
