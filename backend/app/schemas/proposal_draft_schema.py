from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ProposalDraftRequest(BaseModel):
    """
    Request model for generating a structured proposal draft from a research direction.
    """
    direction_id: Optional[str] = Field(None, description="ID of the research direction (e.g. dir_1)")
    project_id: Optional[int] = Field(None, description="Optional Research Project ID")
    opportunity_family_id: Optional[str] = Field(None, description="Opportunity family ID or canonical relationship key")
    title: Optional[str] = Field(None, description="Opportunity or proposal title")
    research_question: Optional[str] = Field(None, description="Explicit research question being investigated")
    supporting_papers: Optional[List[Dict[str, Any]]] = Field(None, description="Supporting paper metadata objects")
    regenerate: Optional[bool] = Field(False, description="Explicit flag to force generating a NEW proposal version")
    is_manual_idea: Optional[bool] = Field(False, description="Flag for user-created manual research idea")
    manual_title: Optional[str] = Field(None, description="Title for manual research idea")
    manual_description: Optional[str] = Field(None, description="Description for manual research idea")


class ProposalDraft(BaseModel):
    """
    Structured academic research proposal draft synthesized from collection evidence.
    """
    proposal_id: str = Field(..., description="Unique proposal ID")
    source_direction_id: Optional[str] = Field(None, description="Source research direction ID")
    source_gap_id: Optional[str] = Field(None, description="Source research gap ID")
    title: str = Field(..., description="Proposal Title")
    abstract: str = Field(..., description="Executive Abstract")
    problem_statement: str = Field(..., description="Problem Statement")
    research_motivation: str = Field(..., description="Research Motivation")
    research_question: str = Field(..., description="Testable Research Question")
    objectives: List[str] = Field(default_factory=list, description="Measurable Research Objectives")
    related_work_synthesis: str = Field(..., description="Related Work Synthesis citing supporting papers")
    research_gap: str = Field(..., description="Identified Collection Research Gap")
    proposed_methodology: str = Field(..., description="Proposed Methodology Plan")
    candidate_algorithms: List[str] = Field(default_factory=list, description="Candidate Algorithms")
    candidate_datasets: List[str] = Field(default_factory=list, description="Candidate Datasets")
    task_type: str = Field("OBJECT_DETECTION", description="Research task type: OBJECT_DETECTION, IMAGE_CLASSIFICATION, SEGMENTATION, EXPLAINABILITY_ANALYSIS, COMPARATIVE_BENCHMARK, or OTHER_SUPPORTED_TASK")
    datasets_provenance: List[Dict[str, Any]] = Field(default_factory=list, description="Evidence-grounded datasets with source paper IDs, role, and evidence status")
    dataset_evaluation_plan: str = Field(..., description="Dataset Evaluation Plan")
    experimental_plan: str = Field(..., description="Experimental Plan & Baseline Comparisons")
    evaluation_metrics: str = Field(..., description="Evaluation Metrics & Performance Benchmarks")
    expected_contribution: str = Field(..., description="Expected Academic & Technical Contribution")
    limitations: str = Field(..., description="Collection Limitations & Study Assumptions")
    supporting_papers: List[Dict[str, Any]] = Field(default_factory=list, description="Supporting Papers Metadata")
    evidence_summary: Dict[str, Any] = Field(default_factory=dict, description="Multi-signal evidence scores")
    generation_mode: str = Field("template", description="Generation mode: 'llm', 'template', or 'manual_idea'")
    is_user_provided: bool = Field(False, description="Whether proposal originates from a manual user idea")
    generation_timestamp: str = Field(..., description="ISO timestamp of proposal synthesis")
    disclaimer: str = Field(..., description="Collection-based academic disclaimer")


class ProposalDraftResponse(BaseModel):
    """
    API Response wrapper for Proposal Draft endpoints matching Phase 3 Contract.
    """
    id: Optional[int] = Field(None, description="Database Primary Key ID of persisted proposal")
    proposal_id: str = Field(..., description="Unique proposal UUID")
    project_id: Optional[int] = Field(None, description="Research Project ID")
    direction_id: Optional[str] = Field(None, description="Source Research Direction ID")
    title: str = Field(..., description="Proposal Title")
    research_question: Optional[str] = Field(None, description="Research Question")
    status: str = Field("DRAFT", description="Proposal Status")
    version_number: int = Field(1, description="Proposal Version Number")
    proposal: ProposalDraft = Field(..., description="Complete structured ProposalDraft object")
    version: Optional[Dict[str, Any]] = Field(None, description="Version metadata summary")


