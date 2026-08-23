from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class SupportingPaperSummary(BaseModel):
    paper_id: int
    title: str
    role: str
    key_methods: List[str] = []


class TechItem(BaseModel):
    name: str
    category: str  # 'supported_by_collection' | 'candidate_for_further_investigation'
    supporting_paper_count: int = 0
    reason: str


class DatasetConsideration(BaseModel):
    name: str
    observed_in_collection_count: int = 0
    observed_papers: List[str] = []
    suitability_context: str
    potential_limitation: str


class ExperimentStep(BaseModel):
    step_number: int
    title: str
    description: str
    metrics_to_evaluate: List[str] = []


class PipelineStep(BaseModel):
    step_number: int
    stage: str  # 'INPUT' | 'FEATURE_EXTRACTION' | 'MODELING' | 'CLASSIFICATION' | 'OUTPUT'
    title: str
    description: str


class EvidenceMetrics(BaseModel):
    relationship_strength: float = Field(..., description="Knowledge Graph link prediction / structural strength [0-100]")
    semantic_relevance: float = Field(..., description="SBERT cosine similarity relevance [0-100]")
    collection_support: float = Field(..., description="Collection coverage support percentage [0-100]")
    underrepresentation: float = Field(..., description="Concept underrepresentation score [0-100]")
    overall_gap_score: float = Field(..., description="Multi-signal gap score [0-100]")


class IdeaScorecardItem(BaseModel):
    metric_name: str
    score_percentage: float
    rating_label: str  # 'Strong' | 'Moderate' | 'Needs Investigation'
    explanation: str


class IdeaScorecard(BaseModel):
    metrics: List[IdeaScorecardItem]
    overall_verdict: str  # e.g. "🟡 PROMISING — INVESTIGATE FURTHER"


class OpportunityEvaluationResponse(BaseModel):
    opportunity_id: str
    title: str
    confidence: str  # 'HIGH' | 'MODERATE' | 'LOW'
    scope_tag: str   # 'Promising within current collection' | 'Project evidence only'
    
    # Core Sections
    research_problem: str
    what_current_research_does: List[SupportingPaperSummary]
    what_is_missing: str
    why_relevant: str
    
    # Evidence & Metrics
    evidence: EvidenceMetrics
    technical_evidence_details: Dict[str, Any] = {}
    
    # Build & Tech
    implementation_preview: List[PipelineStep]
    candidate_algorithms: List[TechItem]
    candidate_datasets: List[TechItem]
    dataset_considerations: List[DatasetConsideration]
    
    # Experiment & Contribution
    experiment_plan: List[ExperimentStep]
    possible_contribution: str
    limitations: List[str]
    
    # Student Helper & Scorecard
    scorecard: IdeaScorecard
    why_consider_this: List[str]
    validation_checklist: List[str]
    
    disclaimer: str
