from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ProposalDraftRequest(BaseModel):
    """
    Request model for generating a structured proposal draft from a research direction.
    """
    direction_id: str = Field(..., description="ID of the research direction (e.g. dir_1)")


class ProposalDraft(BaseModel):
    """
    Structured academic research proposal draft synthesized from collection evidence.
    """
    proposal_id: str = Field(..., description="Unique proposal ID")
    source_direction_id: Optional[str] = Field(None, description="Source research direction ID")
    title: str = Field(..., description="Proposal Title")
    abstract: str = Field(..., description="Executive Abstract")
    problem_statement: str = Field(..., description="Problem Statement")
    research_motivation: str = Field(..., description="Research Motivation")
    related_work_synthesis: str = Field(..., description="Related Work Synthesis citing supporting papers")
    research_gap: str = Field(..., description="Identified Collection Research Gap")
    proposed_methodology: str = Field(..., description="Proposed Methodology Plan")
    candidate_algorithms: List[str] = Field(default_factory=list, description="Candidate Algorithms")
    candidate_datasets: List[str] = Field(default_factory=list, description="Candidate Datasets")
    dataset_evaluation_plan: str = Field(..., description="Dataset Evaluation Plan")
    experimental_plan: str = Field(..., description="Experimental Plan & Baseline Comparisons")
    evaluation_metrics: str = Field(..., description="Evaluation Metrics & Performance Benchmarks")
    expected_contribution: str = Field(..., description="Expected Academic & Technical Contribution")
    limitations: str = Field(..., description="Collection Limitations & Study Assumptions")
    supporting_papers: List[Dict[str, Any]] = Field(default_factory=list, description="Supporting Papers Metadata")
    evidence_summary: Dict[str, Any] = Field(default_factory=dict, description="Multi-signal evidence scores")
    generation_mode: str = Field("template", description="Generation mode: 'llm' or 'template'")
    generation_timestamp: str = Field(..., description="ISO timestamp of proposal synthesis")
    disclaimer: str = Field(..., description="Collection-based academic disclaimer")


class ProposalDraftResponse(BaseModel):
    """
    API Response wrapper for Proposal Draft endpoints.
    """
    proposal: ProposalDraft
