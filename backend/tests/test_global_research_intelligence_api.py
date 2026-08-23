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


class TestGlobalResearchIntelligenceAPI(unittest.TestCase):

    # 1. Successful request
    @patch("app.api.intelligence_api.GlobalResearchIntelligenceService")
    def test_01_request_success(self, mock_service_cls):
        """Verify GET /api/research-intelligence returns HTTP 200 OK."""
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.analyze_collection.return_value = {
            "collection_summary": {
                "total_papers": 1, "total_graph_nodes": 2, "total_graph_edges": 1,
                "total_keywords": 0, "total_algorithms": 1, "total_datasets": 0,
                "total_methodologies": 0, "total_domains": 0, "total_potential_gaps": 0,
                "total_link_prediction_candidates": 0
            },
            "paper_landscape": [],
            "shared_concepts": {
                "keywords": [], "algorithms": [], "datasets": [], "methodologies": [], "domains": []
            },
            "paper_relationships": [],
            "research_gap_summary": {
                "total_gaps": 0, "high_confidence": 0, "moderate_confidence": 0, "low_confidence": 0
            },
            "gaps": [],
            "underrepresented_concepts": [],
            "candidate_research_directions": [],
            "collection_disclaimer": "All findings are derived from the currently indexed research-paper collection."
        }

        resp = client.get("/api/research-intelligence")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertIn("collection_summary", data)
        self.assertIn("collection_disclaimer", data)

    # 2. Parameter validation bounds
    def test_02_parameter_validation_bounds(self):
        """Verify query parameters out of bounds return validation error code."""
        resp1 = client.get("/api/research-intelligence?max_paper_relationships=0")
        self.assertIn(resp1.status_code, [400, 422])

        resp2 = client.get("/api/research-intelligence?max_gaps=500")
        self.assertIn(resp2.status_code, [400, 422])

    # 3. Empty database response
    @patch("app.api.intelligence_api.GlobalResearchIntelligenceService")
    def test_03_empty_database_response(self, mock_service_cls):
        """Verify empty database returns HTTP 200 OK with zero metrics."""
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.analyze_collection.return_value = {
            "collection_summary": {
                "total_papers": 0, "total_graph_nodes": 0, "total_graph_edges": 0,
                "total_keywords": 0, "total_algorithms": 0, "total_datasets": 0,
                "total_methodologies": 0, "total_domains": 0, "total_potential_gaps": 0,
                "total_link_prediction_candidates": 0
            },
            "paper_landscape": [],
            "shared_concepts": {
                "keywords": [], "algorithms": [], "datasets": [], "methodologies": [], "domains": []
            },
            "paper_relationships": [],
            "research_gap_summary": {
                "total_gaps": 0, "high_confidence": 0, "moderate_confidence": 0, "low_confidence": 0
            },
            "gaps": [],
            "underrepresented_concepts": [],
            "candidate_research_directions": [],
            "collection_disclaimer": "All findings are derived from the currently indexed research-paper collection."
        }

        resp = client.get("/api/research-intelligence")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["collection_summary"]["total_papers"], 0)

    # 4. Schema validation
    @patch("app.api.intelligence_api.GlobalResearchIntelligenceService")
    def test_04_schema_validation(self, mock_service_cls):
        """Verify all top-level response schema keys are present."""
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.analyze_collection.return_value = {
            "collection_summary": {
                "total_papers": 0, "total_graph_nodes": 0, "total_graph_edges": 0,
                "total_keywords": 0, "total_algorithms": 0, "total_datasets": 0,
                "total_methodologies": 0, "total_domains": 0, "total_potential_gaps": 0,
                "total_link_prediction_candidates": 0
            },
            "paper_landscape": [],
            "shared_concepts": {
                "keywords": [], "algorithms": [], "datasets": [], "methodologies": [], "domains": []
            },
            "paper_relationships": [],
            "research_gap_summary": {
                "total_gaps": 0, "high_confidence": 0, "moderate_confidence": 0, "low_confidence": 0
            },
            "gaps": [],
            "underrepresented_concepts": [],
            "candidate_research_directions": [],
            "collection_disclaimer": "All findings are derived from the currently indexed research-paper collection."
        }

        resp = client.get("/api/research-intelligence")
        data = resp.json()

        for k in [
            "collection_summary", "paper_landscape", "shared_concepts",
            "paper_relationships", "research_gap_summary", "gaps",
            "underrepresented_concepts", "candidate_research_directions", "collection_disclaimer"
        ]:
            self.assertIn(k, data)

    # 5. Disclaimer notice
    @patch("app.api.intelligence_api.GlobalResearchIntelligenceService")
    def test_05_disclaimer_notice(self, mock_service_cls):
        """Verify collection disclaimer is included in API response."""
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.analyze_collection.return_value = {
            "collection_summary": {
                "total_papers": 0, "total_graph_nodes": 0, "total_graph_edges": 0,
                "total_keywords": 0, "total_algorithms": 0, "total_datasets": 0,
                "total_methodologies": 0, "total_domains": 0, "total_potential_gaps": 0,
                "total_link_prediction_candidates": 0
            },
            "paper_landscape": [],
            "shared_concepts": {
                "keywords": [], "algorithms": [], "datasets": [], "methodologies": [], "domains": []
            },
            "paper_relationships": [],
            "research_gap_summary": {
                "total_gaps": 0, "high_confidence": 0, "moderate_confidence": 0, "low_confidence": 0
            },
            "gaps": [],
            "underrepresented_concepts": [],
            "candidate_research_directions": [],
            "collection_disclaimer": "All findings are derived from the currently indexed research-paper collection."
        }

        resp = client.get("/api/research-intelligence")
        self.assertIn("collection_disclaimer", resp.json())

    # 6. Error handling
    @patch("app.api.intelligence_api.GlobalResearchIntelligenceService")
    def test_06_error_handling(self, mock_service_cls):
        """Verify server exception returns HTTP 500 Internal Server Error."""
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.analyze_collection.side_effect = Exception("Fatal intelligence analysis crash")

        resp = client.get("/api/research-intelligence")
        self.assertEqual(resp.status_code, 500)
        self.assertIn("detail", resp.json())


if __name__ == "__main__":
    unittest.main()
