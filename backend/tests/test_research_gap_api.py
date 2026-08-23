import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app

client = TestClient(app)


class TestResearchGapAPI(unittest.TestCase):

    # 1. Successful request
    @patch("app.api.research_gap_api.ResearchGapService")
    def test_01_request_success(self, mock_service_cls):
        """Verify GET /api/research-gaps returns HTTP 200 OK."""
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.detect_gaps.return_value = [
            {
                "source_paper_id": 26,
                "source_paper_title": "Paper 26 Title",
                "target_node_id": "algorithm_lstm",
                "target_type": "ALGORITHM",
                "target_label": "LSTM",
                "relationship_type": "USES_ALGORITHM",
                "gap_score": 0.78,
                "confidence": "High",
                "evidence": {
                    "link_prediction_score": 0.7676,
                    "cross_paper_support": 0.72,
                    "semantic_evidence": 0.81,
                    "underrepresentation_score": 0.63
                },
                "explanation": ["The predicted relationship has strong graph-based support."]
            }
        ]

        resp = client.get("/api/research-gaps?top_k=10")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data["total_candidates"], 1)
        self.assertIn("collection_disclaimer", data)
        self.assertEqual(len(data["gaps"]), 1)

    # 2. top_k parameter validation
    def test_02_top_k_validation(self):
        """Verify top_k <= 0 or top_k > 50 returns validation error status code."""
        resp1 = client.get("/api/research-gaps?top_k=0")
        self.assertIn(resp1.status_code, [400, 422])

        resp2 = client.get("/api/research-gaps?top_k=100")
        self.assertIn(resp2.status_code, [400, 422])

    # 3. Empty results
    @patch("app.api.research_gap_api.ResearchGapService")
    def test_03_empty_results(self, mock_service_cls):
        """Verify empty research gap results returns gaps: []."""
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.detect_gaps.return_value = []

        resp = client.get("/api/research-gaps")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data["total_candidates"], 0)
        self.assertEqual(data["gaps"], [])

    # 4. Response schema
    @patch("app.api.research_gap_api.ResearchGapService")
    def test_04_response_schema(self, mock_service_cls):
        """Verify gap object schema keys."""
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.detect_gaps.return_value = [
            {
                "source_paper_id": 5,
                "source_paper_title": "P5",
                "target_node_id": "dataset_coco",
                "target_type": "DATASET",
                "target_label": "COCO",
                "relationship_type": "USES_DATASET",
                "gap_score": 0.65,
                "confidence": "Moderate",
                "evidence": {
                    "link_prediction_score": 0.5,
                    "cross_paper_support": 0.4,
                    "semantic_evidence": 0.7,
                    "underrepresentation_score": 0.8
                },
                "explanation": ["Explanation 1"]
            }
        ]

        resp = client.get("/api/research-gaps")
        gap = resp.json()["gaps"][0]

        self.assertIn("source_paper_id", gap)
        self.assertIn("source_paper_title", gap)
        self.assertIn("target_node_id", gap)
        self.assertIn("target_type", gap)
        self.assertIn("target_label", gap)
        self.assertIn("relationship_type", gap)
        self.assertIn("gap_score", gap)
        self.assertIn("confidence", gap)
        self.assertIn("evidence", gap)
        self.assertIn("explanation", gap)

    # 5. Disclaimer notice
    @patch("app.api.research_gap_api.ResearchGapService")
    def test_05_disclaimer_notice(self, mock_service_cls):
        """Verify response contains collection disclaimer message."""
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.detect_gaps.return_value = []

        resp = client.get("/api/research-gaps")
        data = resp.json()

        self.assertIn("collection_disclaimer", data)
        self.assertIn("indexed research-paper collection", data["collection_disclaimer"])

    # 6. Error handling
    @patch("app.api.research_gap_api.ResearchGapService")
    def test_06_error_handling(self, mock_service_cls):
        """Verify server exception returns HTTP 500 Internal Server Error."""
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.detect_gaps.side_effect = Exception("Fatal research gap crash")

        resp = client.get("/api/research-gaps")
        self.assertEqual(resp.status_code, 500)
        self.assertIn("detail", resp.json())


if __name__ == "__main__":
    unittest.main()
