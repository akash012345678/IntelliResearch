from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class DocumentFormatConfig(BaseModel):
    profile: str = "COLLEGE_PROJECT"  # 'COLLEGE_PROJECT' | 'RESEARCH_PAPER' | 'THESIS'
    page_size: str = "A4"  # 'A4' | 'LETTER'
    margins: str = "NORMAL"  # 'NORMAL' | 'NARROW'
    font_family: str = "Times New Roman"  # 'Times New Roman' | 'Arial' | 'Calibri'
    font_size: int = 12
    line_spacing: float = 1.5
    citation_style: str = "IEEE"  # 'IEEE' | 'APA' | 'Harvard'
    student_name: Optional[str] = None
    register_number: Optional[str] = None
    institution: Optional[str] = None
    department: Optional[str] = None
    supervisor: Optional[str] = None
    academic_year: Optional[str] = "2025-2026"
    show_evidence_badges: bool = True
    show_table_sources: bool = True
    show_figure_sources: bool = True
    show_evidence_appendix: bool = True
    show_reproducibility_appendix: bool = True
    show_experiment_appendix: bool = True


class DocumentValidationIssue(BaseModel):
    issue_id: str
    issue_type: str  # 'PLACEHOLDER_FOUND' | 'MISSING_TITLE' | 'MISSING_ABSTRACT' | 'BROKEN_CITATION' | 'RESULT_MISMATCH'
    severity: str  # 'ERROR' | 'WARNING' | 'INFO'
    title: str
    description: str
    location: str
    suggested_fix: str


class DocumentValidationResponse(BaseModel):
    project_id: int
    is_valid_for_submission: bool
    passed_checks_count: int
    warnings_count: int
    errors_count: int
    placeholders_found_count: int
    issues: List[DocumentValidationIssue] = []


class DocumentPreviewPage(BaseModel):
    page_number: int
    title: str
    section_type: str  # 'TITLE_PAGE' | 'TOC' | 'LIST_OF_FIGURES' | 'LIST_OF_TABLES' | 'SECTION' | 'REFERENCES' | 'APPENDIX'
    html_content: str


class DocumentPreviewResponse(BaseModel):
    project_id: int
    project_name: str
    total_pages: int
    profile: str
    config: DocumentFormatConfig
    pages: List[DocumentPreviewPage] = []
    toc: List[Dict[str, Any]] = []
    list_of_figures: List[Dict[str, Any]] = []
    list_of_tables: List[Dict[str, Any]] = []
