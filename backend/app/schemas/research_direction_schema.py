from pydantic import BaseModel, Field
from typing import List, Optional


class ResearchDirectionEvidence(BaseModel):
    """
    Quantitative evidence metrics for a candidate research direction.
    """
    gap_score: float = Field(..., description="Multi-signal gap score [0.0 - 1.0]")
    opportunity_score: Optional[float] = Field(None, description="Composite opportunity relevance score [0.0 - 1.0]")
    semantic_evidence: float = Field(..., description="Maximum SBERT cosine similarity [0.0 - 1.0]")
    link_prediction_score: float = Field(..., description="Knowledge Graph link prediction score [0.0 - 1.0]")
    collection_coverage: float = Field(..., description="Percentage coverage across collection [0.0 - 100.0]")
    underrepresentation_score: float = Field(..., description="Concept underrepresentation score [0.0 - 1.0]")
    evidence_classification: Optional[str] = Field(None, description="Evidence classification tier")


class SupportingPaper(BaseModel):
    """
    Research paper contributing evidence to a candidate research direction.
    """
    paper_id: int
    title: str
    role: str


class CandidateAlgorithm(BaseModel):
    """
    Algorithm entity identified as a candidate for the research direction.
    """
    name: str
    supporting_paper_count: int
    reason: str


class CandidateDataset(BaseModel):
    """
    Dataset entity identified as a candidate for the research direction.
    """
    name: str
    supporting_paper_count: int
    reason: str


class CandidateMethodology(BaseModel):
    """
    Methodology entity identified as a candidate for the research direction.
    """
    name: str
    paper_count: int
    coverage_percentage: float


class ResearchDirection(BaseModel):
    """
    Complete structured proposal model for an actionable research direction.
    """
    direction_id: str
    opportunity_family_id: Optional[str] = Field(None, description="Research question family identifier")
    parent_gap_id: Optional[str] = Field(None, description="ID of parent qualified research gap")
    gap_relationship_key: Optional[str] = Field(None, description="Canonical relationship key of parent gap")
    gap_type: Optional[str] = Field(None, description="Gap classification type")
    gap_evidence_class: Optional[str] = Field(None, description="Evidence classification tier of parent gap")
    gap_evidence_score: Optional[float] = Field(None, description="Relationship evidence score of parent gap")
    source_paper_ids: Optional[List[int]] = Field(default_factory=list, description="IDs of direct supporting source papers")
    title: str
    research_question: Optional[str] = Field(None, description="Explicit research question being investigated")
    research_problem: str
    motivation: str
    existing_evidence: List[str]
    missing_aspect: str
    proposed_direction: str
    supporting_papers: List[SupportingPaper]
    supporting_concepts: List[str]
    candidate_algorithms: List[CandidateAlgorithm]
    candidate_datasets: List[CandidateDataset]
    candidate_methodologies: List[CandidateMethodology]
    evidence: ResearchDirectionEvidence
    direction_score: float = Field(..., description="Weighted composite direction score [0.0 - 1.0]")
    confidence: str = Field(..., description="Confidence classification: High, Moderate, or Low")
    disclaimer: str


class ResearchDirectionResponse(BaseModel):
    """
    API Response model for GET /api/research-directions.
    """
    total_directions: int
    directions: List[ResearchDirection]
    collection_disclaimer: str
