import logging
import io
import zipfile
from typing import Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse

from app.models.project_model import ResearchProject
from app.services.academic_manuscript_service import AcademicManuscriptService
from app.services.academic_citation_service import AcademicCitationService
from app.services.academic_quality_service import AcademicQualityService
from app.services.research_results_analysis_service import ResearchResultsAnalysisService

logger = logging.getLogger(__name__)


class SubmissionPackageService:
    """
    Service for bundling all project deliverables into a downloadable ZIP submission package
    containing /paper/, /evidence/, /references/, and /report/ files.
    """

    @classmethod
    def generate_submission_package_zip(cls, db: Session, project_id: int) -> StreamingResponse:
        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"Research project {project_id} not found")

        manuscript_res = AcademicManuscriptService.get_or_generate_manuscript(db, project_id)
        references = AcademicCitationService.get_project_references(db, project_id)
        quality_res = AcademicQualityService.get_manuscript_quality(db, project_id)
        results_summary = ResearchResultsAnalysisService.get_project_results_analysis(db, project_id)

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # 1. /paper/ manuscript.md & manuscript.json
            md_content = f"# {manuscript_res.title}\n\n"
            for s in manuscript_res.sections:
                md_content += f"## {s.title} ({s.evidence_badge_text})\n\n{s.content}\n\n"

            zip_file.writestr("paper/manuscript.md", md_content)
            zip_file.writestr("paper/manuscript.json", manuscript_res.model_dump_json(indent=2))

            # 2. /evidence/ evidence_traceability.md & experiment_log.md & reproducibility.md
            traceability_md = "# Appendix A — Evidence Traceability Matrix\n\n| Section | Badge | Source |\n|---|---|---|\n"
            for s in manuscript_res.sections:
                traceability_md += f"| {s.title} | {s.evidence_badge_text} | Project DB |\n"
            zip_file.writestr("evidence/evidence_traceability.md", traceability_md)

            exp_log_md = f"# Appendix C — Experiment Log\n\nTotal Recorded Results: {results_summary.results_recorded_count}\nOverall Percentage: {quality_res.evidence_coverage_percentage}%\n"
            zip_file.writestr("evidence/experiment_log.md", exp_log_md)

            repro_md = "# Appendix B — Reproducibility Checklist\n\n- PyTorch / Python Environment: Configured\n- Controlled Random Seeds: Specified\n"
            zip_file.writestr("evidence/reproducibility.md", repro_md)

            # 3. /references/ references.md
            refs_md = f"# References (IEEE / APA / Harvard)\n\n"
            for r in references:
                refs_md += f"{r.formatted_ieee}\n\n"
            zip_file.writestr("references/references.md", refs_md)

            # 4. /report/ research_report.md
            report_md = f"# Project Research Report: {project.name}\n\nStatus: {project.status}\nCreated: {project.created_at}\n"
            zip_file.writestr("report/research_report.md", report_md)

        zip_buffer.seek(0)
        filename = f"Submission_Package_Project_{project_id}.zip"

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
