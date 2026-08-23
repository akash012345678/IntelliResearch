from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class CollectionEvidenceSummary(BaseModel):
    paper_count: int
    supporting_papers_count: int
    supporting_papers: List[Dict[str, Any]] = []
    relevant_algorithms: List[str] = []
    relevant_datasets: List[str] = []
    relevant_concepts: List[str] = []
    gap_score_pct: float
    semantic_relevance_pct: float
    collection_support_pct: float


class LiteratureSearchResultItem(BaseModel):
    title: str
    authors: Optional[List[str]] = []
    year: Optional[int] = None
    source: str  # 'Collection Search' | 'Semantic Search' | 'External Literature'
    relevance_explanation: str
    is_possibly_related_work: bool = False
    url: Optional[str] = None


class ExternalValidationSummary(BaseModel):
    status: str  # 'not_performed' | 'performed' | 'provider_unavailable'
    results: List[LiteratureSearchResultItem] = []


class LiteratureSearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)


class LiteratureSearchResponse(BaseModel):
    query: str
    results: List[LiteratureSearchResultItem]
    total_results: int
    provider: str


class OpportunityValidationResponse(BaseModel):
    direction_id: str
    title: str
    scope: str  # 'global' | 'project'
    validation_status: str  # 'strongly_supported' | 'needs_further_validation' | 'weak_evidence' | 'overlap_detected'
    
    collection_summary: CollectionEvidenceSummary
    core_assumption: str
    suggested_search_queries: List[str] = []
    validation_checklist: List[str] = []
    external_validation: ExternalValidationSummary
    possible_overlap_warning: Optional[str] = None
    refinement_areas: List[str] = []
    invalidation_conditions: List[str] = []
    validation_summary_text: str
    recommended_action: str  # 'proceed_to_proposal' | 'perform_broader_search' | 'refine_research_idea'
    disclaimer: str
