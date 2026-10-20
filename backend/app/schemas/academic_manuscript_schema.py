from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class ClaimEvidenceMetadata(BaseModel):
    source_type: str  # 'RECORDED_EVIDENCE' | 'PROPOSED' | 'DERIVED' | 'EXPERIMENTAL_RESULT' | 'MISSING'
    source_papers: List[int] = Field(default_factory=list)
    source_paper_titles: List[str] = Field(default_factory=list)
    source_gap_id: Optional[int] = None
    source_opportunity_id: Optional[int] = None
    source_plan_id: Optional[int] = None
    source_experiment_ids: List[int] = Field(default_factory=list)
    source_result_ids: List[int] = Field(default_factory=list)
    provenance_summary: str = ""


class ManuscriptSectionItem(BaseModel):
    section_key: str  # e.g. 'ABSTRACT', 'INTRODUCTION', 'LITERATURE_REVIEW', 'RECORDED_RESULTS'
    chapter_number: Optional[int] = 0  # 0: Front Matter, 1-6: Chapters, 7: Refs, 8: Appendix
    chapter_title: Optional[str] = "FRONT MATTER"
    section_number: Optional[str] = ""  # e.g. "1.1", "2.3", "4.5"
    title: str
    student_label: str  # Student-friendly description/header
    evidence_level: str  # 'RECORDED_EVIDENCE' | 'DERIVED' | 'PROPOSED' | 'EXPERIMENTAL_RESULT' | 'MISSING'
    evidence_badge_text: str
    content: str
    bullet_points: List[str] = Field(default_factory=list)
    is_edited: bool = False
    is_applicable: bool = True
    claim_traceability: Optional[ClaimEvidenceMetadata] = None


class ManuscriptVersionItem(BaseModel):
    version_id: int
    version_number: int
    title: Optional[str] = "Academic Manuscript"
    change_summary: Optional[str] = "Manuscript Draft Saved"
    created_at: str


class ManuscriptCompletenessScore(BaseModel):
    overall_percentage: int  # 0 to 100 (Evidence Completeness for backward compatibility)
    evidence_completeness_percentage: int = 0  # 0 to 100 (Verified Evidence Completeness)
    evidence_rating_label: str = "STARTING"  # 'STARTING' | 'PARTIAL' | 'IN PROGRESS' | 'HIGHLY COMPLETE' | 'NEAR COMPLETE' | 'COMPLETE'
    manuscript_completion_percentage: int = 0  # 0 to 100 (Structural Document Completion)
    manuscript_completion_label: str = "STARTING"  # 'STARTING' | 'PARTIAL' | 'IN PROGRESS' | 'HIGHLY COMPLETE' | 'NEAR COMPLETE' | 'COMPLETE'
    recorded_sections_count: int
    derived_sections_count: int
    proposed_sections_count: int
    experimental_result_sections_count: int
    missing_sections_count: int
    rating_label: str  # Alias for evidence_rating_label
    quality_status: str = "PASS"  # 'PASS' | 'WARNING' | 'ERROR'


class ManuscriptGenerateResponse(BaseModel):
    project_id: int
    project_name: str
    manuscript_id: int
    title: str
    status: str  # DRAFT | EVIDENCE_INCOMPLETE | READY_FOR_EXPERIMENTS | RESULTS_PARTIAL | RESULTS_COMPLETE | READY_FOR_REVIEW | READY_FOR_EXPORT
    current_version_number: int
    completeness: ManuscriptCompletenessScore
    sections: List[ManuscriptSectionItem] = Field(default_factory=list)
    available_versions: List[ManuscriptVersionItem] = Field(default_factory=list)
    acronyms: Dict[str, str] = Field(default_factory=dict)
    academic_integrity_notice: str = (
        "IntelliResearch generates a structured academic paper grounded in your project evidence. "
        "Strict Zero-Fabrication Rule: Unexecuted experiments and unavailable metadata are explicitly marked as MISSING. "
        "Students are responsible for verifying citations, interpreting empirical metrics, and conducting peer review prior to thesis submission."
    )


class ManuscriptSaveVersionRequest(BaseModel):
    title: Optional[str] = "Research Paper Draft"
    sections: List[ManuscriptSectionItem]
    change_summary: Optional[str] = "Manual student revision"


class ManuscriptVersionRestoreRequest(BaseModel):
    version_number: int


class SectionDiffItem(BaseModel):
    section_key: str
    title: str
    old_content: str
    new_content: str
    status: str  # 'UNCHANGED' | 'MODIFIED' | 'ADDED' | 'REMOVED'


class ManuscriptVersionCompareResponse(BaseModel):
    version_a: int
    version_b: int
    title_changed: bool
    old_title: str
    new_title: str
    diffs: List[SectionDiffItem] = Field(default_factory=list)

