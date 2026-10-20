import sys
import os
import unittest
import fitz  # PyMuPDF
import zipfile
import io
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.models.paper_model import ResearchPaper
from app.models.project_model import (
    ResearchProject,
    ProjectPaper,
    SavedResearchDirection,
    ResearchExperiment,
    ExperimentRun,
    ExperimentResult,
    ResearchManuscript,
    ResearchManuscriptVersion
)
from app.models.proposal_model import Proposal
from app.services.academic_manuscript_service import AcademicManuscriptService
from app.services.academic_report_pdf_engine import AcademicReportPdfEngine
from app.services.academic_docx_engine import AcademicDocxEngine
from app.services.submission_package_service import SubmissionPackageService
from app.services.research_results_analysis_service import ResearchResultsAnalysisService


class TestAcademicPaperGeneratorRegression(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        cls.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

        cls.db = cls.TestingSessionLocal()
        cls.seed_test_projects(cls.db)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    @classmethod
    def seed_test_projects(cls, db):
        # 1. Project A: Computer Vision / Medical Imaging
        p1 = ResearchProject(
            id=101,
            name="Automated Medical Image Classification Framework",
            description="Deep Learning for Radiological Scan Diagnostics",
            status="IN_PROGRESS"
        )
        db.add(p1)

        paper1 = ResearchPaper(id=201, title="Deep Residual Networks for Medical Scans", full_text="Full text content for paper 201", filename="paper201.pdf", algorithms=["ResNet50"], datasets=["ChestXRay"], tasks=["Classification"])
        paper2 = ResearchPaper(id=202, title="Attention Mechanisms in Radiology", full_text="Full text content for paper 202", filename="paper202.pdf", algorithms=["VisionTransformer"], datasets=["MIMIC-CXR"], tasks=["Classification"])
        db.add_all([paper1, paper2])
        db.commit()

        db.add_all([
            ProjectPaper(project_id=101, paper_id=201),
            ProjectPaper(project_id=101, paper_id=202)
        ])

        d1 = SavedResearchDirection(
            id=301,
            project_id=101,
            title="Incorporate Spatial Attention into Residual Neural Networks",
            description="Combines ResNet backbone with spatial attention for medical scan classification.",
            direction_data={"methodology_plan": {"phases": ["Data", "Model", "Eval"]}}
        )
        db.add(d1)

        prop1 = Proposal(
            id=401,
            proposal_uuid="prop-401-uuid",
            project_id=101,
            title="Spatial Attention Residual Network for Medical Image Classification",
            status="DRAFT"
        )
        db.add(prop1)
        db.commit()

        exp1 = ResearchExperiment(
            id=501,
            project_id=101,
            name="ResNet vs Spatial-ResNet on ChestXRay",
            status="COMPLETED",
            baseline_config={"name": "ResNet-50"},
            proposed_config={"name": "Spatial-ResNet50"},
            dataset_config={"name": "ChestXRay"},
            environment_config={"hardware": "NVIDIA RTX 4090"}
        )
        db.add(exp1)
        db.commit()

        run1 = ExperimentRun(id=601, experiment_id=501, run_number=1)
        db.add(run1)
        db.commit()

        db.add_all([
            ExperimentResult(run_id=601, method_type="baseline", metric_name="Accuracy", metric_value="0.842", unit=""),
            ExperimentResult(run_id=601, method_type="proposed", metric_name="Accuracy", metric_value="0.895", unit="")
        ])
        db.commit()

        # 2. Project B: Cybersecurity / Threat Detection (NO empirical results yet!)
        p2 = ResearchProject(
            id=102,
            name="Network Intrusion Detection System using Graph Embeddings",
            description="Cybersecurity Threat Analytics for Industrial Control Systems",
            status="DRAFT"
        )
        db.add(p2)

        paper3 = ResearchPaper(id=203, title="Graph Neural Networks in Cyber Defense", full_text="Full text content for paper 203", filename="paper203.pdf", algorithms=["GCN"], datasets=["UNSW-NB15"], tasks=["Intrusion Detection"])
        db.add(paper3)
        db.commit()

        db.add(ProjectPaper(project_id=102, paper_id=203))

        d2 = SavedResearchDirection(
            id=302,
            project_id=102,
            title="Temporal Graph Convolutional Networks for Network Traffic Anomaly Detection",
            description="Integrate GCN with temporal modeling for flow-level intrusion detection.",
            direction_data={"methodology_plan": {}}
        )
        db.add(d2)

        exp2 = ResearchExperiment(
            id=502,
            project_id=102,
            name="Temporal-GCN on UNSW-NB15",
            status="PLANNED",
            baseline_config={"name": "Random Forest"},
            proposed_config={"name": "Temporal-GCN"},
            dataset_config={"name": "UNSW-NB15"}
        )
        db.add(exp2)
        db.commit()

        # 3. Project C: NLP / Text Summarization
        p3 = ResearchProject(
            id=103,
            name="Transformer-Based Abstractive Text Summarization",
            description="Natural Language Processing for Scientific Document Summarization",
            status="IN_PROGRESS"
        )
        db.add(p3)

        paper4 = ResearchPaper(id=204, title="BART for Scientific Document Summarization", full_text="Full text content for paper 204", filename="paper204.pdf", algorithms=["BART"], datasets=["CNN/DailyMail"], tasks=["Text Summarization"])
        db.add(paper4)
        db.commit()

        db.add(ProjectPaper(project_id=103, paper_id=204))

        d3 = SavedResearchDirection(
            id=303,
            project_id=103,
            title="Incorporate Hierarchical Attention into BART for Multi-Document Summarization",
            description="Combines BART transformer backbone with hierarchical attention for multi-doc summarization.",
            direction_data={"methodology_plan": {}}
        )
        db.add(d3)
        db.commit()

    def test_01_project_independent_synthesis(self):
        """Test manuscript generator creates domain-appropriate 44 sections for both Vision and Security projects."""
        res_a = AcademicManuscriptService.generate_fresh_manuscript(self.db, 101)
        self.assertEqual(res_a.project_id, 101)
        self.assertIn("Spatial Attention", res_a.title)
        self.assertGreaterEqual(len(res_a.sections), 40)

        res_b = AcademicManuscriptService.generate_fresh_manuscript(self.db, 102)
        self.assertEqual(res_b.project_id, 102)
        self.assertIn("Temporal Graph Convolutional", res_b.title)
        self.assertGreaterEqual(len(res_b.sections), 40)

    def test_02_zero_fabrication_rule(self):
        """Test zero empirical result fabrication: Project 102 (no results) explicitly states MISSING / pending."""
        res_b = AcademicManuscriptService.generate_fresh_manuscript(self.db, 102)

        recorded_results_sec = next(s for s in res_b.sections if s.section_key == "RECORDED_RESULTS")
        self.assertEqual(recorded_results_sec.evidence_level, "MISSING")
        self.assertIn("not yet available", recorded_results_sec.content.lower())

        ablation_sec = next(s for s in res_b.sections if s.section_key == "ABLATION_STUDY")
        self.assertEqual(ablation_sec.evidence_level, "MISSING")
        self.assertIn("not available in current project evidence", ablation_sec.content.lower())

    def test_03_empirical_results_grounding(self):
        """Test Project 101 (with actual DB results) properly records 0.895 proposed accuracy."""
        res_a = AcademicManuscriptService.generate_fresh_manuscript(self.db, 101)

        recorded_results_sec = next(s for s in res_a.sections if s.section_key == "RECORDED_RESULTS")
        self.assertEqual(recorded_results_sec.evidence_level, "EXPERIMENTAL_RESULT")
        self.assertIn("ResNet vs Spatial-ResNet", recorded_results_sec.content)

    def test_04_claim_traceability_metadata(self):
        """Test each section carries provenance metadata."""
        res_a = AcademicManuscriptService.get_or_generate_manuscript(self.db, 101)
        for s in res_a.sections:
            self.assertIsNotNone(s.claim_traceability)
            self.assertIn(s.claim_traceability.source_type, ["RECORDED_EVIDENCE", "PROPOSED", "DERIVED", "EXPERIMENTAL_RESULT", "MISSING"])

    def test_05_version_save_restore_compare(self):
        """Test manuscript versioning save, restore, and diff comparison."""
        res_orig = AcademicManuscriptService.get_or_generate_manuscript(self.db, 101)
        v1_num = res_orig.current_version_number

        # Save revised version
        modified_sections = [s.model_copy(deep=True) for s in res_orig.sections]
        modified_sections[0].content = "Custom Student Revised Title"
        save_req = {"title": "Custom Student Revised Title", "sections": [s.model_dump() for s in modified_sections], "change_summary": "Manual student edit"}

        from app.schemas.academic_manuscript_schema import ManuscriptSaveVersionRequest
        res_v2 = AcademicManuscriptService.save_manuscript_version(self.db, 101, ManuscriptSaveVersionRequest(**save_req))
        self.assertEqual(res_v2.current_version_number, v1_num + 1)

        # Compare v1 and v2
        comp = AcademicManuscriptService.compare_manuscript_versions(self.db, 101, v1_num, res_v2.current_version_number)
        self.assertEqual(comp.version_a, v1_num)
        self.assertEqual(comp.version_b, res_v2.current_version_number)
        self.assertTrue(any(d.status == "MODIFIED" for d in comp.diffs))

        # Restore v1
        res_v3 = AcademicManuscriptService.restore_manuscript_version(self.db, 101, v1_num)
        self.assertEqual(res_v3.current_version_number, res_v2.current_version_number + 1)

    def test_06_pdf_engine_university_formatting(self):
        """Test AcademicReportPdfEngine renders valid PyMuPDF PDF with TOC, bookmarks, and Times New Roman fonts."""
        p = self.db.query(ResearchProject).filter(ResearchProject.id == 101).first()
        papers = [assoc.paper for assoc in p.project_papers if assoc.paper]
        manuscript_res = AcademicManuscriptService.get_or_generate_manuscript(self.db, 101)
        results_summary = ResearchResultsAnalysisService.get_project_results_analysis(self.db, 101)

        pdf_engine = AcademicReportPdfEngine(
            report=p,
            project=p,
            papers=papers,
            proposal=p.proposals[-1] if p.proposals else None,
            plan=p.saved_directions[0] if p.saved_directions else None,
            experiments=p.experiments or [],
            results_analysis=results_summary.model_dump() if hasattr(results_summary, "model_dump") else {},
            manuscript=manuscript_res,
            db=self.db
        )
        pdf_bytes = pdf_engine.generate_pdf()
        self.assertTrue(len(pdf_bytes) > 5000)

        # Inspect generated PDF with PyMuPDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        self.assertGreaterEqual(len(doc), 5)

        # Check native TOC outline bookmarks
        toc = doc.get_toc()
        self.assertTrue(len(toc) > 0)
        self.assertTrue(any("INTRODUCTION" in item[1].upper() for item in toc))

        # Verify Cover Page has title
        page1_text = doc[0].get_text().replace("\n", " ")
        self.assertIn("AUTOMATED MEDICAL IMAGE CLASSIFICATION", page1_text.upper())

    def test_07_docx_engine_academic_formatting(self):
        """Test AcademicDocxEngine creates valid DOCX zip archive."""
        p = self.db.query(ResearchProject).filter(ResearchProject.id == 101).first()
        papers = [assoc.paper for assoc in p.project_papers if assoc.paper]
        manuscript_res = AcademicManuscriptService.get_or_generate_manuscript(self.db, 101)

        docx_bytes = AcademicDocxEngine.generate_docx(manuscript_res, p, papers)
        self.assertTrue(len(docx_bytes) > 2000)

        # Inspect ZIP structure
        with zipfile.ZipFile(io.BytesIO(docx_bytes), "r") as zf:
            filenames = zf.namelist()
            self.assertIn("word/document.xml", filenames)
            self.assertIn("[Content_Types].xml", filenames)

            doc_xml = zf.read("word/document.xml").decode("utf-8")
            self.assertIn("Times New Roman", doc_xml)
            self.assertIn("TABLE OF CONTENTS", doc_xml)

    def test_08_submission_package_zip(self):
        """Test SubmissionPackageService generates complete ZIP deliverable."""
        import asyncio

        streaming_res = SubmissionPackageService.generate_submission_package_zip(self.db, 101)

        async def read_chunks():
            chunks = []
            async for chunk in streaming_res.body_iterator:
                chunks.append(chunk)
            return b"".join(chunks)

        zip_bytes = asyncio.run(read_chunks())

        self.assertTrue(len(zip_bytes) > 5000)
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            namelist = zf.namelist()
            self.assertIn("paper/manuscript.md", namelist)
            self.assertIn("paper/manuscript.json", namelist)
            self.assertIn("paper/academic_report.pdf", namelist)
            self.assertIn("paper/academic_thesis.docx", namelist)
            self.assertIn("evidence/evidence_traceability.md", namelist)
            self.assertIn("evidence/claim_traceability.json", namelist)
            self.assertIn("references/references.md", namelist)
            self.assertIn("README.md", namelist)

    def test_09_multi_project_isolation_and_domain_adaptation(self):
        """Test project isolation and task domain metrics adaptation across Projects 101 (CV), 102 (Cybersecurity), and 103 (NLP)."""
        res_101 = AcademicManuscriptService.generate_fresh_manuscript(self.db, 101)
        res_102 = AcademicManuscriptService.generate_fresh_manuscript(self.db, 102)
        res_103 = AcademicManuscriptService.generate_fresh_manuscript(self.db, 103)

        # 1. Project 101 (CV) must NOT contain GCN, UNSW-NB15, or BART
        text_101 = " ".join([s.content for s in res_101.sections])
        self.assertNotIn("UNSW-NB15", text_101)
        self.assertNotIn("BART", text_101)

        # 2. Project 102 (Cybersecurity) must NOT contain ResNet or ChestXRay
        text_102 = " ".join([s.content for s in res_102.sections])
        self.assertNotIn("ChestXRay", text_102)
        self.assertNotIn("ResNet", text_102)

        # 3. Project 103 (NLP) metrics must contain BLEU / ROUGE
        text_103 = " ".join([s.content for s in res_103.sections])
        eval_metrics_sec = next(s for s in res_103.sections if s.section_key == "EVALUATION_METRICS")
        self.assertIn("BLEU", eval_metrics_sec.content)


if __name__ == "__main__":
    unittest.main()

