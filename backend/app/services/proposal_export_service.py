import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional
import fitz  # PyMuPDF

from app.schemas.research_direction_schema import ResearchDirectionResponse

logger = logging.getLogger(__name__)

EXPORT_DISCLAIMER = (
    "This research direction is derived from evidence available in the indexed research collection. "
    "It represents a potential direction for further investigation and does not establish global academic novelty or guarantee research originality."
)


class ProposalExportService:
    """
    Service responsible for exporting Phase 4 actionable research directions into
    Markdown (.md), JSON (.json), and PDF (.pdf) formats.
    """

    @staticmethod
    def get_export_filename(format_str: str) -> str:
        """Generate download filename based on format."""
        fmt = format_str.lower().strip()
        if fmt in ("md", "markdown"):
            return "intelliresearch_research_directions.md"
        elif fmt == "json":
            return "intelliresearch_research_directions.json"
        elif fmt == "pdf":
            return "intelliresearch_research_directions.pdf"
        else:
            return "intelliresearch_research_directions.txt"

    @classmethod
    def export_to_markdown(cls, directions_resp: ResearchDirectionResponse) -> str:
        """
        Generate academic Markdown (.md) document containing exported research directions.
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        lines = [
            "# IntelliResearch — Actionable Research Directions Report",
            "",
            f"**Exported:** {timestamp}  ",
            f"**Total Directions Exported:** {directions_resp.total_directions}  ",
            f"**Collection Scope:** Indexed Supabase PostgreSQL Research Collection",
            "",
            "---",
            ""
        ]

        if directions_resp.total_directions == 0:
            lines.append("### No Actionable Research Directions Found")
            lines.append("")
            lines.append("The current paper collection does not have sufficient cross-paper evidence to generate directions.")
            lines.append("")
            lines.append("---")
            lines.append("")
            lines.append(f"**Disclaimer:** {directions_resp.collection_disclaimer}")
            return "\n".join(lines)

        for idx, dir_item in enumerate(directions_resp.directions, 1):
            lines.extend([
                f"## {idx}. {dir_item.title}",
                "",
                f"**Direction Score:** `{dir_item.direction_score}` | **Confidence Level:** `{dir_item.confidence}`",
                "",
                "### Research Problem",
                f"{dir_item.research_problem}",
                "",
                "### Why This May Be Worth Exploring",
                f"{dir_item.motivation}",
                "",
                "### Missing / Underrepresented Aspect",
                f"{dir_item.missing_aspect}",
                "",
                "### Proposed Direction",
                f"{dir_item.proposed_direction}",
                "",
                "### Evidence Metrics",
                "",
                "| Signal Metric | Value | Description |",
                "| :--- | :---: | :--- |",
                f"| **Gap Score** | `{dir_item.evidence.gap_score}` | Composite graph and similarity distance |",
                f"| **Semantic Evidence** | `{dir_item.evidence.semantic_evidence}` | SBERT embedding vector similarity |",
                f"| **Link Prediction Score** | `{dir_item.evidence.link_prediction_score}` | Graph topological link prediction |",
                f"| **Underrepresentation Score** | `{dir_item.evidence.underrepresentation_score}` | Relative concept sparsity across collection |",
                f"| **Collection Coverage** | `{dir_item.evidence.collection_coverage}%` | Percentage of papers with related concepts |",
                ""
            ])

            if dir_item.existing_evidence:
                lines.append("#### Graph Rationale Notes")
                for note in dir_item.existing_evidence:
                    lines.append(f"- {note}")
                lines.append("")

            lines.append("### Supporting Papers")
            if dir_item.supporting_papers:
                for sp in dir_item.supporting_papers:
                    lines.append(f"- **Paper ID {sp.paper_id}:** *{sp.title}* — {sp.role}")
            else:
                lines.append("- *No direct supporting papers identified.*")
            lines.append("")

            lines.append("### Candidate Approaches & Entities")
            if dir_item.candidate_algorithms:
                algos_str = ", ".join([f"`{a.name}`" for a in dir_item.candidate_algorithms])
                lines.append(f"- **Algorithms:** {algos_str}")
            if dir_item.candidate_datasets:
                ds_str = ", ".join([f"`{d.name}`" for d in dir_item.candidate_datasets])
                lines.append(f"- **Datasets:** {ds_str}")
            if dir_item.candidate_methodologies:
                m_str = ", ".join([f"`{m.name}`" for m in dir_item.candidate_methodologies])
                lines.append(f"- **Methodologies:** {m_str}")
            lines.append("")

            lines.append("### Disclaimer")
            lines.append(f"> {dir_item.disclaimer}")
            lines.append("")
            lines.append("---")
            lines.append("")

        lines.append(f"**Global Collection Disclaimer:** {directions_resp.collection_disclaimer}")
        return "\n".join(lines)

    @classmethod
    def export_to_json(cls, directions_resp: ResearchDirectionResponse) -> str:
        """
        Generate machine-readable JSON export containing research directions.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        payload = {
            "schema_version": "1.0",
            "export_timestamp": timestamp,
            "total_directions": directions_resp.total_directions,
            "collection_disclaimer": directions_resp.collection_disclaimer,
            "directions": [d.model_dump() for d in directions_resp.directions]
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)

    @classmethod
    def export_to_pdf(cls, directions_resp: ResearchDirectionResponse) -> bytes:
        """
        Generate printable academic PDF document bytes using PyMuPDF (fitz).
        """
        doc = fitz.open()
        font_name = "helv"
        margin_left = 40
        margin_right = 555
        margin_top = 40
        margin_bottom = 800
        max_width = margin_right - margin_left

        page = doc.new_page(width=595, height=842) # A4 size
        y = margin_top

        def check_page_space(required_h: float) -> fitz.Page:
            nonlocal page, y
            if y + required_h > margin_bottom:
                page = doc.new_page(width=595, height=842)
                y = margin_top
            return page

        # Document Header
        page.insert_text((margin_left, y), "IntelliResearch — Actionable Research Directions Report", fontsize=16, fontname="helv", color=(0.1, 0.15, 0.3))
        y += 24
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        page.insert_text((margin_left, y), f"Exported: {timestamp} | Total Directions: {directions_resp.total_directions}", fontsize=9, fontname="helv", color=(0.4, 0.4, 0.4))
        y += 18

        # Header Line
        page.draw_line(fitz.Point(margin_left, y), fitz.Point(margin_right, y), color=(0.8, 0.8, 0.8), width=0.8)
        y += 15

        if directions_resp.total_directions == 0:
            page.insert_text((margin_left, y), "No actionable research directions currently identified.", fontsize=11, fontname="helv", color=(0.3, 0.3, 0.3))
            y += 20
            page.insert_text((margin_left, y), directions_resp.collection_disclaimer, fontsize=8, fontname="helv", color=(0.5, 0.5, 0.5))
            return doc.tobytes()

        def draw_wrapped_text(text: str, fontsize: int = 10, is_bold: bool = False, color=(0.1, 0.1, 0.1), line_spacing: int = 12) -> None:
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

        for idx, dir_item in enumerate(directions_resp.directions, 1):
            check_page_space(60)

            # Section Title
            draw_wrapped_text(f"{idx}. {dir_item.title}", fontsize=13, is_bold=True, color=(0.05, 0.2, 0.4), line_spacing=16)
            y += 4

            # Sub-header Score / Confidence
            score_text = f"Direction Score: {dir_item.direction_score}  |  Confidence: {dir_item.confidence}  |  Coverage: {dir_item.evidence.collection_coverage}%"
            draw_wrapped_text(score_text, fontsize=9, is_bold=True, color=(0.3, 0.3, 0.3), line_spacing=12)
            y += 4

            # Research Problem
            draw_wrapped_text("Research Problem:", fontsize=10, is_bold=True, color=(0.1, 0.3, 0.5), line_spacing=12)
            draw_wrapped_text(dir_item.research_problem, fontsize=9.5, is_bold=False, line_spacing=12)
            y += 4

            # Why Worth Exploring
            draw_wrapped_text("Why This May Be Worth Exploring:", fontsize=10, is_bold=True, color=(0.1, 0.3, 0.5), line_spacing=12)
            draw_wrapped_text(dir_item.motivation, fontsize=9.5, is_bold=False, line_spacing=12)
            y += 4

            # Missing Aspect
            draw_wrapped_text("Missing / Underrepresented Aspect:", fontsize=10, is_bold=True, color=(0.1, 0.3, 0.5), line_spacing=12)
            draw_wrapped_text(dir_item.missing_aspect, fontsize=9.5, is_bold=False, line_spacing=12)
            y += 4

            # Proposed Direction
            draw_wrapped_text("Proposed Direction:", fontsize=10, is_bold=True, color=(0.1, 0.3, 0.5), line_spacing=12)
            draw_wrapped_text(dir_item.proposed_direction, fontsize=9.5, is_bold=False, line_spacing=12)
            y += 4

            # Evidence Breakdown
            ev = dir_item.evidence
            ev_str = (
                f"Evidence Signals: Gap Score={ev.gap_score}, Semantic Similarity={ev.semantic_evidence}, "
                f"Link Prediction={ev.link_prediction_score}, Underrepresentation={ev.underrepresentation_score}"
            )
            draw_wrapped_text(ev_str, fontsize=8.5, is_bold=False, color=(0.3, 0.3, 0.3), line_spacing=11)
            y += 4

            # Supporting Papers
            if dir_item.supporting_papers:
                draw_wrapped_text("Supporting Papers:", fontsize=9.5, is_bold=True, color=(0.2, 0.2, 0.2), line_spacing=12)
                for sp in dir_item.supporting_papers:
                    draw_wrapped_text(f"• Paper ID {sp.paper_id}: '{sp.title}' - {sp.role}", fontsize=8.5, is_bold=False, line_spacing=11)
                y += 4

            # Candidate Entities
            algos = ", ".join([a.name for a in dir_item.candidate_algorithms]) if dir_item.candidate_algorithms else "N/A"
            datasets = ", ".join([d.name for d in dir_item.candidate_datasets]) if dir_item.candidate_datasets else "N/A"
            methods = ", ".join([m.name for m in dir_item.candidate_methodologies]) if dir_item.candidate_methodologies else "N/A"
            draw_wrapped_text(f"Candidate Algorithms: {algos}  |  Datasets: {datasets}  |  Methodologies: {methods}", fontsize=8.5, is_bold=False, color=(0.25, 0.25, 0.25), line_spacing=11)
            y += 4

            # Disclaimer for Direction
            draw_wrapped_text(f"Disclaimer: {dir_item.disclaimer}", fontsize=7.5, is_bold=False, color=(0.5, 0.5, 0.5), line_spacing=10)
            y += 8

            # Separator Line
            page = check_page_space(15)
            page.draw_line(fitz.Point(margin_left, y), fitz.Point(margin_right, y), color=(0.85, 0.85, 0.85), width=0.5)
            y += 12

        # Final Footer Disclaimer
        page = check_page_space(20)
        draw_wrapped_text(f"Global Disclaimer: {directions_resp.collection_disclaimer}", fontsize=7.5, is_bold=False, color=(0.5, 0.5, 0.5), line_spacing=9)

        return doc.tobytes()

    @classmethod
    def export_single_proposal_markdown(cls, proposal_data: Dict[str, Any], version_number: int = 1) -> str:
        """
        Generate academic Markdown (.md) document for a single proposal version containing all sections.
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        title = proposal_data.get("title", "Research Proposal")
        task_type = proposal_data.get("task_type", "GENERIC_RESEARCH")

        lines = [
            f"# {title}",
            "",
            f"**Proposal Version:** `VERSION {version_number}`  ",
            f"**Task Type:** `{task_type}`  ",
            f"**Source Direction ID:** `{proposal_data.get('source_direction_id', 'N/A')}`  ",
            f"**Exported:** {timestamp}  ",
            "",
            "---",
            "",
            "## 1. Executive Abstract",
            proposal_data.get("abstract", "N/A"),
            "",
            "## 2. Problem Statement",
            proposal_data.get("problem_statement", "N/A"),
            "",
            "## 3. Testable Research Question",
            proposal_data.get("research_question", "N/A"),
            "",
            "## 4. Measurable Research Objectives",
        ]

        objectives = proposal_data.get("objectives", [])
        if isinstance(objectives, list):
            for obj in objectives:
                lines.append(f"- {obj}")
        else:
            lines.append(str(objectives))
        lines.append("")

        lines.extend([
            "## 5. Research Motivation",
            proposal_data.get("research_motivation", "N/A"),
            "",
            "## 6. Related Work Synthesis",
            proposal_data.get("related_work_synthesis", "N/A"),
            "",
            "## 7. Identified Research Gap",
            proposal_data.get("research_gap", "N/A"),
            "",
            "## 8. Proposed Methodology",
            str(proposal_data.get("proposed_methodology", "N/A")),
            "",
            "## 9. Candidate Algorithms",
        ])

        algos = proposal_data.get("candidate_algorithms", [])
        algos_str = ", ".join([str(a) for a in algos]) if isinstance(algos, list) else str(algos)
        lines.append(algos_str or "Standard baseline & target algorithm suite")
        lines.append("")

        lines.extend([
            "## 10. Candidate Datasets & Provenance",
            f"**Dataset Evaluation Plan:** {proposal_data.get('dataset_evaluation_plan', 'N/A')}",
            "",
        ])

        prov = proposal_data.get("datasets_provenance", [])
        if isinstance(prov, list) and prov:
            lines.append("### Dataset Evidence Status:")
            for d in prov:
                lines.append(f"- **{d.get('dataset_name')}** (Papers: {d.get('source_paper_ids')}) — *{d.get('dataset_role')}* [{d.get('evidence_status', 'RECORDED_EVIDENCE')}]")
        lines.append("")

        lines.extend([
            "## 11. Structured Experimental Plan",
            str(proposal_data.get("experimental_plan", "N/A")),
            "",
            "## 12. Proposed Evaluation Metrics",
        ])

        eval_metrics = proposal_data.get("evaluation_metrics", "N/A")
        eval_metrics_str = ", ".join([str(m) for m in eval_metrics]) if isinstance(eval_metrics, list) else str(eval_metrics)
        lines.append(eval_metrics_str or "Standard task evaluation metrics")
        lines.append("")

        lines.extend([
            "## 13. Expected Contribution",
            str(proposal_data.get("expected_contribution", "N/A")),
            "",
            "## 14. Collection Limitations & Assumptions",
            str(proposal_data.get("limitations", "N/A")),
            "",
        ])

        # Protected Intelligence Signals
        ev_summary = proposal_data.get("evidence_summary", {})
        if isinstance(ev_summary, dict) and ev_summary:
            lines.extend([
                "## 15. Protected Intelligence Signals",
                f"- **Gap Score:** `{ev_summary.get('gap_score', 'N/A')}`",
                f"- **Semantic Evidence:** `{ev_summary.get('semantic_evidence', 'N/A')}`",
                f"- **Link Prediction Score:** `{ev_summary.get('link_prediction_score', 'N/A')}`",
                f"- **Underrepresentation Score:** `{ev_summary.get('underrepresentation_score', 'N/A')}`",
                f"- **Evidence Classification:** `{ev_summary.get('evidence_classification', 'N/A')}`",
                ""
            ])

        # Supporting Papers
        supp_papers = proposal_data.get("supporting_papers", [])
        if isinstance(supp_papers, list) and supp_papers:
            lines.append("## 16. Supporting Collection Papers")
            for sp in supp_papers:
                pid = sp.get("paper_id") or sp.get("id") if isinstance(sp, dict) else getattr(sp, "paper_id", "N/A")
                title_str = sp.get("title") if isinstance(sp, dict) else getattr(sp, "title", "")
                role_str = sp.get("role") if isinstance(sp, dict) else getattr(sp, "role", "Supporting evidence")
                lines.append(f"- **Paper ID {pid}:** *{title_str}* — {role_str} [RECORDED_EVIDENCE]")
            lines.append("")

        lines.extend([
            "---",
            f"> **Academic Disclaimer:** {proposal_data.get('disclaimer', EXPORT_DISCLAIMER)}"
        ])

        return "\n".join(lines)

    @classmethod
    def export_single_proposal_json(cls, proposal_data: Dict[str, Any], version_number: int = 1) -> str:
        """
        Generate machine-readable JSON export for a single proposal version.
        """
        payload = {
            "schema_version": "1.0",
            "version_number": version_number,
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "proposal": proposal_data
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)

    @classmethod
    def export_single_proposal_pdf(cls, proposal_data: Dict[str, Any], version_number: int = 1) -> bytes:
        """
        Generate printable academic PDF document bytes for a single proposal version using PyMuPDF (fitz).
        Renders complete proposal sections: Abstract, Problem Statement, RQ, Objectives, Motivation, Related Work,
        Research Gap, Methodology, Algorithms, Datasets, Experimental Plan, Metrics, Contribution, Limitations,
        Evidence Summary, Supporting Papers, and Academic Disclaimer.
        """
        doc = fitz.open()
        margin_left = 40
        margin_right = 555
        margin_top = 40
        margin_bottom = 800
        max_width = margin_right - margin_left

        page = doc.new_page(width=595, height=842)
        y = margin_top

        def check_page_space(required_h: float) -> fitz.Page:
            nonlocal page, y
            if y + required_h > margin_bottom:
                page = doc.new_page(width=595, height=842)
                y = margin_top
            return page

        def draw_wrapped_text(text: str, fontsize: int = 10, is_bold: bool = False, color=(0.1, 0.1, 0.1), line_spacing: int = 12) -> None:
            nonlocal page, y
            fname = "hebo" if is_bold else "helv"
            words = str(text).split()
            current_line = []
            for word in words:
                test_line = " ".join(current_line + [word])
                if fitz.get_text_length(test_line, fontname=fname, fontsize=fontsize) <= max_width:
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

        title = proposal_data.get("title", "Research Proposal")
        draw_wrapped_text(title, fontsize=15, is_bold=True, color=(0.05, 0.2, 0.4), line_spacing=18)
        y += 4

        timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        task_type = proposal_data.get('task_type', 'GENERIC_RESEARCH')
        meta_str = f"Proposal Version: VERSION {version_number} | Task Type: {task_type} | Exported: {timestamp_str}"
        draw_wrapped_text(meta_str, fontsize=8.5, is_bold=True, color=(0.35, 0.35, 0.35), line_spacing=11)
        y += 6

        # Draw line under header
        page.draw_line(fitz.Point(margin_left, y), fitz.Point(margin_right, y), color=(0.8, 0.8, 0.8), width=0.8)
        y += 12

        # Format objectives
        objectives = proposal_data.get("objectives", [])
        if isinstance(objectives, list):
            objectives_str = "\n".join([f"• {obj}" for obj in objectives])
        else:
            objectives_str = str(objectives)

        # Format algorithms
        algos = proposal_data.get("candidate_algorithms", [])
        algos_str = ", ".join([str(a) for a in algos]) if isinstance(algos, list) else str(algos)

        # Format datasets provenance
        prov = proposal_data.get("datasets_provenance", [])
        if isinstance(prov, list) and prov:
            prov_lines = [f"• {d.get('dataset_name')} (Papers: {d.get('source_paper_ids')}) - {d.get('dataset_role')} [{d.get('evidence_status', 'RECORDED_EVIDENCE')}]" for d in prov]
            datasets_str = "\n".join(prov_lines)
        else:
            datasets_str = str(proposal_data.get("dataset_evaluation_plan", "Suitable dataset evaluation plan required."))

        # Format metrics
        eval_m = proposal_data.get("evaluation_metrics", "")
        eval_m_str = ", ".join([str(m) for m in eval_m]) if isinstance(eval_m, list) else str(eval_m)

        sections = [
            ("1. Executive Abstract", proposal_data.get("abstract", "N/A")),
            ("2. Problem Statement", proposal_data.get("problem_statement", "N/A")),
            ("3. Testable Research Question", proposal_data.get("research_question", "N/A")),
            ("4. Measurable Research Objectives", objectives_str),
            ("5. Research Motivation", proposal_data.get("research_motivation", "N/A")),
            ("6. Related Work Synthesis", proposal_data.get("related_work_synthesis", "N/A")),
            ("7. Identified Research Gap", proposal_data.get("research_gap", "N/A")),
            ("8. Proposed Methodology", proposal_data.get("proposed_methodology", "N/A")),
            ("9. Candidate Algorithms", algos_str or "N/A"),
            ("10. Candidate Datasets & Provenance", datasets_str),
            ("11. Structured Experimental Plan", proposal_data.get("experimental_plan", "N/A")),
            ("12. Proposed Evaluation Metrics", eval_m_str or "N/A"),
            ("13. Expected Contribution", proposal_data.get("expected_contribution", "N/A")),
            ("14. Collection Limitations & Assumptions", proposal_data.get("limitations", "N/A"))
        ]

        for sec_title, sec_content in sections:
            check_page_space(35)
            draw_wrapped_text(sec_title, fontsize=10.5, is_bold=True, color=(0.1, 0.3, 0.5), line_spacing=13)
            y += 2
            # Handle multiline content line by line for clean paragraph rendering
            content_lines = str(sec_content).split("\n")
            for c_line in content_lines:
                if c_line.strip():
                    draw_wrapped_text(c_line.strip(), fontsize=9, is_bold=False, color=(0.15, 0.15, 0.15), line_spacing=11)
            y += 6

        # Supporting Collection Papers if available
        supp_papers = proposal_data.get("supporting_papers", [])
        if isinstance(supp_papers, list) and supp_papers:
            check_page_space(35)
            draw_wrapped_text("15. Supporting Collection Papers", fontsize=10.5, is_bold=True, color=(0.1, 0.3, 0.5), line_spacing=13)
            y += 2
            for sp in supp_papers:
                pid = sp.get("paper_id") or sp.get("id") if isinstance(sp, dict) else getattr(sp, "paper_id", "N/A")
                title_str = sp.get("title") if isinstance(sp, dict) else getattr(sp, "title", "")
                role_str = sp.get("role") if isinstance(sp, dict) else getattr(sp, "role", "Supporting evidence")
                draw_wrapped_text(f"• Paper ID {pid}: '{title_str}' - {role_str} [RECORDED_EVIDENCE]", fontsize=8.5, is_bold=False, line_spacing=11)
            y += 6

        # Disclaimer
        check_page_space(30)
        draw_wrapped_text(f"Academic Disclaimer: {proposal_data.get('disclaimer', EXPORT_DISCLAIMER)}", fontsize=7.5, is_bold=False, color=(0.5, 0.5, 0.5), line_spacing=10)

        return doc.tobytes()
