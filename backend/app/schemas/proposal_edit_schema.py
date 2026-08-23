from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ProposalEditRequest(BaseModel):
    """
    Schema for submitting manual section edits to an existing proposal.
    Protected empirical evidence fields (supporting_papers, evidence_summary,
    source_direction_id, generation_timestamp, disclaimer, proposal_id)
    cannot be modified.
    """
    change_summary: str = Field(..., description="Human-readable description of what changed in this edit")
    title: Optional[str] = Field(None, description="Updated Title")
    abstract: Optional[str] = Field(None, description="Updated Executive Abstract")
    problem_statement: Optional[str] = Field(None, description="Updated Problem Statement")
    research_motivation: Optional[str] = Field(None, description="Updated Research Motivation")
    related_work_synthesis: Optional[str] = Field(None, description="Updated Related Work Synthesis")
    research_gap: Optional[str] = Field(None, description="Updated Identified Research Gap")
    proposed_methodology: Optional[str] = Field(None, description="Updated Proposed Methodology")
    candidate_algorithms: Optional[List[str]] = Field(None, description="Updated Candidate Algorithms list")
    candidate_datasets: Optional[List[str]] = Field(None, description="Updated Candidate Datasets list")
    dataset_evaluation_plan: Optional[str] = Field(None, description="Updated Dataset Evaluation Plan")
    experimental_plan: Optional[str] = Field(None, description="Updated Experimental Plan")
    evaluation_metrics: Optional[List[str]] = Field(None, description="Updated Evaluation Metrics list")
    expected_contribution: Optional[str] = Field(None, description="Updated Expected Contribution")
    limitations: Optional[str] = Field(None, description="Updated Limitations")


class SectionChangeItem(BaseModel):
    """Represents a section-level difference between two versions."""
    section: str
    changed: bool
    before: Any = None
    after: Any = None


class ProposalComparisonResponse(BaseModel):
    """Schema for returning diff comparison results between two proposal versions."""
    proposal_id: int
    version_a: int
    version_b: int
    total_changes: int
    changes: List[SectionChangeItem]
