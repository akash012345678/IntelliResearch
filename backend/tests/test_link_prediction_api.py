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


class TestLinkPredictionAPI(unittest.TestCase):

    # 1. Successful prediction request
    @patch("app.api.knowledge_graph_api.LinkPredictionService")
    @patch("app.api.knowledge_graph_api.KnowledgeGraphBuilder")
    def test_01_prediction_request_success(self, mock_builder_cls, mock_service_cls):
        """Verify GET /api/knowledge-graph/link-predictions returns HTTP 200 OK."""
        mock_builder = MagicMock()
        mock_builder_cls.return_value = mock_builder
        mock_builder.build_from_database.return_value = {}

        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.predict_links.return_value = [
            {
                "source_paper_id": 101,
                "target_node_id": "algorithm_yolov8",
                "target_type": "ALGORITHM",
                "target_label": "YOLOv8",
                "relationship_type": "USES_ALGORITHM",
                "existing_relationship": False,
                "scores": {
                    "jaccard": 0.42,
                    "adamic_adar": 1.18,
                    "resource_allocation": 0.50,
                    "combined": 0.67
                }
            }
        ]

        resp = client.get("/api/knowledge-graph/link-predictions?top_k=10")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data["total_candidates"], 1)
        self.assertEqual(len(data["predictions"]), 1)

    # 2. top_k parameter validation
    def test_02_top_k_parameter_validation(self):
        """Verify top_k <= 0 or top_k > 50 returns validation error status code."""
        resp1 = client.get("/api/knowledge-graph/link-predictions?top_k=0")
        self.assertIn(resp1.status_code, [400, 422])

        resp2 = client.get("/api/knowledge-graph/link-predictions?top_k=100")
        self.assertIn(resp2.status_code, [400, 422])

    # 3. Empty graph
    @patch("app.api.knowledge_graph_api.LinkPredictionService")
    @patch("app.api.knowledge_graph_api.KnowledgeGraphBuilder")
    def test_03_empty_graph(self, mock_builder_cls, mock_service_cls):
        """Verify empty graph returns total_candidates: 0 and predictions: []."""
        mock_builder = MagicMock()
        mock_builder_cls.return_value = mock_builder
        mock_builder.build_from_database.return_value = {"total_papers": 0}

        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.predict_links.return_value = []

        resp = client.get("/api/knowledge-graph/link-predictions")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data["total_candidates"], 0)
        self.assertEqual(data["predictions"], [])

    # 4. No candidates
    @patch("app.api.knowledge_graph_api.LinkPredictionService")
    @patch("app.api.knowledge_graph_api.KnowledgeGraphBuilder")
    def test_04_no_candidates(self, mock_builder_cls, mock_service_cls):
        """Verify graph with no candidate relationships returns empty list cleanly."""
        mock_builder = MagicMock()
        mock_builder_cls.return_value = mock_builder
        mock_builder.build_from_database.return_value = {}

        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.predict_links.return_value = []

        resp = client.get("/api/knowledge-graph/link-predictions")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["predictions"], [])

    # 5. Response schema validation
    @patch("app.api.knowledge_graph_api.LinkPredictionService")
    @patch("app.api.knowledge_graph_api.KnowledgeGraphBuilder")
    def test_05_response_schema(self, mock_builder_cls, mock_service_cls):
        """Verify prediction item matches expected JSON schema."""
        mock_builder = MagicMock()
        mock_builder_cls.return_value = mock_builder
        mock_builder.build_from_database.return_value = {}

        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.predict_links.return_value = [
            {
                "source_paper_id": 5,
                "target_node_id": "dataset_coco",
                "target_type": "DATASET",
                "target_label": "COCO",
                "relationship_type": "USES_DATASET",
                "existing_relationship": False,
                "scores": {
                    "jaccard": 0.5,
                    "adamic_adar": 0.8,
                    "resource_allocation": 0.4,
                    "combined": 0.58
                }
            }
        ]

        resp = client.get("/api/knowledge-graph/link-predictions")
        pred = resp.json()["predictions"][0]

        self.assertIn("source_paper_id", pred)
        self.assertIn("target_node_id", pred)
        self.assertIn("target_type", pred)
        self.assertIn("target_label", pred)
        self.assertIn("relationship_type", pred)
        self.assertIn("existing_relationship", pred)
        self.assertIn("scores", pred)
        self.assertIn("jaccard", pred["scores"])
        self.assertIn("adamic_adar", pred["scores"])
        self.assertIn("resource_allocation", pred["scores"])
        self.assertIn("combined", pred["scores"])

    # 6. Error handling
    @patch("app.api.knowledge_graph_api.KnowledgeGraphBuilder")
    def test_06_error_handling(self, mock_builder_cls):
        """Verify server exception returns HTTP 500 Internal Server Error."""
        mock_builder = MagicMock()
        mock_builder_cls.return_value = mock_builder
        mock_builder.build_from_database.side_effect = Exception("Fatal prediction crash")

        resp = client.get("/api/knowledge-graph/link-predictions")
        self.assertEqual(resp.status_code, 500)
        self.assertIn("detail", resp.json())


if __name__ == "__main__":
    unittest.main()
