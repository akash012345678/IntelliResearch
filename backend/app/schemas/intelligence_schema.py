from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class CollectionSummarySchema(BaseModel):
    total_papers: int
    total_graph_nodes: int
    total_graph_edges: int
    total_keywords: int
    total_algorithms: int
    total_datasets: int
    total_methodologies: int
    total_domains: int
    total_potential_gaps: int
    total_link_prediction_candidates: int


class PaperLandscapeItemSchema(BaseModel):
    paper_id: int
    title: str
    abstract: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    algorithms: List[str] = Field(default_factory=list)
    datasets: List[str] = Field(default_factory=list)
    methodologies: List[str] = Field(default_factory=list)
    application_domains: List[str] = Field(default_factory=list)


class ConceptCoverageItemSchema(BaseModel):
    name: str
    paper_count: int
    coverage_percentage: float


class SharedConceptsSchema(BaseModel):
    keywords: List[ConceptCoverageItemSchema] = Field(default_factory=list)
    algorithms: List[ConceptCoverageItemSchema] = Field(default_factory=list)
    datasets: List[ConceptCoverageItemSchema] = Field(default_factory=list)
    methodologies: List[ConceptCoverageItemSchema] = Field(default_factory=list)
    domains: List[ConceptCoverageItemSchema] = Field(default_factory=list)


class PaperRelationshipItemSchema(BaseModel):
    source_paper_id: int
    source_title: str
    target_paper_id: int
    target_title: str
    similarity_score: float


class ResearchGapSummarySchema(BaseModel):
    total_gaps: int
    high_confidence: int
    moderate_confidence: int
    low_confidence: int


class UnderrepresentedConceptItemSchema(BaseModel):
    name: str
    type: str
    paper_count: int
    coverage_percentage: float
    related_paper_count: int
    reason: str


class CandidateResearchDirectionEvidenceSchema(BaseModel):
    gap_score: float
    semantic_evidence: float
    collection_coverage: float


class CandidateResearchDirectionSchema(BaseModel):
    title: str
    description: str
    supporting_papers: List[str] = Field(default_factory=list)
    supporting_concepts: List[str] = Field(default_factory=list)
    evidence: CandidateResearchDirectionEvidenceSchema
    confidence: str
    disclaimer: str


class GlobalResearchIntelligenceResponse(BaseModel):
    collection_summary: CollectionSummarySchema
    paper_landscape: List[PaperLandscapeItemSchema] = Field(default_factory=list)
    shared_concepts: SharedConceptsSchema
    paper_relationships: List[PaperRelationshipItemSchema] = Field(default_factory=list)
    research_gap_summary: ResearchGapSummarySchema
    gaps: List[Dict[str, Any]] = Field(default_factory=list)
    underrepresented_concepts: List[UnderrepresentedConceptItemSchema] = Field(default_factory=list)
    candidate_research_directions: List[CandidateResearchDirectionSchema] = Field(default_factory=list)
    collection_disclaimer: str
