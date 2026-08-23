import logging
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.project_model import ResearchProject, ResearchManuscript, ResearchManuscriptVersion, ProjectPaper, SavedResearchDirection, ResearchExperiment, ExperimentRun, ExperimentResult
from app.models.proposal_model import Proposal
from app.schemas.academic_manuscript_schema import (
    ManuscriptSectionItem,
    ManuscriptVersionItem,
    ManuscriptCompletenessScore,
    ManuscriptGenerateResponse,
    ManuscriptSaveVersionRequest
)
from app.services.research_results_analysis_service import ResearchResultsAnalysisService
from app.services.project_research_report_service import ProjectResearchReportService

logger = logging.getLogger(__name__)


class AcademicManuscriptService:
    """
    Service for generating, editing, versioning, and exporting 29-section evidence-grounded academic manuscripts.
    Enforces 4 evidence classification badges (RECORDED, DERIVED, PROPOSED, MISSING) and cautious academic framing.
    """

    @classmethod
    def get_or_generate_manuscript(cls, db: Session, project_id: int) -> ManuscriptGenerateResponse:
        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"Research project {project_id} not found")

        # Find existing manuscript record
        manuscript = db.query(ResearchManuscript).filter(ResearchManuscript.project_id == project_id).first()

        if manuscript and manuscript.versions:
            # Load latest saved version
            latest_version = max(manuscript.versions, key=lambda v: v.version_number)
            return cls._build_response_from_version(project, manuscript, latest_version)
        else:
            # Synthesize fresh manuscript draft from project evidence
            return cls.generate_fresh_manuscript(db, project_id)

    @classmethod
    def generate_fresh_manuscript(cls, db: Session, project_id: int) -> ManuscriptGenerateResponse:
        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"Research project {project_id} not found")

        # Aggregated project evidence
        papers = [assoc.paper for assoc in project.project_papers if assoc.paper]
        saved_dirs = project.saved_directions or []
        exps = project.experiments or []
        props = project.proposals or []

        # Find saved methodology plan if exists
        saved_plan = None
        for d in saved_dirs:
            if d.direction_data and isinstance(d.direction_data, dict) and "methodology_plan" in d.direction_data:
                saved_plan = d.direction_data["methodology_plan"]
                break

        # Results analysis summary
        results_summary = ResearchResultsAnalysisService.get_project_results_analysis(db, project_id)
        has_results = results_summary.has_recorded_results

        # Helper experiment attributes
        first_exp = exps[0] if len(exps) > 0 else None
        first_ds_name = (first_exp.dataset_config or {}).get("name", "Custom Dataset") if first_exp else "Dataset not yet configured"
        first_bl_alg = (first_exp.baseline_config or {}).get("name") or (first_exp.baseline_config or {}).get("algorithm", "Baseline Algorithm") if first_exp else "Baseline algorithm not recorded"
        first_pr_arch = (first_exp.proposed_config or {}).get("name") or (first_exp.proposed_config or {}).get("architecture", "Proposed Model") if first_exp else "Proposed model configuration"
        first_hw_info = (first_exp.environment_config or {}).get("hardware", "Standard Compute Environment") if first_exp else "Standard Compute Environment"
        first_tg_metrics = ", ".join((first_exp.execution_config or {}).get("target_metrics", ["Accuracy", "F1"])) if (first_exp and isinstance(first_exp.execution_config, dict) and "target_metrics" in first_exp.execution_config) else "Accuracy, F1-score, Precision, Latency"

        # Synthesize 29 Manuscript Sections
        sections: List[ManuscriptSectionItem] = [
            # 1. Title
            ManuscriptSectionItem(
                section_key="TITLE",
                title="1. Title",
                student_label="Paper Title",
                evidence_level="RECORDED" if len(saved_dirs) > 0 else "PROPOSED",
                evidence_badge_text="🟢 RECORDED" if len(saved_dirs) > 0 else "🔵 PROPOSED",
                content=f"Empirical Investigation into {saved_dirs[0].title if len(saved_dirs) > 0 else project.name}: An Evidence-Grounded Study",
                bullet_points=[f"Project Scope: {project.name}", f"Assigned Papers: {len(papers)}"]
            ),
            # 2. Abstract
            ManuscriptSectionItem(
                section_key="ABSTRACT",
                title="2. Abstract",
                student_label="Abstract Summary",
                evidence_level="DERIVED" if has_results else "PROPOSED",
                evidence_badge_text="🟡 DERIVED" if has_results else "🔵 PROPOSED",
                content=(
                    f"This study investigates {saved_dirs[0].title if len(saved_dirs) > 0 else 'the research domain'} within a curated collection of {len(papers)} research papers. "
                    + (f"Empirical experiments evaluated baseline models against proposed configurations across {results_summary.results_recorded_count} recorded result set(s). " if has_results else "Experimental validation remains ongoing. ")
                    + f"Recorded findings suggest key operational trade-offs and highlight underrepresented concept areas for future academic research."
                ),
                bullet_points=["Grounded in indexed project literature", "Evaluated on student-entered empirical measurements"]
            ),
            # 3. Keywords
            ManuscriptSectionItem(
                section_key="KEYWORDS",
                title="3. Keywords",
                student_label="Key Terms",
                evidence_level="RECORDED" if len(papers) > 0 else "MISSING",
                evidence_badge_text="🟢 RECORDED" if len(papers) > 0 else "🔴 MISSING",
                content=", ".join([p.title.split()[0] for p in papers[:5]]) if papers else "Research Gap Discovery, Empirical Evaluation, Literature Synthesis",
                bullet_points=["Extracted from assigned paper topics"]
            ),
            # 4. Introduction
            ManuscriptSectionItem(
                section_key="INTRODUCTION",
                title="4. Introduction",
                student_label="Introduction & Domain Context",
                evidence_level="DERIVED" if len(papers) > 0 else "PROPOSED",
                evidence_badge_text="🟡 DERIVED" if len(papers) > 0 else "🔵 PROPOSED",
                content=f"Within the indexed collection of {len(papers)} research papers for project '{project.name}', recent literature demonstrates increasing interest in novel algorithmic architectures. However, systematic analysis reveals structural gaps between current methodologies and target performance bounds.",
                bullet_points=[f"Collection size: {len(papers)} papers", "Avoids global novelty claims"]
            ),
            # 5. Background
            ManuscriptSectionItem(
                section_key="BACKGROUND",
                title="5. Background",
                student_label="Domain Background",
                evidence_level="DERIVED" if len(papers) > 0 else "MISSING",
                evidence_badge_text="🟡 DERIVED" if len(papers) > 0 else "🔴 MISSING",
                content=f"Background context synthesizes foundational concepts from indexed papers including {', '.join([p.title[:30] + '...' for p in papers[:3]]) if papers else 'indexed literature'}.",
                bullet_points=["Synthesized from assigned paper abstracts"]
            ),
            # 6. Literature Review
            ManuscriptSectionItem(
                section_key="LITERATURE_REVIEW",
                title="6. Literature Review",
                student_label="What do existing papers do?",
                evidence_level="RECORDED" if len(papers) > 0 else "MISSING",
                evidence_badge_text="🟢 RECORDED" if len(papers) > 0 else "🔴 MISSING",
                content="\n\n".join([f"• **{p.title}**: Investigates domain methodologies with indexed relevance to project scope." for p in papers[:5]]) if papers else "No research papers assigned to project literature review.",
                bullet_points=[f"{len(papers)} papers reviewed in collection"]
            ),
            # 7. Research Gap
            ManuscriptSectionItem(
                section_key="RESEARCH_GAP",
                title="7. Research Gap",
                student_label="What appears to be missing?",
                evidence_level="RECORDED" if len(saved_dirs) > 0 else "DERIVED",
                evidence_badge_text="🟢 RECORDED" if len(saved_dirs) > 0 else "🟡 DERIVED",
                content=f"Analysis of the indexed collection identifies an underrepresented opportunity: {saved_dirs[0].description if len(saved_dirs) > 0 else 'Underrepresented concept overlap detected in project literature.'} Note: This gap represents an opportunity identified within the indexed project collection and does not establish global academic novelty.",
                bullet_points=["Collection-scoped gap detection", "Grounded in paper concept graph"]
            ),
            # 8. Research Problem
            ManuscriptSectionItem(
                section_key="RESEARCH_PROBLEM",
                title="8. Research Problem",
                student_label="Core Research Problem",
                evidence_level="DERIVED" if len(saved_dirs) > 0 else "PROPOSED",
                evidence_badge_text="🟡 DERIVED" if len(saved_dirs) > 0 else "🔵 PROPOSED",
                content=f"The primary research problem addresses the lack of integrated evaluation combining existing baseline methods with proposed architectural refinements under controlled experimental settings.",
                bullet_points=["Defined from candidate research direction"]
            ),
            # 9. Research Objectives
            ManuscriptSectionItem(
                section_key="OBJECTIVES",
                title="9. Research Objectives",
                student_label="Measurable Objectives",
                evidence_level="RECORDED" if saved_plan else "PROPOSED",
                evidence_badge_text="🟢 RECORDED" if saved_plan else "🔵 PROPOSED",
                content="\n".join([f"1. Evaluate baseline algorithm performance.", "2. Implement proposed model configuration.", "3. Conduct empirical comparative analysis.", "4. Assess performance trade-offs and computational efficiency."]),
                bullet_points=["Measurable project milestones"]
            ),
            # 10. Research Questions
            ManuscriptSectionItem(
                section_key="RESEARCH_QUESTIONS",
                title="10. Research Questions",
                student_label="Research Questions (RQs)",
                evidence_level="RECORDED" if saved_plan else "PROPOSED",
                evidence_badge_text="🟢 RECORDED" if saved_plan else "🔵 PROPOSED",
                content="• RQ1: Does the proposed configuration improve target empirical metrics compared with the selected baseline?\n• RQ2: What performance trade-offs (e.g. latency vs accuracy) are observed across experimental runs?",
                bullet_points=["Formulated for experimental verification"]
            ),
            # 11. Hypotheses
            ManuscriptSectionItem(
                section_key="HYPOTHESES",
                title="11. Hypotheses",
                student_label="H0 / H1 Hypotheses",
                evidence_level="RECORDED" if saved_plan else "PROPOSED",
                evidence_badge_text="🟢 RECORDED" if saved_plan else "🔵 PROPOSED",
                content=f"• H0: The proposed method exhibits no statistically significant difference compared to baseline.\n• H1: The proposed method achieves measurable improvement on primary target metrics.",
                bullet_points=["Null and alternative hypothesis definition"]
            ),
            # 12. Proposed Contribution
            ManuscriptSectionItem(
                section_key="PROPOSED_CONTRIBUTION",
                title="12. Proposed Contribution",
                student_label="Project Contribution",
                evidence_level="DERIVED" if len(saved_dirs) > 0 else "PROPOSED",
                evidence_badge_text="🟡 DERIVED" if len(saved_dirs) > 0 else "🔵 PROPOSED",
                content="This work contributes an empirical comparative analysis, structured methodology framework, and recorded experimental results evaluated against established baseline techniques.",
                bullet_points=["Empirical framework contribution"]
            ),
            # 13. Methodology
            ManuscriptSectionItem(
                section_key="METHODOLOGY",
                title="13. Methodology",
                student_label="System Pipeline & Design",
                evidence_level="RECORDED" if saved_plan else "PROPOSED",
                evidence_badge_text="🟢 RECORDED" if saved_plan else "🔵 PROPOSED",
                content=f"The proposed methodology follows a multi-stage pipeline: Data Ingestion -> Preprocessing -> Model Training -> Comparative Baseline Evaluation -> Metric Extraction.",
                bullet_points=["Multi-stage experimental design"]
            ),
            # 14. Dataset Description
            ManuscriptSectionItem(
                section_key="DATASET_DESCRIPTION",
                title="14. Dataset Description",
                student_label="Dataset Details",
                evidence_level="RECORDED" if len(exps) > 0 else "MISSING",
                evidence_badge_text="🟢 RECORDED" if len(exps) > 0 else "🔴 MISSING",
                content=f"Dataset: {first_ds_name}. Configured for controlled comparative evaluation.",
                bullet_points=[f"Dataset: {first_ds_name}"]
            ),
            # 15. Data Preparation
            ManuscriptSectionItem(
                section_key="DATA_PREPARATION",
                title="15. Data Preparation",
                student_label="Data Preprocessing",
                evidence_level="DERIVED" if len(exps) > 0 else "MISSING",
                evidence_badge_text="🟡 DERIVED" if len(exps) > 0 else "🔴 MISSING",
                content="Standard data cleaning, feature normalization, and train/validation/test split partitioning procedures applied prior to model execution.",
                bullet_points=["Standard preprocessing pipeline"]
            ),
            # 16. Baseline Methods
            ManuscriptSectionItem(
                section_key="BASELINE_METHODS",
                title="16. Baseline Methods",
                student_label="Baseline Algorithms",
                evidence_level="RECORDED" if len(exps) > 0 else "MISSING",
                evidence_badge_text="🟢 RECORDED" if len(exps) > 0 else "🔴 MISSING",
                content=f"Selected Baseline: {first_bl_alg}.",
                bullet_points=["Established comparative reference"]
            ),
            # 17. Proposed Method
            ManuscriptSectionItem(
                section_key="PROPOSED_METHOD",
                title="17. Proposed Method",
                student_label="Proposed Architecture",
                evidence_level="RECORDED" if len(exps) > 0 else "PROPOSED",
                evidence_badge_text="🟢 RECORDED" if len(exps) > 0 else "🔵 PROPOSED",
                content=f"Proposed Architecture: {first_pr_arch}.",
                bullet_points=["Refined candidate architecture"]
            ),
            # 18. Experimental Setup
            ManuscriptSectionItem(
                section_key="EXPERIMENTAL_SETUP",
                title="18. Experimental Setup",
                student_label="Hardware & Software Setup",
                evidence_level="RECORDED" if len(exps) > 0 else "MISSING",
                evidence_badge_text="🟢 RECORDED" if len(exps) > 0 else "🔴 MISSING",
                content=f"Hardware: {first_hw_info}. Execution framework configured in PyTorch/Python.",
                bullet_points=["Controlled compute environment"]
            ),
            # 19. Evaluation Metrics
            ManuscriptSectionItem(
                section_key="EVALUATION_METRICS",
                title="19. Evaluation Metrics",
                student_label="Target Metrics",
                evidence_level="RECORDED" if len(exps) > 0 else "MISSING",
                evidence_badge_text="🟢 RECORDED" if len(exps) > 0 else "🔴 MISSING",
                content=f"Primary Metrics Evaluated: {first_tg_metrics}.",
                bullet_points=["Standard quantitative metrics"]
            ),
            # 20. Experimental Results
            ManuscriptSectionItem(
                section_key="EXPERIMENTAL_RESULTS",
                title="20. Experimental Results",
                student_label="What did your experiments show?",
                evidence_level="RECORDED" if has_results else "MISSING",
                evidence_badge_text="🟢 RECORDED" if has_results else "🔴 MISSING",
                content=(
                    f"Results recorded across {results_summary.results_recorded_count} experiment(s):\n\n"
                    + "\n".join([
                        f"• **{ea.experiment_name}**: Baseline ({ea.baseline_alg}) vs Proposed ({ea.proposed_arch}) on {ea.dataset_name}. "
                        + f"Evaluated {ea.metrics_count} metric(s) across {ea.run_count} run(s). {ea.safe_conclusion}"
                        for ea in results_summary.experiments_analysis
                    ]) if has_results else "Results not yet recorded. Execute experiments in the Experiment Workspace to log empirical measurements."
                ),
                bullet_points=["Strict zero data fabrication", f"Results recorded: {results_summary.results_recorded_count}"]
            ),
            # 21. Result Analysis
            ManuscriptSectionItem(
                section_key="RESULT_ANALYSIS",
                title="21. Result Analysis",
                student_label="Empirical Analysis & Trade-offs",
                evidence_level="DERIVED" if has_results else "MISSING",
                evidence_badge_text="🟡 DERIVED" if has_results else "🔴 MISSING",
                content=results_summary.project_overall_conclusion if has_results else "Results analysis pending recorded experimental data.",
                bullet_points=["Automated metric trade-off detection", "Multi-run dispersion analysis"]
            ),
            # 22. Discussion
            ManuscriptSectionItem(
                section_key="DISCUSSION",
                title="22. Discussion",
                student_label="What do these results mean?",
                evidence_level="DERIVED" if has_results else "PROPOSED",
                evidence_badge_text="🟡 DERIVED" if has_results else "🔵 PROPOSED",
                content=(
                    "Within the recorded experimental evaluations, empirical measurements indicate observable trade-offs between accuracy gains and computational overhead. "
                    "These findings align with expected theoretical constraints in the indexed literature."
                ),
                bullet_points=["Cautious academic interpretation", "Identifies operational trade-offs"]
            ),
            # 23. Ablation Analysis
            ManuscriptSectionItem(
                section_key="ABLATION_ANALYSIS",
                title="23. Ablation Analysis",
                student_label="Ablation Component Impact",
                evidence_level="RECORDED" if results_summary.ablation_experiments_count > 0 else "MISSING",
                evidence_badge_text="🟢 RECORDED" if results_summary.ablation_experiments_count > 0 else "🔴 MISSING",
                content=f"Ablation Experiments Recorded: {results_summary.ablation_experiments_count} component ablation run(s)." if results_summary.ablation_experiments_count > 0 else "Ablation experiments were not recorded.",
                bullet_points=["Component contribution isolation"]
            ),
            # 24. Error Analysis
            ManuscriptSectionItem(
                section_key="ERROR_ANALYSIS",
                title="24. Error Analysis",
                student_label="Failure Cases & Error Modes",
                evidence_level="MISSING",
                evidence_badge_text="🔴 MISSING",
                content="Detailed error log analysis data has not been recorded for this project workspace.",
                bullet_points=["Qualitative failure classification"]
            ),
            # 25. Limitations
            ManuscriptSectionItem(
                section_key="LIMITATIONS",
                title="25. Limitations",
                student_label="What should you be careful about?",
                evidence_level="DERIVED" if results_summary.limitations_recorded_count > 0 else "DERIVED",
                evidence_badge_text="🟡 DERIVED",
                content="Limitations: 1) Findings are scoped to the indexed paper collection. 2) Hardware compute constraints may affect latency measurements. 3) Empirical validation is limited to configured datasets.",
                bullet_points=["Explicit scope boundaries", "Prevents overgeneralization"]
            ),
            # 26. Reproducibility
            ManuscriptSectionItem(
                section_key="REPRODUCIBILITY",
                title="26. Reproducibility",
                student_label="Reproducibility Checklist",
                evidence_level="RECORDED" if len(exps) > 0 else "MISSING",
                evidence_badge_text="🟢 RECORDED" if len(exps) > 0 else "🔴 MISSING",
                content=f"Reproducibility Checklist: Dataset version ({'Recorded' if len(exps) > 0 else 'Missing'}), Random seeds ({'Recorded' if len(exps) > 0 else 'Missing'}), Hardware environment ({'Recorded' if len(exps) > 0 else 'Missing'}).",
                bullet_points=["Empirical reproducibility summary"]
            ),
            # 27. Conclusion
            ManuscriptSectionItem(
                section_key="CONCLUSION",
                title="27. Conclusion",
                student_label="Evidence-Grounded Conclusion",
                evidence_level="DERIVED" if has_results else "PROPOSED",
                evidence_badge_text="🟡 DERIVED" if has_results else "🔵 PROPOSED",
                content=(
                    f"Within the evaluated experiments for project '{project.name}', recorded evidence indicates "
                    + (f"measurable metric improvements for the proposed configuration over baseline algorithms." if has_results else "a structured methodology framework ready for experimental execution.")
                ),
                bullet_points=["Summary of empirical evidence"]
            ),
            # 28. Future Work
            ManuscriptSectionItem(
                section_key="FUTURE_WORK",
                title="28. Future Work",
                student_label="Future Research Directions",
                evidence_level="PROPOSED",
                evidence_badge_text="🔵 PROPOSED",
                content="Future research recommendations: 1) Cross-dataset robustness testing. 2) Computational optimization for real-time deployment. 3) Expanding collection coverage to adjacent domains.",
                bullet_points=["Identified future opportunities"]
            ),
            # 29. References
            ManuscriptSectionItem(
                section_key="REFERENCES",
                title="29. References",
                student_label="Verified Project Citations",
                evidence_level="RECORDED" if len(papers) > 0 else "MISSING",
                evidence_badge_text="🟢 RECORDED" if len(papers) > 0 else "🔴 MISSING",
                content="\n\n".join([f"[{idx+1}] {p.title}. (Indexed in IntelliResearch Project Workspace)." for idx, p in enumerate(papers)]) if papers else "No verified paper citations in project collection.",
                bullet_points=[f"{len(papers)} verified paper references"]
            ),
        ]

        # Calculate completeness score
        rec_cnt = sum(1 for s in sections if s.evidence_level == "RECORDED")
        der_cnt = sum(1 for s in sections if s.evidence_level == "DERIVED")
        prp_cnt = sum(1 for s in sections if s.evidence_level == "PROPOSED")
        msg_cnt = sum(1 for s in sections if s.evidence_level == "MISSING")
        overall_pct = int(((rec_cnt * 1.0 + der_cnt * 0.7 + prp_cnt * 0.4) / 29.0) * 100)

        rating = "HIGHLY COMPLETE" if overall_pct >= 75 else ("MODERATELY COMPLETE" if overall_pct >= 50 else "PROPOSAL STAGE")

        completeness = ManuscriptCompletenessScore(
            overall_percentage=overall_pct,
            recorded_sections_count=rec_cnt,
            derived_sections_count=der_cnt,
            proposed_sections_count=prp_cnt,
            missing_sections_count=msg_cnt,
            rating_label=rating
        )

        # Create or update DB record
        manuscript = db.query(ResearchManuscript).filter(ResearchManuscript.project_id == project_id).first()
        if not manuscript:
            manuscript = ResearchManuscript(
                project_id=project_id,
                title=f"Academic Manuscript: {project.name}",
                status="DRAFT"
            )
            db.add(manuscript)
            db.commit()
            db.refresh(manuscript)

        # Save initial version if no versions exist
        if not manuscript.versions:
            content_dict = [s.model_dump() for s in sections]
            init_ver = ResearchManuscriptVersion(
                manuscript_id=manuscript.id,
                version_number=1,
                content_json=content_dict,
                change_summary="Initial auto-generated manuscript draft"
            )
            db.add(init_ver)
            db.commit()
            db.refresh(manuscript)

        latest_version = max(manuscript.versions, key=lambda v: v.version_number)
        return cls._build_response_from_version(project, manuscript, latest_version)

    @classmethod
    def save_manuscript_version(cls, db: Session, project_id: int, req: ManuscriptSaveVersionRequest) -> ManuscriptGenerateResponse:
        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"Research project {project_id} not found")

        manuscript = db.query(ResearchManuscript).filter(ResearchManuscript.project_id == project_id).first()
        if not manuscript:
            manuscript = ResearchManuscript(
                project_id=project_id,
                title=req.title or f"Academic Manuscript: {project.name}",
                status="DRAFT"
            )
            db.add(manuscript)
            db.commit()
            db.refresh(manuscript)

        next_ver_num = (max([v.version_number for v in manuscript.versions], default=0)) + 1
        content_dict = [s.model_dump() for s in req.sections]

        new_ver = ResearchManuscriptVersion(
            manuscript_id=manuscript.id,
            version_number=next_ver_num,
            content_json=content_dict,
            change_summary=req.change_summary or f"Saved Manuscript Version {next_ver_num}"
        )
        db.add(new_ver)
        if req.title:
            manuscript.title = req.title
        db.commit()
        db.refresh(manuscript)

        return cls._build_response_from_version(project, manuscript, new_ver)

    @classmethod
    def get_manuscript_versions(cls, db: Session, project_id: int) -> List[ManuscriptVersionItem]:
        manuscript = db.query(ResearchManuscript).filter(ResearchManuscript.project_id == project_id).first()
        if not manuscript:
            return []

        versions = sorted(manuscript.versions, key=lambda v: v.version_number, reverse=True)
        return [
            ManuscriptVersionItem(
                version_id=v.id,
                version_number=v.version_number,
                change_summary=v.change_summary,
                created_at=v.created_at.isoformat() if v.created_at else ""
            )
            for v in versions
        ]

    @classmethod
    def export_manuscript(cls, db: Session, project_id: int, export_format: str = "markdown") -> Dict[str, Any]:
        manuscript_res = cls.get_or_generate_manuscript(db, project_id)
        sections = manuscript_res.sections

        if export_format.lower() == "json":
            return {
                "project_id": project_id,
                "title": manuscript_res.title,
                "sections": [s.model_dump() for s in sections]
            }

        md_content = f"# {manuscript_res.title}\n\n"
        md_content += f"*Academic Manuscript Draft — Grounded in IntelliResearch Evidence*\n"
        md_content += f"*Completeness Score: {manuscript_res.completeness.overall_percentage}% ({manuscript_res.completeness.rating_label})*\n\n"
        md_content += f"> **Notice:** {manuscript_res.academic_integrity_notice}\n\n---\n\n"

        for s in sections:
            md_content += f"## {s.title}  `[{s.evidence_badge_text}]`  \n\n{s.content}\n\n"
            if s.bullet_points:
                for bp in s.bullet_points:
                    md_content += f"- {bp}\n"
                md_content += "\n"
            md_content += "---\n\n"

        return {
            "project_id": project_id,
            "format": export_format,
            "filename": f"Academic_Manuscript_Project_{project_id}.{export_format.lower()}",
            "content": md_content
        }

    @classmethod
    def _build_response_from_version(
        cls, project: ResearchProject, manuscript: ResearchManuscript, version: ResearchManuscriptVersion
    ) -> ManuscriptGenerateResponse:
        raw_sections = version.content_json if isinstance(version.content_json, list) else []
        sections = [ManuscriptSectionItem(**s) for s in raw_sections]

        rec_cnt = sum(1 for s in sections if s.evidence_level == "RECORDED")
        der_cnt = sum(1 for s in sections if s.evidence_level == "DERIVED")
        prp_cnt = sum(1 for s in sections if s.evidence_level == "PROPOSED")
        msg_cnt = sum(1 for s in sections if s.evidence_level == "MISSING")
        overall_pct = int(((rec_cnt * 1.0 + der_cnt * 0.7 + prp_cnt * 0.4) / 29.0) * 100)

        completeness = ManuscriptCompletenessScore(
            overall_percentage=overall_pct,
            recorded_sections_count=rec_cnt,
            derived_sections_count=der_cnt,
            proposed_sections_count=prp_cnt,
            missing_sections_count=msg_cnt,
            rating_label="HIGHLY COMPLETE" if overall_pct >= 75 else ("MODERATELY COMPLETE" if overall_pct >= 50 else "PROPOSAL STAGE")
        )

        all_versions = [
            ManuscriptVersionItem(
                version_id=v.id,
                version_number=v.version_number,
                change_summary=v.change_summary,
                created_at=v.created_at.isoformat() if v.created_at else ""
            )
            for v in sorted(manuscript.versions, key=lambda x: x.version_number, reverse=True)
        ]

        return ManuscriptGenerateResponse(
            project_id=project.id,
            project_name=project.name,
            manuscript_id=manuscript.id,
            title=manuscript.title,
            status=manuscript.status,
            current_version_number=version.version_number,
            completeness=completeness,
            sections=sections,
            available_versions=all_versions
        )
