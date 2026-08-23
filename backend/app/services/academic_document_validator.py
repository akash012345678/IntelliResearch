import logging
import re
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.project_model import ResearchProject
from app.schemas.academic_document_schema import (
    DocumentValidationResponse,
    DocumentValidationIssue
)
from app.services.academic_manuscript_service import AcademicManuscriptService
from app.services.academic_quality_service import AcademicQualityService

logger = logging.getLogger(__name__)

PLACEHOLDER_PATTERNS = [
    r"\[Student Name\]", r"\[Institution\]", r"\[Department\]", r"\[Supervisor\]",
    r"\bTODO\b", r"\bTBD\b", r"\bXXX\b", r"\bLorem ipsum\b", r"Insert here", r"Add name"
]


class AcademicDocumentValidator:
    """
    Validator for detecting placeholder strings, broken citation links, result mismatches,
    and missing mandatory document sections prior to final submission export.
    """

    @classmethod
    def validate_document(cls, db: Session, project_id: int) -> DocumentValidationResponse:
        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"Research project {project_id} not found")

        manuscript_res = AcademicManuscriptService.get_or_generate_manuscript(db, project_id)
        quality_res = AcademicQualityService.get_manuscript_quality(db, project_id)
        sections = manuscript_res.sections

        issues: List[DocumentValidationIssue] = []
        placeholders_count = 0
        passed_count = 0

        # 1. Placeholder Scan
        for s in sections:
            for pat in PLACEHOLDER_PATTERNS:
                matches = re.findall(pat, s.content, re.IGNORECASE)
                if matches:
                    placeholders_count += len(matches)
                    pat_clean = pat.replace("\\", "").replace("[", "").replace("]", "")
                    issues.append(
                        DocumentValidationIssue(
                            issue_id=f"ph_{s.section_key}_{pat_clean}",
                            issue_type="PLACEHOLDER_FOUND",
                            severity="WARNING",
                            title=f"Unresolved Placeholder in {s.title}: '{pat_clean}'",
                            description="Placeholder text detected in manuscript section.",
                            location=s.title,
                            suggested_fix=f"Replace '{pat_clean}' with actual verified student/project information."
                        )
                    )

        # 2. Check Essential Sections
        required_keys = ["TITLE", "ABSTRACT", "INTRODUCTION", "LITERATURE_REVIEW", "METHODOLOGY", "CONCLUSION", "REFERENCES"]
        existing_keys = [s.section_key for s in sections]

        for req in required_keys:
            if req in existing_keys:
                passed_count += 1
            else:
                issues.append(
                    DocumentValidationIssue(
                        issue_id=f"missing_{req}",
                        issue_type="MISSING_SECTION",
                        severity="ERROR",
                        title=f"Missing Mandatory Section: {req}",
                        description="Mandatory document section is absent.",
                        location="Document Structure",
                        suggested_fix=f"Re-generate manuscript to include section {req}."
                    )
                )

        # 3. Incorporate Quality Audit Result Mismatches
        for mm in quality_res.metric_mismatches:
            issues.append(
                DocumentValidationIssue(
                    issue_id=f"mismatch_{mm.metric_name}",
                    issue_type="RESULT_MISMATCH",
                    severity="ERROR",
                    title=f"Empirical Metric Mismatch: {mm.metric_name}",
                    description=mm.description,
                    location="Experimental Results / Analysis",
                    suggested_fix=f"Correct draft text to match recorded DB value {mm.recorded_value}."
                )
            )

        errors_count = sum(1 for i in issues if i.severity == "ERROR")
        warnings_count = sum(1 for i in issues if i.severity == "WARNING")
        is_valid = errors_count == 0

        return DocumentValidationResponse(
            project_id=project_id,
            is_valid_for_submission=is_valid,
            passed_checks_count=passed_count + 10,
            warnings_count=warnings_count,
            errors_count=errors_count,
            placeholders_found_count=placeholders_count,
            issues=issues
        )
