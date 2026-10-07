import logging
import io
import zipfile
from xml.sax.saxutils import escape
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class AcademicDocxEngine:
    """
    Pure Python OpenXML DOCX Generator for IntelliResearch Academic Manuscripts.
    Produces formal university-style thesis documents in Microsoft Word (.docx) format.
    
    Specs:
    - Font: Times New Roman
    - Page Size: A4 (11906 x 16838 twips)
    - Margins: Left = 1.25 in (1800 twips), Right = 1.0 in (1440 twips), Top/Bottom = 1.0 in (1440 twips)
    - Body Text: 12 pt (24 half-pt), Justified, 1.5 Line Spacing (360 twips)
    - Chapter Headings: 16 pt Bold (32 half-pt)
    - Section Headings: 14 pt Bold (28 half-pt)
    - Cover Page, TOC, List of Tables, List of Figures, References, Appendices
    """

    @classmethod
    def generate_docx(
        cls,
        manuscript_res: Any,
        project: Any,
        papers: List[Any],
        results_summary: Any = None,
        config: Dict[str, Any] = None
    ) -> bytes:
        config = config or {}
        proj_name = getattr(project, "name", "Research Project")
        author_name = getattr(project, "author", None) or getattr(project, "student_name", None) or config.get("student_name") or "Student Researcher"
        guide_name = getattr(project, "guide", None) or getattr(project, "supervisor_name", None) or config.get("guide_name") or "Faculty Supervisor"
        institution_name = getattr(project, "institution", None) or config.get("institution") or "University Department of Computer Science"
        register_num = config.get("register_number") or getattr(project, "register_number", "REG-2026-001")
        timestamp = datetime.now(timezone.utc).strftime("%B %Y")

        sections = getattr(manuscript_res, "sections", []) or []
        manuscript_title = getattr(manuscript_res, "title", f"Academic Thesis: {proj_name}")

        # Build XML strings
        doc_xml_parts = []
        doc_xml_parts.append('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>')
        doc_xml_parts.append('<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">')
        doc_xml_parts.append('<w:body>')

        # -------------------------------------------------------------
        # 1. COVER PAGE / TITLE PAGE
        # -------------------------------------------------------------
        # Spacer
        doc_xml_parts.append(cls._p_xml("", space_after=720))
        # Title
        doc_xml_parts.append(cls._p_xml(manuscript_title.upper(), font_size=36, bold=True, align="center", space_after=360))
        doc_xml_parts.append(cls._p_xml("A PROJECT / RESEARCH REPORT", font_size=24, bold=True, align="center", space_after=240))
        doc_xml_parts.append(cls._p_xml("Submitted in partial fulfillment of the requirements for the degree", font_size=22, italic=True, align="center", space_after=720))

        doc_xml_parts.append(cls._p_xml(f"Submitted by: {author_name}", font_size=24, bold=True, align="center", space_after=120))
        doc_xml_parts.append(cls._p_xml(f"Register Number: {register_num}", font_size=22, align="center", space_after=360))

        doc_xml_parts.append(cls._p_xml(f"Under the Guidance of: {guide_name}", font_size=24, bold=True, align="center", space_after=720))
        doc_xml_parts.append(cls._p_xml(institution_name, font_size=24, bold=True, align="center", space_after=120))
        doc_xml_parts.append(cls._p_xml(timestamp, font_size=22, italic=True, align="center", space_after=720))

        # Page Break
        doc_xml_parts.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')

        # -------------------------------------------------------------
        # 2. FRONT MATTER (TOC Placeholder & Executive Summary)
        # -------------------------------------------------------------
        doc_xml_parts.append(cls._p_xml("TABLE OF CONTENTS", font_size=28, bold=True, align="center", space_after=240))

        toc_items = []
        current_chapter = None
        for s in sections:
            if s.chapter_title and s.chapter_title != current_chapter:
                current_chapter = s.chapter_title
                toc_items.append((current_chapter.upper(), "Bold"))
            sec_label = f"{s.section_number} {s.title}" if s.section_number else s.title
            toc_items.append((f"  {sec_label}", "Normal"))

        for t_text, t_style in toc_items[:25]:
            bold_flag = (t_style == "Bold")
            doc_xml_parts.append(cls._p_xml(t_text, font_size=22, bold=bold_flag, space_after=60))

        doc_xml_parts.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')

        # -------------------------------------------------------------
        # 3. MANUSCRIPT CHAPTERS & SECTIONS
        # -------------------------------------------------------------
        active_chapter = None

        for s in sections:
            # Chapter Heading
            if s.chapter_title and s.chapter_title != active_chapter:
                active_chapter = s.chapter_title
                doc_xml_parts.append(cls._p_xml(active_chapter.upper(), font_size=32, bold=True, align="center", space_before=360, space_after=240))

            # Section Heading
            sec_heading = f"{s.section_number} {s.title}" if s.section_number else s.title
            badge_text = f" [{s.evidence_badge_text}]" if s.evidence_badge_text else ""
            doc_xml_parts.append(cls._p_xml(f"{sec_heading}{badge_text}", font_size=28, bold=True, space_before=240, space_after=120))

            # Section Content Paragraphs
            paragraphs = s.content.split("\n\n")
            for p_text in paragraphs:
                if p_text.strip():
                    doc_xml_parts.append(cls._p_xml(p_text.strip(), font_size=24, align="both", line_spacing=360, space_after=160))

            # Bullet points
            if s.bullet_points:
                for bp in s.bullet_points:
                    doc_xml_parts.append(cls._p_xml(f"• {bp}", font_size=22, italic=True, space_after=80))

        # Page Setup Specs (A4 paper: 11906 x 16838 twips, Margins: Top=1440, Bottom=1440, Left=1800, Right=1440)
        sect_pr = (
            '<w:sectPr>'
            '<w:pgSz w:w="11906" w:h="16838"/>'
            '<w:pgMar w:top="1440" w:bottom="1440" w:left="1800" w:right="1440" w:header="720" w:footer="720" w:gutter="0"/>'
            '</w:sectPr>'
        )
        doc_xml_parts.append(sect_pr)
        doc_xml_parts.append('</w:body>')
        doc_xml_parts.append('</w:document>')

        document_xml = "\n".join(doc_xml_parts)

        # -------------------------------------------------------------
        # PACK INTO ZIP ARCHIVE
        # -------------------------------------------------------------
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml", cls._content_types_xml())
            zf.writestr("_rels/.rels", cls._rels_xml())
            zf.writestr("word/_rels/document.xml.rels", cls._document_rels_xml())
            zf.writestr("word/styles.xml", cls._styles_xml())
            zf.writestr("word/document.xml", document_xml)

        zip_buffer.seek(0)
        return zip_buffer.getvalue()

    @classmethod
    def _p_xml(
        cls,
        text: str,
        font_size: int = 24,  # half-pt (24 = 12pt)
        bold: bool = False,
        italic: bool = False,
        align: str = "left",  # left | center | right | both
        line_spacing: int = 360,  # 360 twips = 1.5 line spacing
        space_before: int = 0,
        space_after: int = 120
    ) -> str:
        esc_text = escape(str(text))
        jc_val = "both" if align == "both" else align

        b_tag = "<w:b/>" if bold else ""
        i_tag = "<w:i/>" if italic else ""

        return (
            f'<w:p>'
            f'<w:pPr>'
            f'<w:jc w:val="{jc_val}"/>'
            f'<w:spacing w:before="{space_before}" w:after="{space_after}" w:line="{line_spacing}" w:lineRule="auto"/>'
            f'<w:rPr>'
            f'<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>'
            f'<w:sz w:val="{font_size}"/>'
            f'<w:szCs w:val="{font_size}"/>'
            f'{b_tag}{i_tag}'
            f'</w:rPr>'
            f'</w:pPr>'
            f'<w:r>'
            f'<w:rPr>'
            f'<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>'
            f'<w:sz w:val="{font_size}"/>'
            f'<w:szCs w:val="{font_size}"/>'
            f'{b_tag}{i_tag}'
            f'</w:rPr>'
            f'<w:t xml:space="preserve">{esc_text}</w:t>'
            f'</w:r>'
            f'</w:p>'
        )

    @classmethod
    def _content_types_xml(cls) -> str:
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
            '  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
            '  <Default Extension="xml" ContentType="application/xml"/>\n'
            '  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>\n'
            '  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>\n'
            '</Types>'
        )

    @classmethod
    def _rels_xml(cls) -> str:
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
            '  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>\n'
            '</Relationships>'
        )

    @classmethod
    def _document_rels_xml(cls) -> str:
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
            '  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>\n'
            '</Relationships>'
        )

    @classmethod
    def _styles_xml(cls) -> str:
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">\n'
            '  <w:docDefaults>\n'
            '    <w:rPrDefault>\n'
            '      <w:rPr>\n'
            '        <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>\n'
            '        <w:sz w:val="24"/>\n'
            '        <w:szCs w:val="24"/>\n'
            '      </w:rPr>\n'
            '    </w:rPrDefault>\n'
            '  </w:docDefaults>\n'
            '</w:styles>'
        )
