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
    total_metrics: int = 0
    total_tasks: int = 0
    total_applications: int = 0


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
    metrics: List[str] = []
    tasks: List[str] = []
    applications: List[str] = []
    keyword_details: List[Dict[str, Any]] = []
    algorithm_details: List[Dict[str, Any]] = []
    dataset_details: List[Dict[str, Any]] = []
    methodology_details: List[Dict[str, Any]] = []


class ProjectSharedConcept(BaseModel):
    """Concept extracted across project papers with coverage analysis."""
    name: str
    type: str  # 'keyword' | 'algorithm' | 'dataset' | 'methodology' | 'domain' | 'metric' | 'task' | 'application'
    paper_count: int
    coverage_percentage: float
    classification: str  # 'COMMON' | 'UNDERREPRESENTED'
    roles: List[str] = []
    papers: List[Dict[str, Any]] = []
    evidence_text: Optional[str] = None
    evidence_section: Optional[str] = None


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
    gap_type: Optional[str] = "CROSS_PAPER_COMPARISON"
    title: Optional[str] = None
    description: Optional[str] = None
    source_paper_id: Optional[int] = 0
    source_paper_title: Optional[str] = "Project Papers"
    source_papers: List[Dict[str, Any]] = []
    supported_paper_count: Optional[int] = 0
    related_concepts: List[str] = []
    missing_concept: str
    concept_type: str
    relationship_type: str = "uses_algorithm"
    gap_score: float
    confidence: str
    eligibility_status: Optional[str] = "QUALIFIED_POTENTIAL_GAP"
    evidence: Dict[str, Any] = {}
    gap_reasoning: Optional[Dict[str, Any]] = {}
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
    opportunity_family_id: Optional[str] = None
    parent_gap_id: Optional[str] = None
    gap_relationship_key: Optional[str] = None
    gap_type: Optional[str] = None
    gap_evidence_class: Optional[str] = None
    gap_evidence_score: Optional[float] = None
    source_paper_ids: Optional[List[int]] = []
    title: str
    research_question: Optional[str] = None
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
