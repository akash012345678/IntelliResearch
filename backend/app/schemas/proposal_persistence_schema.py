from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ProposalCreate(BaseModel):
    """Schema for persisting a generated ProposalDraft under a Research Project."""
    project_id: int = Field(..., description="Target Research Project ID")
    source_direction_id: Optional[str] = Field(None, description="Source Research Direction ID")
    title: str = Field(..., description="Proposal Title")
    proposal_data: Dict[str, Any] = Field(..., description="Full structured ProposalDraft JSON object")
    generation_mode: Optional[str] = Field("template", description="Generation mode ('llm' or 'template')")
    status: Optional[str] = Field("DRAFT", description="Proposal status ('DRAFT', 'FINAL', 'ARCHIVED')")


class ProposalVersionCreate(BaseModel):
    """Schema for adding a new version to an existing Proposal."""
    proposal_data: Dict[str, Any] = Field(..., description="Full structured ProposalDraft JSON object for this version")
    generation_mode: Optional[str] = Field("template", description="Generation mode ('llm' or 'template')")


class ProposalVersionResponse(BaseModel):
    """Schema for returning a single ProposalVersion."""
    id: int
    proposal_id: int
    version_number: int
    proposal_data: Dict[str, Any]
    generation_mode: str
    change_summary: Optional[str] = None
    is_restored: bool = False
    created_at: str
    updated_at: str



class ProposalVersionListResponse(BaseModel):
    """Schema for returning version history of a proposal."""
    proposal_id: int
    total_versions: int
    versions: List[ProposalVersionResponse]


class ProposalResponse(BaseModel):
    """Schema for returning full saved Proposal detail with current version."""
    id: int
    proposal_uuid: str
    project_id: int
    source_direction_id: Optional[str] = None
    title: str
    status: str
    current_version: ProposalVersionResponse
    created_at: str
    updated_at: str
