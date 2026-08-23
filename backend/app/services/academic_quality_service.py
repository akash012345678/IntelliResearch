import logging
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.project_model import ResearchProject, ResearchExperiment, ExperimentRun, ExperimentResult, ResearchManuscript
from app.schemas.citation_schema import (
    AcademicQualityResponse,
    QualityIssueItem,
    MetricMismatchItem
)
from app.services.academic_manuscript_service import AcademicManuscriptService
from app.services.academic_citation_service import AcademicCitationService

logger = logging.getLogger(__name__)

# Dangerous novelty keywords requiring review warnings
NOVELTY_KEYWORDS = [
    r"\bfirst\b", r"\bnovel\b", r"\bunique\b", r"\bunprecedented\b",
    r"\bstate-of-the-art\b", r"\bSOTA\b", r"\bnever previously proposed\b",
    r"\bno previous work\b", r"\bglobally superior\b", r"\bguaranteed improvement\b"
]

# Unsupported claim phrases requiring review warnings
UNSUPPORTED_PHRASES = [
    (r"\bthis method is superior\b", "Consider: 'Recorded results indicate an improvement in target metrics...'"),
    (r"\bprevious studies failed\b", "Consider: 'Prior literature exhibits operational constraints...'"),
    (r"\bguarantees accuracy\b", "Consider: 'Empirical runs demonstrate stable performance...'"),
    (r"\bdefinitively proves\b", "Consider: 'Recorded evidence supports hypothesis H1...'"),
    (r"\b100% accurate\b", "Consider: 'Observed empirical accuracy on test split...'")
]


class AcademicQualityService:
    """
    Service for auditing manuscript citation traceability, metric consistency against ExperimentResult DB records,
    detecting unsafe novelty claims, and validating dataset coverage.
    """

    @classmethod
    def get_manuscript_quality(cls, db: Session, project_id: int) -> AcademicQualityResponse:
        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"Research project {project_id} not found")

        # Load manuscript sections
        manuscript_res = AcademicManuscriptService.get_or_generate_manuscript(db, project_id)
        sections = manuscript_res.sections
        references = AcademicCitationService.get_project_references(db, project_id)

        # 1. References Integrity Check
        incomplete_refs = [r for r in references if not r.has_complete_metadata]
        ref_integrity_score = 100 if len(references) == 0 else int(((len(references) - len(incomplete_refs)) / len(references)) * 100)

        # 2. Citation Traceability Score
        literature_dependent_keys = ["ABSTRACT", "INTRODUCTION", "BACKGROUND", "LITERATURE_REVIEW", "RESEARCH_GAP"]
        lit_sections = [s for s in sections if s.section_key in literature_dependent_keys]
        rec_lit_cnt = sum(1 for s in lit_sections if s.evidence_level in ["RECORDED", "DERIVED"])
        traceability_score = 100 if len(lit_sections) == 0 else int((rec_lit_cnt / len(lit_sections)) * 100)

        # 3. Metric Mismatch Detection against DB ExperimentResult records
        exps = project.experiments or []
        recorded_results: List[ExperimentResult] = []
        for e in exps:
            for r in e.runs:
                recorded_results.extend(r.results)

        mismatches: List[MetricMismatchItem] = []
        issues: List[QualityIssueItem] = []

        # Scan text for novelty and unsupported claims
        full_text = " ".join([s.content for s in sections])

        # Scan for Novelty Warnings
        for kw in NOVELTY_KEYWORDS:
            matches = re.findall(kw, full_text, re.IGNORECASE)
            if matches:
                kw_clean = kw.replace(r"\b", "").replace("\\", "")
                issues.append(
                    QualityIssueItem(
                        issue_id=f"nov_{kw_clean}",
                        issue_type="NOVELTY_CLAIM",
                        title=f"Novelty Claim Warning: '{kw_clean}'",
                        description="IntelliResearch cannot establish global academic novelty from the indexed collection alone.",
                        problematic_text=f"Detected novelty keyword '{kw_clean}' in manuscript draft text.",
                        suggested_fix="Use collection-scoped framing (e.g. 'Within the indexed project collection...').",
                        severity="WARNING"
                    )
                )

        # Scan for Unsupported Claims
        for phrase_regex, suggestion in UNSUPPORTED_PHRASES:
            matches = re.findall(phrase_regex, full_text, re.IGNORECASE)
            if matches:
                phrase_clean = phrase_regex.replace(r"\b", "").replace("\\", "")
                issues.append(
                    QualityIssueItem(
                        issue_id=f"unsup_{phrase_clean}",
                        issue_type="UNSUPPORTED_CLAIM",
                        title=f"Claim Needs Review: '{phrase_clean}'",
                        description="Absolute academic statement detected without explicit empirical qualification.",
                        problematic_text=f"Detected phrase '{phrase_clean}' in manuscript text.",
                        suggested_fix=suggestion,
                        severity="WARNING"
                    )
                )

        # Scan for Metric Mismatches (e.g., if text mentions F1 or accuracy values conflicting with DB)
        for res in recorded_results:
            try:
                rec_val = float(res.metric_value)
                # Look for numbers in text near metric_name
                pattern = rf"{res.metric_name}\s*[:=]\s*([0-9\.]+)"
                matches = re.findall(pattern, full_text, re.IGNORECASE)
                for m in matches:
                    text_val = float(m)
                    if abs(text_val - rec_val) > 0.001:
                        mismatches.append(
                            MetricMismatchItem(
                                metric_name=res.metric_name,
                                recorded_value=str(rec_val),
                                manuscript_value=str(text_val),
                                severity="HIGH",
                                description=f"Manuscript states {res.metric_name}={text_val}, but DB records {rec_val}."
                            )
                        )
                        issues.append(
                            QualityIssueItem(
                                issue_id=f"mismatch_{res.metric_name}",
                                issue_type="RESULT_MISMATCH",
                                title=f"Result Metric Mismatch: {res.metric_name}",
                                description=f"Recorded DB metric ({rec_val}) differs from draft text ({text_val}).",
                                problematic_text=f"{res.metric_name}={text_val}",
                                suggested_fix=f"Correct draft text to match recorded empirical value {rec_val}.",
                                severity="CRITICAL"
                            )
                        )
            except (ValueError, TypeError):
                continue

        # Incomplete Reference Warnings
        if incomplete_refs:
            issues.append(
                QualityIssueItem(
                    issue_id="incomplete_refs",
                    issue_type="INCOMPLETE_REFERENCE",
                    title=f"Incomplete Bibliographic Metadata ({len(incomplete_refs)} Papers)",
                    description="Some project papers lack complete author or publication year metadata.",
                    problematic_text=f"{len(incomplete_refs)} references lack author/year fields.",
                    suggested_fix="Update paper metadata or use verified paper ID citation format.",
                    severity="INFO"
                )
            )

        novelty_status = "WARNING_FLAGS_DETECTED" if any(i.issue_type == "NOVELTY_CLAIM" for i in issues) else "PASS"
        result_consistency = 100 if len(mismatches) == 0 else max(0, 100 - (len(mismatches) * 25))

        return AcademicQualityResponse(
            project_id=project_id,
            citation_traceability_score=traceability_score,
            evidence_coverage_percentage=manuscript_res.completeness.overall_percentage,
            result_consistency_score=result_consistency,
            reference_integrity_score=ref_integrity_score,
            novelty_claim_safety=novelty_status,
            dataset_verification_score=100 if len(exps) > 0 else 50,
            issues=issues,
            metric_mismatches=mismatches
        )
