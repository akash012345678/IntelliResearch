import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app
from app.schemas.research_direction_schema import ResearchDirectionResponse
from app.schemas.proposal_draft_schema import ProposalDraftResponse, ProposalDraft

client = TestClient(app)


class TestResearchDirectionAPI(unittest.TestCase):
    """
    Integration tests for GET /api/research-directions, GET /api/research-directions/export,
    and POST /api/research-directions/draft endpoints.
    """

    @patch("app.api.research_direction_api.ResearchDirectionService")
    def test_01_get_research_directions_default(self, mock_service):
        """
        Test GET /api/research-directions returns 200 OK and valid schema.
        """
        mock_service.generate_directions.return_value = ResearchDirectionResponse(
            total_directions=0,
            directions=[],
            collection_disclaimer="Disclaimer text"
        )

        response = client.get("/api/research-directions")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("total_directions", data)
        self.assertIn("directions", data)
        self.assertIn("collection_disclaimer", data)
        self.assertIsInstance(data["directions"], list)

    @patch("app.api.research_direction_api.ResearchDirectionService")
    def test_02_get_research_directions_top_k_param(self, mock_service):
        """
        Test GET /api/research-directions?top_k=5 handles top_k parameter correctly.
        """
        mock_service.generate_directions.return_value = ResearchDirectionResponse(
            total_directions=0,
            directions=[],
            collection_disclaimer="Disclaimer text"
        )

        response = client.get("/api/research-directions?top_k=5")
        self.assertEqual(response.status_code, 200)

    def test_03_get_research_directions_invalid_top_k(self):
        """
        Test top_k validation returns 422 Unprocessable Entity when top_k > 20 or top_k < 1.
        """
        resp_too_large = client.get("/api/research-directions?top_k=50")
        self.assertEqual(resp_too_large.status_code, 422)

        resp_too_small = client.get("/api/research-directions?top_k=0")
        self.assertEqual(resp_too_small.status_code, 422)

    @patch("app.api.research_direction_api.ResearchDirectionService")
    def test_04_export_markdown(self, mock_service):
        """Test GET /api/research-directions/export?format=md returns Markdown content."""
        mock_service.generate_directions.return_value = ResearchDirectionResponse(
            total_directions=0,
            directions=[],
            collection_disclaimer="Disclaimer text"
        )

        response = client.get("/api/research-directions/export?format=md&top_k=10")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/markdown", response.headers["content-type"])
        self.assertIn('attachment; filename="intelliresearch_research_directions.md"', response.headers["content-disposition"])
        self.assertIn("IntelliResearch — Actionable Research Directions Report", response.text)

    @patch("app.api.research_direction_api.ResearchDirectionService")
    def test_05_export_json(self, mock_service):
        """Test GET /api/research-directions/export?format=json returns JSON content."""
        mock_service.generate_directions.return_value = ResearchDirectionResponse(
            total_directions=0,
            directions=[],
            collection_disclaimer="Disclaimer text"
        )

        response = client.get("/api/research-directions/export?format=json&top_k=5")
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/json", response.headers["content-type"])
        self.assertIn('attachment; filename="intelliresearch_research_directions.json"', response.headers["content-disposition"])
        data = response.json()
        self.assertIn("schema_version", data)

    @patch("app.api.research_direction_api.ResearchDirectionService")
    def test_06_export_pdf(self, mock_service):
        """Test GET /api/research-directions/export?format=pdf returns PDF content."""
        mock_service.generate_directions.return_value = ResearchDirectionResponse(
            total_directions=0,
            directions=[],
            collection_disclaimer="Disclaimer text"
        )

        response = client.get("/api/research-directions/export?format=pdf&top_k=10")
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/pdf", response.headers["content-type"])
        self.assertIn('attachment; filename="intelliresearch_research_directions.pdf"', response.headers["content-disposition"])
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_07_export_invalid_format(self):
        """Test GET /api/research-directions/export with invalid format returns 400 Bad Request."""
        response = client.get("/api/research-directions/export?format=invalid_fmt")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Unsupported export format", response.json()["detail"])

    @patch("app.api.research_direction_api.ProposalDraftService")
    def test_08_post_proposal_draft_success(self, mock_draft_service):
        """Test POST /api/research-directions/draft returns 200 OK and ProposalDraftResponse."""
        sample_draft = ProposalDraft(
            proposal_id="prop_123",
            source_direction_id="dir_1",
            title="Sample Title",
            abstract="Sample Abstract",
            problem_statement="Sample Problem",
            research_motivation="Sample Motivation",
            related_work_synthesis="Sample Related Work",
            research_gap="Sample Gap",
            proposed_methodology="Sample Methodology",
            candidate_algorithms=["YOLOv8"],
            candidate_datasets=["COCO"],
            dataset_evaluation_plan="Sample Dataset Plan",
            experimental_plan="Sample Exp Plan",
            evaluation_metrics="Accuracy",
            expected_contribution="Sample Contribution",
            limitations="Sample Limitations",
            supporting_papers=[],
            evidence_summary={},
            generation_mode="template",
            generation_timestamp="2026-08-23T00:00:00Z",
            disclaimer="Disclaimer notice"
        )
        mock_draft_service.synthesize_draft.return_value = ProposalDraftResponse(proposal=sample_draft)

        response = client.post("/api/research-directions/draft", json={"direction_id": "dir_1"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("proposal", data)
        self.assertEqual(data["proposal"]["proposal_id"], "prop_123")
        self.assertEqual(data["proposal"]["generation_mode"], "template")


if __name__ == "__main__":
    unittest.main()
