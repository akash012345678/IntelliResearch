from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ProjectCollectionSummary(BaseModel):
    """Summary metrics of papers assigned to a research project."""
    total_papers: int = 0
    total_nodes: int = 0
    total_edges: int = 0
    total_keywords: int = 0
    total_algorithms: int = 0
    total_datasets: int = 0
    total_methodologies: int = 0
    total_domains: int = 0


class ProjectPaperLandscapeItem(BaseModel):
    """Summary of a paper assigned to a research project."""
    id: int
    title: str
    abstract: Optional[str] = None
    year: Optional[int] = None
    authors: Optional[List[str]] = []
    keywords: List[str] = []
    algorithms: List[str] = []
    datasets: List[str] = []
    methodologies: List[str] = []
    application_domains: List[str] = []



class ProjectSharedConcept(BaseModel):
    """Concept extracted across project papers with coverage analysis."""
    name: str
    type: str  # 'keyword' | 'algorithm' | 'dataset' | 'methodology' | 'domain'
    paper_count: int
    coverage_percentage: float
    classification: str  # 'COMMON' | 'UNDERREPRESENTED'
    papers: List[Dict[str, Any]] = []


class ProjectPaperRelationship(BaseModel):
    """Pairwise semantic relationship between two project papers."""
    source_paper_id: int
    source_paper_title: str
    target_paper_id: int
    target_paper_title: str
    similarity_score: float
    shared_concepts: List[str] = []


class ProjectGap(BaseModel):
    """Identified research gap within the project paper collection."""
    gap_id: str
    source_paper_id: int
    source_paper_title: str
    missing_concept: str
    concept_type: str
    relationship_type: str
    gap_score: float
    confidence: str
    evidence: Dict[str, Any] = {}
    explanation: str


class ProjectUnderrepresentedConcept(BaseModel):
    """Rare concept within the project collection worth exploring."""
    name: str
    type: str
    paper_count: int
    coverage_percentage: float
    related_paper_count: int
    explanation: str


class ProjectResearchDirection(BaseModel):
    """Actionable candidate research direction generated from project evidence."""
    direction_id: str
    title: str
    description: str
    research_problem: Optional[str] = None
    motivation: Optional[str] = None
    missing_aspect: Optional[str] = None
    proposed_direction: Optional[str] = None
    supporting_papers: List[Dict[str, Any]] = []
    supporting_concepts: List[str] = []
    candidate_algorithms: List[Dict[str, Any]] = []
    candidate_datasets: List[Dict[str, Any]] = []
    evidence: Dict[str, Any] = {}
    confidence: str
    disclaimer: str


class ProjectProposalTraceability(BaseModel):
    """Traceability mapping connecting project papers -> evidence -> directions -> saved proposal."""
    proposal_id: int
    proposal_uuid: str
    title: str
    status: str
    current_version_number: int
    source_direction_id: Optional[str] = None
    supporting_papers: List[Dict[str, Any]] = []
    supporting_concepts: List[str] = []


class ProjectResearchIntelligenceResponse(BaseModel):
    """Complete project-scoped research intelligence response."""
    project: Dict[str, Any]
    collection_summary: ProjectCollectionSummary
    paper_landscape: List[ProjectPaperLandscapeItem]
    shared_concepts: Dict[str, List[ProjectSharedConcept]]
    paper_relationships: List[ProjectPaperRelationship]
    research_gaps: List[ProjectGap]
    underrepresented_concepts: List[ProjectUnderrepresentedConcept]
    candidate_research_directions: List[ProjectResearchDirection]
    proposal_traceability: List[ProjectProposalTraceability]
    insight_summary: str
