from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ResearchProjectCreate(BaseModel):
    """Schema for creating a new Research Project."""
    name: str = Field(..., description="Project Name")
    description: Optional[str] = Field(None, description="Optional Project Description")
    status: Optional[str] = Field("ACTIVE", description="Project Status ('ACTIVE' or 'ARCHIVED')")


class ResearchProjectUpdate(BaseModel):
    """Schema for updating an existing Research Project."""
    name: Optional[str] = Field(None, description="Project Name")
    description: Optional[str] = Field(None, description="Project Description")
    status: Optional[str] = Field(None, description="Project Status ('ACTIVE' or 'ARCHIVED')")


class ResearchProjectResponse(BaseModel):
    """Schema for returning Research Project summary information."""
    id: int
    name: str
    description: Optional[str] = None
    status: str
    created_at: str
    updated_at: str
    paper_count: int = 0
    direction_count: int = 0
    proposal_count: int = 0


class ProjectPaperResponse(BaseModel):
    """Schema for returning assigned project papers with full metadata."""
    project_id: int
    paper_id: int
    title: str
    filename: str
    abstract: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    algorithms: List[str] = Field(default_factory=list)
    datasets: List[str] = Field(default_factory=list)
    methodologies: List[str] = Field(default_factory=list)
    application_domains: List[str] = Field(default_factory=list)
    uploaded_at: Optional[str] = None
    added_at: str


class BulkAddPapersRequest(BaseModel):
    """Schema for bulk paper assignment request."""
    paper_ids: List[int] = Field(..., description="List of ResearchPaper IDs to assign to project")


class BulkAddPapersResponse(BaseModel):
    """Schema for bulk paper assignment response."""
    added: List[int] = Field(default_factory=list, description="IDs of papers newly assigned")
    already_assigned: List[int] = Field(default_factory=list, description="IDs of papers already assigned")
    not_found: List[int] = Field(default_factory=list, description="IDs of papers not found in database")


class AvailablePaperResponse(BaseModel):
    """Schema for returning ResearchPaper records available for project assignment."""
    id: int
    title: str
    abstract: Optional[str] = None
    filename: str
    keywords: List[str] = Field(default_factory=list)
    algorithms: List[str] = Field(default_factory=list)
    datasets: List[str] = Field(default_factory=list)
    methodologies: List[str] = Field(default_factory=list)
    application_domains: List[str] = Field(default_factory=list)
    uploaded_at: str



class SavedDirectionCreate(BaseModel):
    """Schema for persisting a Research Direction snapshot under a project."""
    project_id: int = Field(..., description="Target Research Project ID")
    source_direction_id: Optional[str] = Field(None, description="Source Research Direction ID (e.g. dir_1)")
    title: str = Field(..., description="Direction Title")
    description: Optional[str] = Field(None, description="Direction Description / Proposed Direction")
    confidence: Optional[str] = Field(None, description="Confidence Level ('High', 'Moderate', 'Low')")
    direction_data: Dict[str, Any] = Field(..., description="Full immutable direction snapshot object")


class SavedDirectionResponse(BaseModel):
    """Schema for returning a saved Research Direction snapshot."""
    id: int
    project_id: int
    source_direction_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    confidence: Optional[str] = None
    direction_data: Dict[str, Any]
    created_at: str


class ProposalSummaryResponse(BaseModel):
    """Schema for returning proposal summary inside project details."""
    id: int
    proposal_uuid: str
    project_id: int
    source_direction_id: Optional[str] = None
    title: str
    status: str
    current_version_number: int = 1
    created_at: str
    updated_at: str


class ProjectDetailResponse(ResearchProjectResponse):
    """Schema for detailed Research Project view with assigned papers, directions, and proposals."""
    papers: List[ProjectPaperResponse] = Field(default_factory=list)
    saved_directions: List[SavedDirectionResponse] = Field(default_factory=list)
    proposals: List[ProposalSummaryResponse] = Field(default_factory=list)
