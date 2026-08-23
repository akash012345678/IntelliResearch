import sys
import json
import unittest
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.schemas.research_direction_schema import (

    ResearchDirectionResponse,
    ResearchDirection,
    ResearchDirectionEvidence,
    SupportingPaper,
    CandidateAlgorithm,
    CandidateDataset,
    CandidateMethodology
)
from app.services.proposal_export_service import ProposalExportService, EXPORT_DISCLAIMER


class TestProposalExportService(unittest.TestCase):
    """
    Unit tests for ProposalExportService (Markdown, JSON, PDF formats).
    """

    def setUp(self):
        self.sample_evidence = ResearchDirectionEvidence(
            gap_score=0.82,
            semantic_evidence=0.75,
            link_prediction_score=0.90,
            collection_coverage=37.5,
            underrepresentation_score=0.60
        )

        self.sample_direction = ResearchDirection(
            direction_id="dir_1",
            title="Explore YOLOv8 + Vision Transformer for Autonomous Driving",
            research_problem="Current papers investigate Autonomous Driving using YOLOv8, while integration with Vision Transformer remains underrepresented.",
            motivation="The collection contains 3 papers referencing related concepts with a gap score of 0.82.",
            existing_evidence=["High link prediction score.", "Strong cross-paper coverage."],
            missing_aspect="Integration of Vision Transformer with baseline methodology is underrepresented.",
            proposed_direction="Investigate whether combining YOLOv8 with Vision Transformer could explore potential methodology enhancements.",
            supporting_papers=[
                SupportingPaper(
                    paper_id=45,
                    title="Driver Drowsiness Detection Framework",
                    role="Provides primary domain context (Autonomous Driving) and baseline concepts."
                )
            ],
            supporting_concepts=["Autonomous Driving", "YOLOv8", "Vision Transformer"],
            candidate_algorithms=[
                CandidateAlgorithm(name="YOLOv8", supporting_paper_count=1, reason="Baseline algorithm.")
            ],
            candidate_datasets=[
                CandidateDataset(name="COCO", supporting_paper_count=1, reason="Benchmark dataset.")
            ],
            candidate_methodologies=[
                CandidateMethodology(name="Deep Learning", paper_count=1, coverage_percentage=12.5)
            ],
            evidence=self.sample_evidence,
            direction_score=0.77,
            confidence="High",
            disclaimer=EXPORT_DISCLAIMER
        )

        self.sample_response = ResearchDirectionResponse(
            total_directions=1,
            directions=[self.sample_direction],
            collection_disclaimer="Global collection disclaimer message."
        )

    def test_01_filename_generation(self):
        """Verify filenames for md, markdown, json, pdf formats."""
        self.assertEqual(ProposalExportService.get_export_filename("md"), "intelliresearch_research_directions.md")
        self.assertEqual(ProposalExportService.get_export_filename("markdown"), "intelliresearch_research_directions.md")
        self.assertEqual(ProposalExportService.get_export_filename("json"), "intelliresearch_research_directions.json")
        self.assertEqual(ProposalExportService.get_export_filename("pdf"), "intelliresearch_research_directions.pdf")

    def test_02_export_to_markdown(self):
        """Verify Markdown export content and headers."""
        md_text = ProposalExportService.export_to_markdown(self.sample_response)
        self.assertIn("# IntelliResearch — Actionable Research Directions Report", md_text)
        self.assertIn("Explore YOLOv8 + Vision Transformer for Autonomous Driving", md_text)
        self.assertIn("### Research Problem", md_text)
        self.assertIn("### Proposed Direction", md_text)
        self.assertIn("### Evidence Metrics", md_text)
        self.assertIn("Gap Score", md_text)
        self.assertIn("`0.82`", md_text)
        self.assertIn("Driver Drowsiness Detection Framework", md_text)
        self.assertIn("`YOLOv8`", md_text)
        self.assertIn("`COCO`", md_text)
        self.assertIn(EXPORT_DISCLAIMER, md_text)

    def test_03_export_to_json(self):
        """Verify JSON export content and structure."""
        json_str = ProposalExportService.export_to_json(self.sample_response)
        data = json.loads(json_str)

        self.assertEqual(data["schema_version"], "1.0")
        self.assertIn("export_timestamp", data)
        self.assertEqual(data["total_directions"], 1)
        self.assertEqual(len(data["directions"]), 1)

        d0 = data["directions"][0]
        self.assertEqual(d0["direction_id"], "dir_1")
        self.assertEqual(d0["direction_score"], 0.77)
        self.assertEqual(d0["confidence"], "High")
        self.assertEqual(d0["evidence"]["gap_score"], 0.82)
        self.assertEqual(d0["supporting_papers"][0]["paper_id"], 45)

    def test_04_export_to_pdf(self):
        """Verify PDF export generates valid non-empty PDF bytes starting with %PDF."""
        pdf_bytes = ProposalExportService.export_to_pdf(self.sample_response)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(len(pdf_bytes) > 0)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_05_empty_directions_export(self):
        """Verify empty directions response exports cleanly across all formats."""
        empty_resp = ResearchDirectionResponse(
            total_directions=0,
            directions=[],
            collection_disclaimer="Empty collection disclaimer."
        )

        md_out = ProposalExportService.export_to_markdown(empty_resp)
        self.assertIn("No Actionable Research Directions Found", md_out)

        json_out = ProposalExportService.export_to_json(empty_resp)
        json_data = json.loads(json_out)
        self.assertEqual(json_data["total_directions"], 0)

        pdf_out = ProposalExportService.export_to_pdf(empty_resp)
        self.assertTrue(pdf_out.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
