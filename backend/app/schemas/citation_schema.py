from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class ReferenceItem(BaseModel):
    id: int
    paper_id: int
    title: str
    authors: str
    publication_year: str
    source_venue: str
    doi: str
    url: str
    formatted_ieee: str
    formatted_apa: str
    formatted_harvard: str
    has_complete_metadata: bool
    citation_key: str  # e.g. '[1]' or '(Author, Year)'


class ClaimEvidenceItem(BaseModel):
    claim_id: str
    section_key: str
    section_title: str
    claim_text: str
    source_type: str  # 'RECORDED_EXPERIMENT' | 'RESEARCH_PAPER' | 'PROJECT_DERIVED' | 'PROPOSED'
    source_badge_text: str
    supporting_paper_id: Optional[int] = None
    supporting_paper_title: Optional[str] = None
    supporting_experiment_id: Optional[int] = None
    supporting_experiment_name: Optional[str] = None
    explanation: str


class MetricMismatchItem(BaseModel):
    metric_name: str
    recorded_value: str
    manuscript_value: str
    severity: str  # 'HIGH' | 'MEDIUM'
    description: str


class QualityIssueItem(BaseModel):
    issue_id: str
    issue_type: str  # 'UNSUPPORTED_CLAIM' | 'NOVELTY_CLAIM' | 'RESULT_MISMATCH' | 'UNVERIFIED_DATASET' | 'INCOMPLETE_REFERENCE'
    title: str
    description: str
    problematic_text: str
    suggested_fix: str
    severity: str  # 'CRITICAL' | 'WARNING' | 'INFO'


class AcademicQualityResponse(BaseModel):
    project_id: int
    citation_traceability_score: int  # 0 to 100
    evidence_coverage_percentage: int  # 0 to 100
    result_consistency_score: int  # 0 to 100
    reference_integrity_score: int  # 0 to 100
    novelty_claim_safety: str  # 'PASS' | 'WARNING_FLAGS_DETECTED'
    dataset_verification_score: int  # 0 to 100
    issues: List[QualityIssueItem] = []
    metric_mismatches: List[MetricMismatchItem] = []
