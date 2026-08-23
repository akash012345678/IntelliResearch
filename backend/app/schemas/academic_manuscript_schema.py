from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class ManuscriptSectionItem(BaseModel):
    section_key: str  # e.g. 'ABSTRACT', 'INTRODUCTION', 'LITERATURE_REVIEW', 'EXPERIMENT_RESULTS'
    title: str
    student_label: str  # Student-friendly question/header (e.g. 'What did your experiments show?')
    evidence_level: str  # 'RECORDED' | 'DERIVED' | 'PROPOSED' | 'MISSING'
    evidence_badge_text: str
    content: str
    bullet_points: List[str] = []
    is_edited: bool = False


class ManuscriptVersionItem(BaseModel):
    version_id: int
    version_number: int
    change_summary: Optional[str] = "Manuscript Draft Saved"
    created_at: str


class ManuscriptCompletenessScore(BaseModel):
    overall_percentage: int  # 0 to 100
    recorded_sections_count: int
    derived_sections_count: int
    proposed_sections_count: int
    missing_sections_count: int
    rating_label: str  # 'HIGHLY COMPLETE' | 'MODERATELY COMPLETE' | 'PROPOSAL STAGE' | 'INITIAL'


class ManuscriptGenerateResponse(BaseModel):
    project_id: int
    project_name: str
    manuscript_id: int
    title: str
    status: str
    current_version_number: int
    completeness: ManuscriptCompletenessScore
    sections: List[ManuscriptSectionItem] = []
    available_versions: List[ManuscriptVersionItem] = []
    academic_integrity_notice: str = (
        "IntelliResearch generates a structured academic draft grounded in your project evidence. "
        "Students are responsible for verifying citations, interpreting empirical metrics, and conducting peer review prior to submission."
    )


class ManuscriptSaveVersionRequest(BaseModel):
    title: Optional[str] = "Research Paper Draft"
    sections: List[ManuscriptSectionItem]
    change_summary: Optional[str] = "Manual student revision"
