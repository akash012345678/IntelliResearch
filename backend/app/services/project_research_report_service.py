import json
import logging
from collections import Counter
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import fitz  # PyMuPDF

from app.models.project_model import ResearchProject, ProjectPaper, SavedResearchDirection
from app.models.paper_model import ResearchPaper
from app.models.proposal_model import Proposal, ProposalVersion
from app.services.project_intelligence_service import ProjectIntelligenceService
from app.schemas.project_report_schema import (
    ProjectSummaryInfo,
    ResearchProblemSummary,
    TraceabilityConcept,
    TraceabilityGap,
    TraceabilityDirection,
    TraceabilityProposal,
    EvidenceTraceabilityItem,
    ProposalSummaryItem,
    ProjectResearchReportResponse
)

logger = logging.getLogger(__name__)

REPORT_DISCLAIMER = (
    "This Project Research Report is derived exclusively from evidence contained within papers assigned to this Research Project. "
    "All analytics, gap scores, directions, and traceability links are generated deterministically for academic synthesis and do not establish global academic novelty or guarantee originality."
)


class ProjectResearchReportService:
    """
    Service responsible for generating consolidated project-scoped research reports
    and evidence traceability chains, as well as multi-format exports (Markdown, JSON, PDF).
    STRICTLY READ-ONLY with 0 database side effects.
    """

    @classmethod
    def get_export_filename(cls, format_str: str, project_id: int) -> str:
        """Generate download filename based on format and project ID."""
        fmt = format_str.lower().strip()
        if fmt in ("md", "markdown"):
            return f"project_{project_id}_research_report.md"
        elif fmt == "json":
            return f"project_{project_id}_research_report.json"
        elif fmt == "pdf":
            return f"project_{project_id}_research_report.pdf"
        else:
            return f"project_{project_id}_research_report.txt"

    @classmethod
    def generate_project_report(
        cls,
        project_id: int,
        db: Session,
        include_proposals: bool = True,
        include_relationships: bool = True,
        include_gaps: bool = True,
        include_directions: bool = True
    ) -> ProjectResearchReportResponse:
        """
        Generate ONE consolidated analytical report based ONLY on papers assigned to project_id.
        """
        # 1. Validate project existence
        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Research Project with ID {project_id} not found."
            )

        project_info = ProjectSummaryInfo(
            project_id=project.id,
            name=project.name,
            description=project.description,
            status=project.status or "ACTIVE"
        )

        # 2. Query assigned papers
        project_paper_ids = [
            pp.paper_id for pp in db.query(ProjectPaper).filter(ProjectPaper.project_id == project_id).all()
        ]

        if not project_paper_ids:
            # Handle empty project state gracefully
            empty_summary = {
                "total_papers": 0,
                "total_algorithms": 0,
                "total_datasets": 0,
                "total_methodologies": 0,
                "total_domains": 0,
                "total_keywords": 0
            }
            empty_problem = ResearchProblemSummary(
                summary_text="Insufficient evidence to determine a dominant research problem from the current project collection."
            )
            empty_shared = {"keywords": [], "algorithms": [], "datasets": [], "methodologies": [], "domains": []}

            return ProjectResearchReportResponse(
                project=project_info,
                collection_summary=empty_summary,
                paper_landscape=[],
                research_problem_summary=empty_problem,
                shared_concepts=empty_shared,
                paper_relationships=[],
                research_gaps=[],
                underrepresented_concepts=[],
                candidate_research_directions=[],
                evidence_traceability=[],
                proposal_summary=[],
                collection_disclaimer=REPORT_DISCLAIMER
            )

        # 3. Fetch project papers
        papers = db.query(ResearchPaper).filter(ResearchPaper.id.in_(project_paper_ids)).all()

        # 4. Leverage ProjectIntelligenceService for scoped analytics
        intel_resp = ProjectIntelligenceService.analyze_project(
            project_id=project_id,
            db=db,
            max_relationships=20,
            max_gaps=15,
            max_underrepresented=15,
            max_directions=10
        )

        # 5. Derive Research Problem Summary
        domain_counter = Counter()
        method_counter = Counter()
        algo_counter = Counter()
        theme_counter = Counter()

        for p in papers:
            for d in getattr(p, "application_domains", []) or []:
                if d: domain_counter[d] += 1
            for m in getattr(p, "methodologies", []) or []:
                if m: method_counter[m] += 1
            for a in getattr(p, "algorithms", []) or []:
                if a: algo_counter[a] += 1
            for k in getattr(p, "keywords", []) or []:
                if k: theme_counter[k] += 1

        top_domains = [item[0] for item in domain_counter.most_common(3)]
        top_methods = [item[0] for item in method_counter.most_common(3)]
        top_algos = [item[0] for item in algo_counter.most_common(3)]
        top_themes = [item[0] for item in theme_counter.most_common(5)]

        if not top_domains and not top_methods and not top_algos and not top_themes:
            summary_text = "Insufficient evidence to determine a dominant research problem from the current project collection."
        else:
            parts = []
            if top_domains:
                parts.append(f"primary domains of {', '.join(top_domains)}")
            if top_methods:
                parts.append(f"methodologies focused on {', '.join(top_methods)}")
            if top_algos:
                parts.append(f"core algorithms including {', '.join(top_algos)}")
            if top_themes:
                parts.append(f"key themes encompassing {', '.join(top_themes)}")
            summary_text = f"Research focus in this collection emphasizes {' with '.join(parts)}."

        problem_summary = ResearchProblemSummary(
            dominant_domains=top_domains,
            dominant_methods=top_methods,
            dominant_algorithms=top_algos,
            dominant_research_themes=top_themes,
            summary_text=summary_text
        )

        # 6. Fetch Project Proposals & Versions
        project_proposals = db.query(Proposal).filter(Proposal.project_id == project_id).all()
        proposal_summary_items: List[ProposalSummaryItem] = []

        for prop in project_proposals:
            latest_v = db.query(ProposalVersion).filter(
                ProposalVersion.proposal_id == prop.id
            ).order_by(ProposalVersion.version_number.desc()).first()

            latest_version_num = latest_v.version_number if latest_v else 1
            p_content = latest_v.proposal_data if (latest_v and getattr(latest_v, "proposal_data", None)) else {}
            gen_mode = getattr(latest_v, "generation_mode", "TEMPLATE") if latest_v else "TEMPLATE"

            supporting_papers = p_content.get("supporting_papers", []) if isinstance(p_content, dict) else []
            evidence_summary = p_content.get("evidence_summary", {}) if isinstance(p_content, dict) else {}
            src_dir = prop.source_direction_id or (p_content.get("source_direction_id") if isinstance(p_content, dict) else None)

            prop_uuid = getattr(prop, "proposal_uuid", str(prop.id))

            proposal_summary_items.append(ProposalSummaryItem(
                proposal_id=prop_uuid,
                db_id=prop.id,
                title=prop.title,
                status=prop.status or "DRAFT",
                generation_mode=gen_mode,
                latest_version=latest_version_num,
                supporting_papers=supporting_papers if isinstance(supporting_papers, list) else [],
                evidence_summary=evidence_summary if isinstance(evidence_summary, dict) else {},
                source_direction=src_dir
            ))


        # Helper function to convert Pydantic items to dicts
        def to_dict_item(it):
            if hasattr(it, "model_dump"):
                return it.model_dump()
            elif hasattr(it, "dict"):
                return it.dict()
            elif isinstance(it, dict):
                return it
            return {}

        raw_landscape = [to_dict_item(it) for it in (intel_resp.paper_landscape or [])]
        raw_relationships = [to_dict_item(it) for it in (intel_resp.paper_relationships or [])]
        raw_gaps = [to_dict_item(it) for it in (intel_resp.research_gaps or [])]
        raw_underrepresented = [to_dict_item(it) for it in (intel_resp.underrepresented_concepts or [])]
        raw_directions = [to_dict_item(it) for it in (intel_resp.candidate_research_directions or [])]

        raw_shared = {}
        if isinstance(intel_resp.shared_concepts, dict):
            for k_cat, v_list in intel_resp.shared_concepts.items():
                raw_shared[k_cat] = [to_dict_item(it) for it in (v_list or [])]

        # 7. Build Evidence Traceability Chains (Paper -> Concept -> Gap -> Direction -> Proposal -> Version)
        traceability_items: List[EvidenceTraceabilityItem] = []

        for paper in papers:
            # Determine top concept for paper
            concept_node: Optional[TraceabilityConcept] = None
            if paper.algorithms and len(paper.algorithms) > 0:
                concept_node = TraceabilityConcept(type="ALGORITHM", name=paper.algorithms[0])
            elif paper.methodologies and len(paper.methodologies) > 0:
                concept_node = TraceabilityConcept(type="METHODOLOGY", name=paper.methodologies[0])
            elif paper.datasets and len(paper.datasets) > 0:
                concept_node = TraceabilityConcept(type="DATASET", name=paper.datasets[0])
            elif paper.keywords and len(paper.keywords) > 0:
                concept_node = TraceabilityConcept(type="KEYWORD", name=paper.keywords[0])

            # Find matching gap
            gap_node: Optional[TraceabilityGap] = None
            for g in raw_gaps:
                g_concept = g.get("missing_concept", "")
                if concept_node and concept_node.name.lower() in g_concept.lower():
                    gap_node = TraceabilityGap(
                        gap_score=g.get("gap_score", 0.0),
                        confidence=g.get("confidence", "Moderate"),
                        missing_concept=g_concept
                    )
                    break
            if not gap_node and raw_gaps:
                g = raw_gaps[0]
                gap_node = TraceabilityGap(
                    gap_score=g.get("gap_score", 0.0),
                    confidence=g.get("confidence", "Moderate"),
                    missing_concept=g.get("missing_concept")
                )

            # Find matching direction
            direction_node: Optional[TraceabilityDirection] = None
            for d in raw_directions:
                d_id = d.get("direction_id", "")
                d_title = d.get("title", "")
                d_papers = d.get("supporting_papers", [])
                is_paper_match = any(sp.get("paper_id") == paper.id for sp in d_papers if isinstance(sp, dict))
                if is_paper_match or (gap_node and gap_node.missing_concept and gap_node.missing_concept.lower() in d_title.lower()):
                    direction_node = TraceabilityDirection(direction_id=d_id, title=d_title)
                    break
            if not direction_node and raw_directions:
                d = raw_directions[0]
                direction_node = TraceabilityDirection(
                    direction_id=d.get("direction_id", "dir_1"),
                    title=d.get("title", "Research Direction")
                )

            # Find matching proposal
            proposal_node: Optional[TraceabilityProposal] = None
            for prop_item in proposal_summary_items:
                is_prop_paper_match = any(
                    sp.get("paper_id") == paper.id for sp in prop_item.supporting_papers if isinstance(sp, dict)
                )
                is_dir_match = direction_node and prop_item.source_direction == direction_node.direction_id
                if is_prop_paper_match or is_dir_match:
                    proposal_node = TraceabilityProposal(
                        proposal_id=prop_item.proposal_id,
                        db_id=prop_item.db_id,
                        title=prop_item.title,
                        latest_version=prop_item.latest_version
                    )
                    break

            traceability_items.append(EvidenceTraceabilityItem(
                paper_id=paper.id,
                paper_title=paper.title,
                concept=concept_node,
                gap=gap_node,
                research_direction=direction_node,
                proposal=proposal_node
            ))

        # 8. Assemble Full Response
        coll_summary_dict = to_dict_item(intel_resp.collection_summary)

        return ProjectResearchReportResponse(
            project=project_info,
            collection_summary=coll_summary_dict,
            paper_landscape=raw_landscape,
            research_problem_summary=problem_summary,
            shared_concepts=raw_shared,
            paper_relationships=raw_relationships if include_relationships else [],
            research_gaps=raw_gaps if include_gaps else [],
            underrepresented_concepts=raw_underrepresented,
            candidate_research_directions=raw_directions if include_directions else [],
            evidence_traceability=traceability_items,
            proposal_summary=proposal_summary_items if include_proposals else [],
            collection_disclaimer=REPORT_DISCLAIMER
        )


    # =========================================================================
    # EXPORT GENERATION METHODS
    # =========================================================================

    @classmethod
    def export_report_to_markdown(cls, report: ProjectResearchReportResponse) -> str:
        """Generate academic Markdown (.md) document for Project Research Report."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        p = report.project
        cs = report.collection_summary
        prob = report.research_problem_summary

        lines = [
            f"# Project Research Report: {p.name}",
            "",
            f"**Project ID:** `{p.project_id}` | **Status:** `{p.status}` | **Generated:** `{timestamp}`  ",
            f"**Project Description:** {p.description or 'N/A'}  ",
            "",
            "---",
            "",
            "## 1. Executive Collection Summary",
            "",
            "| Metric | Value |",
            "| :--- | :---: |",
            f"| **Assigned Research Papers** | `{cs.get('total_papers', 0)}` |",
            f"| **Unique Algorithms** | `{cs.get('total_algorithms', 0)}` |",
            f"| **Unique Datasets** | `{cs.get('total_datasets', 0)}` |",
            f"| **Unique Methodologies** | `{cs.get('total_methodologies', 0)}` |",
            f"| **Application Domains** | `{cs.get('total_domains', 0)}` |",
            f"| **Indexed Keywords** | `{cs.get('total_keywords', 0)}` |",
            "",
            "---",
            "",
            "## 2. Research Focus & Problem Summary",
            "",
            f"{prob.summary_text or 'No dominant research problem established.'}",
            "",
            f"- **Dominant Domains:** {', '.join(prob.dominant_domains) if prob.dominant_domains else 'None'}",
            f"- **Dominant Methodologies:** {', '.join(prob.dominant_methods) if prob.dominant_methods else 'None'}",
            f"- **Dominant Algorithms:** {', '.join(prob.dominant_algorithms) if prob.dominant_algorithms else 'None'}",
            f"- **Dominant Themes:** {', '.join(prob.dominant_research_themes) if prob.dominant_research_themes else 'None'}",
            "",
            "---",
            "",
            "## 3. Assigned Paper Landscape",
            ""
        ]

        if not report.paper_landscape:
            lines.append("_No research papers currently assigned to this project._\n")
        else:
            for pl in report.paper_landscape:
                lines.extend([
                    f"### Paper #{pl.get('id')}: {pl.get('title')}",
                    f"**Filename:** `{pl.get('filename')}` | **Uploaded:** `{pl.get('uploaded_at', 'N/A')}`",
                    "",
                    f"{pl.get('abstract', 'No abstract available.')}",
                    "",
                    f"- **Algorithms:** {', '.join(pl.get('algorithms', [])) or 'N/A'}",
                    f"- **Datasets:** {', '.join(pl.get('datasets', [])) or 'N/A'}",
                    f"- **Methodologies:** {', '.join(pl.get('methodologies', [])) or 'N/A'}",
                    f"- **Domains:** {', '.join(pl.get('application_domains', [])) or 'N/A'}",
                    ""
                ])

        def fmt_concept_list(items):
            if not items:
                return "None"
            res = []
            for it in items:
                if isinstance(it, str):
                    res.append(it)
                elif isinstance(it, dict):
                    res.append(it.get("name", str(it)))
                else:
                    res.append(getattr(it, "name", str(it)))
            return ", ".join(res) if res else "None"

        lines.extend([
            "---",
            "",
            "## 4. Shared Research Concepts",
            "",
            f"- **Shared Algorithms:** {fmt_concept_list(report.shared_concepts.get('algorithms', []))}",
            f"- **Shared Datasets:** {fmt_concept_list(report.shared_concepts.get('datasets', []))}",
            f"- **Shared Methodologies:** {fmt_concept_list(report.shared_concepts.get('methodologies', []))}",
            f"- **Shared Domains:** {fmt_concept_list(report.shared_concepts.get('domains', []))}",
            f"- **Shared Keywords:** {fmt_concept_list(report.shared_concepts.get('keywords', []))}",
            "",
            "---",
            "",
            "## 5. Identified Research Gaps",
            ""
        ])


        if not report.research_gaps:
            lines.append("_No project-scoped research gaps identified._\n")
        else:
            for idx, g in enumerate(report.research_gaps, 1):
                lines.extend([
                    f"### Gap {idx}: {g.get('missing_concept')}",
                    f"**Gap Score:** `{g.get('gap_score')}` | **Confidence:** `{g.get('confidence')}`",
                    f"{g.get('explanation')}",
                    ""
                ])

        lines.extend([
            "---",
            "",
            "## 6. Candidate Research Directions",
            ""
        ])

        if not report.candidate_research_directions:
            lines.append("_No project-scoped candidate research directions generated._\n")
        else:
            for idx, d in enumerate(report.candidate_research_directions, 1):
                lines.extend([
                    f"### Direction {idx}: {d.get('title')}",
                    f"**Direction ID:** `{d.get('direction_id')}` | **Score:** `{d.get('direction_score')}` | **Confidence:** `{d.get('confidence')}`",
                    f"**Problem:** {d.get('research_problem')}",
                    f"**Proposed Direction:** {d.get('proposed_direction')}",
                    ""
                ])

        lines.extend([
            "---",
            "",
            "## 7. Evidence Traceability Chains",
            "",
            "| Paper ID | Paper Title | Associated Concept | Identified Gap | Source Direction | Proposal & Version |",
            "| :---: | :--- | :--- | :--- | :--- | :--- |"
        ])

        for tr in report.evidence_traceability:
            c_str = f"{tr.concept.type}: {tr.concept.name}" if tr.concept else "Not yet connected"
            g_str = f"Score {tr.gap.gap_score}" if tr.gap else "Not yet connected"
            d_str = tr.research_direction.title[:30] + "..." if tr.research_direction else "Not yet connected"
            p_str = f"{tr.proposal.title[:25]}... (v{tr.proposal.latest_version})" if tr.proposal else "Not yet connected"

            lines.append(f"| #{tr.paper_id} | {tr.paper_title[:35]} | {c_str} | {g_str} | {d_str} | {p_str} |")

        lines.extend([
            "",
            "---",
            "",
            "## 8. Associated Proposals Summary",
            ""
        ])

        if not report.proposal_summary:
            lines.append("_No proposals currently saved under this research project._\n")
        else:
            for prop in report.proposal_summary:
                lines.extend([
                    f"### Proposal: {prop.title}",
                    f"**ID:** `{prop.proposal_id}` | **Status:** `{prop.status}` | **Latest Version:** `v{prop.latest_version}`",
                    f"**Source Direction:** `{prop.source_direction or 'Custom Draft'}`",
                    ""
                ])

        lines.extend([
            "---",
            "",
            f"**Disclaimer:** {report.collection_disclaimer}"
        ])

        return "\n".join(lines)

    @classmethod
    def export_report_to_json(cls, report: ProjectResearchReportResponse) -> str:
        """Generate JSON string representation of Project Research Report."""
        data = report.model_dump() if hasattr(report, "model_dump") else report.dict()
        return json.dumps(data, indent=2, default=str)

    @classmethod
    def export_report_to_pdf(cls, report: ProjectResearchReportResponse) -> bytes:
        """Generate formatted PDF document for Project Research Report using PyMuPDF."""
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)  # A4

        margin_left = 40
        margin_right = 555
        margin_top = 40
        margin_bottom = 800
        max_width = margin_right - margin_left
        y = margin_top

        def check_page_space(required_h: int = 20) -> fitz.Page:
            nonlocal page, y
            if y + required_h > margin_bottom:
                page = doc.new_page(width=595, height=842)
                y = margin_top
            return page

        def draw_text(text: str, fontsize: int = 10, is_bold: bool = False, color=(0.1, 0.1, 0.1), line_spacing: int = 12) -> None:
            nonlocal page, y
            fname = "hebo" if is_bold else "helv"
            words = text.split()
            current_line = []

            for word in words:
                test_line = " ".join(current_line + [word])
                text_len = fitz.get_text_length(test_line, fontname=fname, fontsize=fontsize)
                if text_len <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        page = check_page_space(line_spacing)
                        page.insert_text((margin_left, y), " ".join(current_line), fontsize=fontsize, fontname=fname, color=color)
                        y += line_spacing
                    current_line = [word]

            if current_line:
                page = check_page_space(line_spacing)
                page.insert_text((margin_left, y), " ".join(current_line), fontsize=fontsize, fontname=fname, color=color)
                y += line_spacing

        p = report.project
        cs = report.collection_summary

        # Title Block
        draw_text(f"Project Research Report: {p.name}", fontsize=15, is_bold=True, color=(0.05, 0.15, 0.35), line_spacing=18)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        draw_text(f"Project ID: {p.project_id} | Status: {p.status} | Generated: {timestamp}", fontsize=8.5, color=(0.4, 0.4, 0.4), line_spacing=11)
        y += 6

        page.draw_line(fitz.Point(margin_left, y), fitz.Point(margin_right, y), color=(0.8, 0.8, 0.8), width=0.8)
        y += 12

        # 1. Collection Summary
        draw_text("1. Executive Collection Summary", fontsize=11, is_bold=True, color=(0.1, 0.2, 0.4), line_spacing=14)
        summary_str = (
            f"Assigned Papers: {cs.get('total_papers', 0)}  |  Algorithms: {cs.get('total_algorithms', 0)}  |  "
            f"Datasets: {cs.get('total_datasets', 0)}  |  Methodologies: {cs.get('total_methodologies', 0)}  |  "
            f"Domains: {cs.get('total_domains', 0)}  |  Keywords: {cs.get('total_keywords', 0)}"
        )
        draw_text(summary_str, fontsize=9, is_bold=True, color=(0.2, 0.2, 0.2), line_spacing=12)
        y += 8

        # 2. Research Focus & Problem Summary
        draw_text("2. Research Focus & Problem Summary", fontsize=11, is_bold=True, color=(0.1, 0.2, 0.4), line_spacing=14)
        prob = report.research_problem_summary
        draw_text(prob.summary_text or "No dominant research problem established.", fontsize=9, line_spacing=12)
        y += 8

        # 3. Assigned Paper Landscape
        draw_text(f"3. Assigned Paper Landscape ({len(report.paper_landscape)})", fontsize=11, is_bold=True, color=(0.1, 0.2, 0.4), line_spacing=14)
        for pl in report.paper_landscape:
            draw_text(f"• Paper #{pl.get('id')}: {pl.get('title')}", fontsize=9.5, is_bold=True, line_spacing=12)
            if pl.get("abstract"):
                draw_text(f"  {pl.get('abstract')[:140]}...", fontsize=8.5, color=(0.3, 0.3, 0.3), line_spacing=11)
            y += 4

        y += 6

        # 4. Identified Gaps & Directions
        draw_text(f"4. Research Gaps & Directions ({len(report.research_gaps)} Gaps, {len(report.candidate_research_directions)} Directions)", fontsize=11, is_bold=True, color=(0.1, 0.2, 0.4), line_spacing=14)
        for g in report.research_gaps[:5]:
            draw_text(f"Gap: {g.get('missing_concept')} (Score: {g.get('gap_score')})", fontsize=9, is_bold=True, color=(0.4, 0.2, 0.0), line_spacing=12)
        for d in report.candidate_research_directions[:5]:
            draw_text(f"Direction: {d.get('title')}", fontsize=9, is_bold=True, color=(0.0, 0.3, 0.2), line_spacing=12)
        y += 8

        # 5. Evidence Traceability Chains
        draw_text(f"5. Evidence Traceability Chains ({len(report.evidence_traceability)} Papers)", fontsize=11, is_bold=True, color=(0.1, 0.2, 0.4), line_spacing=14)
        for tr in report.evidence_traceability:
            c_str = f"{tr.concept.type}:{tr.concept.name}" if tr.concept else "No concept"
            g_str = f"Gap {tr.gap.gap_score}" if tr.gap else "No gap"
            d_str = tr.research_direction.title[:25] + "..." if tr.research_direction else "No direction"
            p_str = f"Proposal (v{tr.proposal.latest_version})" if tr.proposal else "No proposal"
            draw_text(f"• Paper #{tr.paper_id} → {c_str} → {g_str} → {d_str} → {p_str}", fontsize=8.5, line_spacing=11)

        y += 12
        page = check_page_space(20)
        draw_text(f"Disclaimer: {report.collection_disclaimer}", fontsize=7.5, color=(0.5, 0.5, 0.5), line_spacing=10)

        return doc.tobytes()
