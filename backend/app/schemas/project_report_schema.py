from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class ProjectSummaryInfo(BaseModel):
    """Basic project information header for project research report."""
    model_config = ConfigDict(from_attributes=True)

    project_id: int
    name: str
    description: Optional[str] = None
    status: str = "ACTIVE"


class ResearchProblemSummary(BaseModel):
    """Derived dominant research focus and themes from project paper collection."""
    model_config = ConfigDict(from_attributes=True)

    dominant_domains: List[str] = Field(default_factory=list)
    dominant_methods: List[str] = Field(default_factory=list)
    dominant_algorithms: List[str] = Field(default_factory=list)
    dominant_research_themes: List[str] = Field(default_factory=list)
    summary_text: Optional[str] = None


class TraceabilityConcept(BaseModel):
    """Concept node in evidence traceability chain."""
    model_config = ConfigDict(from_attributes=True)

    type: str
    name: str


class TraceabilityGap(BaseModel):
    """Gap node in evidence traceability chain."""
    model_config = ConfigDict(from_attributes=True)

    gap_score: float
    confidence: str
    missing_concept: Optional[str] = None


class TraceabilityDirection(BaseModel):
    """Direction node in evidence traceability chain."""
    model_config = ConfigDict(from_attributes=True)

    direction_id: str
    title: str


class TraceabilityProposal(BaseModel):
    """Proposal node in evidence traceability chain."""
    model_config = ConfigDict(from_attributes=True)

    proposal_id: str
    db_id: Optional[int] = None
    title: str
    latest_version: int = 1


class EvidenceTraceabilityItem(BaseModel):
    """
    Consolidated evidence traceability chain connecting:
    Paper -> Concept -> Gap -> Direction -> Proposal -> Proposal Version
    """
    model_config = ConfigDict(from_attributes=True)

    paper_id: int
    paper_title: str
    concept: Optional[TraceabilityConcept] = None
    gap: Optional[TraceabilityGap] = None
    research_direction: Optional[TraceabilityDirection] = None
    proposal: Optional[TraceabilityProposal] = None


class ProposalSummaryItem(BaseModel):
    """Project-scoped research proposal summary with supporting paper links."""
    model_config = ConfigDict(from_attributes=True)

    proposal_id: str
    db_id: Optional[int] = None
    title: str
    status: str = "DRAFT"
    generation_mode: str = "TEMPLATE"
    latest_version: int = 1
    supporting_papers: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_summary: Dict[str, Any] = Field(default_factory=dict)
    source_direction: Optional[str] = None


class ProjectResearchReportResponse(BaseModel):
    """
    Structured Pydantic response for a project-level consolidated research report.
    Consolidates 12 analytical sections strictly scoped to assigned project papers.
    """
    model_config = ConfigDict(from_attributes=True)

    project: ProjectSummaryInfo
    collection_summary: Dict[str, Any] = Field(default_factory=dict)
    paper_landscape: List[Dict[str, Any]] = Field(default_factory=list)
    research_problem_summary: ResearchProblemSummary
    shared_concepts: Dict[str, Any] = Field(default_factory=dict)
    paper_relationships: List[Dict[str, Any]] = Field(default_factory=list)
    research_gaps: List[Dict[str, Any]] = Field(default_factory=list)
    underrepresented_concepts: List[Dict[str, Any]] = Field(default_factory=list)
    candidate_research_directions: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_traceability: List[EvidenceTraceabilityItem] = Field(default_factory=list)
    proposal_summary: List[ProposalSummaryItem] = Field(default_factory=list)
    collection_disclaimer: str

