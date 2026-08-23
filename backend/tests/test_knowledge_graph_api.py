import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.session import Base, get_db
from app.main import app

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_fixture.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


class TestKnowledgeGraphAPI(unittest.TestCase):

    def setUp(self):
        Base.metadata.create_all(bind=engine)

    # 1. GET /api/knowledge-graph returns 200 OK & valid structure
    @patch("app.api.knowledge_graph_api.KnowledgeGraphBuilder")
    def test_01_get_knowledge_graph_success(self, mock_builder_cls):
        """Verify GET /api/knowledge-graph returns HTTP 200 OK with valid nodes, edges, and statistics."""
        mock_builder = MagicMock()
        mock_builder_cls.return_value = mock_builder

        mock_builder.build_from_database.return_value = {
            "total_papers": 1,
            "total_nodes": 2,
            "total_edges": 1,
            "paper_nodes": 1,
            "keyword_nodes": 0,
            "algorithm_nodes": 1,
            "dataset_nodes": 0,
            "methodology_nodes": 0,
            "domain_nodes": 0
        }

        mock_graph = MagicMock()
        mock_graph.nodes.return_value = [
            ("paper_1", {"type": "PAPER", "label": "Title 1", "paper_id": 1}),
            ("algorithm_yolo", {"type": "ALGORITHM", "label": "YOLO"})
        ]
        mock_graph.edges.return_value = [
            ("paper_1", "algorithm_yolo", {"relation": "USES_ALGORITHM"})
        ]
        mock_builder.graph_service.get_graph.return_value = mock_graph

        resp = client.get("/api/knowledge-graph")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertIn("statistics", data)
        self.assertIn("nodes", data)
        self.assertIn("edges", data)

    # 2. Correct node structure
    @patch("app.api.knowledge_graph_api.KnowledgeGraphBuilder")
    def test_02_correct_node_structure(self, mock_builder_cls):
        """Verify returned node objects contain id, type, label, and paper_id for papers."""
        mock_builder = MagicMock()
        mock_builder_cls.return_value = mock_builder
        mock_builder.build_from_database.return_value = {}

        mock_graph = MagicMock()
        mock_graph.nodes.return_value = [
            ("paper_5", {"type": "PAPER", "label": "Paper Title 5", "paper_id": 5}),
            ("keyword_ai", {"type": "KEYWORD", "label": "AI"})
        ]
        mock_graph.edges.return_value = []
        mock_builder.graph_service.get_graph.return_value = mock_graph

        resp = client.get("/api/knowledge-graph")
        self.assertEqual(resp.status_code, 200)
        nodes = resp.json()["nodes"]

        paper_node = next(n for n in nodes if n["id"] == "paper_5")
        self.assertEqual(paper_node["type"], "PAPER")
        self.assertEqual(paper_node["label"], "Paper Title 5")
        self.assertEqual(paper_node["paper_id"], 5)

        keyword_node = next(n for n in nodes if n["id"] == "keyword_ai")
        self.assertEqual(keyword_node["type"], "KEYWORD")
        self.assertEqual(keyword_node["label"], "AI")

    # 3. Correct edge structure
    @patch("app.api.knowledge_graph_api.KnowledgeGraphBuilder")
    def test_03_correct_edge_structure(self, mock_builder_cls):
        """Verify returned edge objects contain source, target, and relation."""
        mock_builder = MagicMock()
        mock_builder_cls.return_value = mock_builder
        mock_builder.build_from_database.return_value = {}

        mock_graph = MagicMock()
        mock_graph.nodes.return_value = [("paper_1", {}), ("algorithm_cnn", {})]
        mock_graph.edges.return_value = [("paper_1", "algorithm_cnn", {"relation": "USES_ALGORITHM"})]
        mock_builder.graph_service.get_graph.return_value = mock_graph

        resp = client.get("/api/knowledge-graph")
        edges = resp.json()["edges"]

        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["source"], "paper_1")
        self.assertEqual(edges[0]["target"], "algorithm_cnn")
        self.assertEqual(edges[0]["relation"], "USES_ALGORITHM")

    # 4. Correct statistics
    @patch("app.api.knowledge_graph_api.KnowledgeGraphBuilder")
    def test_04_correct_statistics(self, mock_builder_cls):
        """Verify returned statistics match builder summary."""
        mock_builder = MagicMock()
        mock_builder_cls.return_value = mock_builder
        mock_builder.build_from_database.return_value = {
            "total_nodes": 10,
            "total_edges": 15,
            "paper_nodes": 2,
            "keyword_nodes": 5,
            "algorithm_nodes": 3,
            "dataset_nodes": 0,
            "methodology_nodes": 0,
            "domain_nodes": 0
        }
        mock_graph = MagicMock()
        mock_graph.nodes.return_value = []
        mock_graph.edges.return_value = []
        mock_builder.graph_service.get_graph.return_value = mock_graph

        resp = client.get("/api/knowledge-graph")
        stats = resp.json()["statistics"]

        self.assertEqual(stats["total_nodes"], 10)
        self.assertEqual(stats["total_edges"], 15)
        self.assertEqual(stats["paper_nodes"], 2)

    # 5. Node-type filtering
    @patch("app.api.knowledge_graph_api.KnowledgeGraphBuilder")
    def test_05_node_type_filtering(self, mock_builder_cls):
        """Verify ?type=ALGORITHM filters nodes to ALGORITHM and PAPER nodes."""
        mock_builder = MagicMock()
        mock_builder_cls.return_value = mock_builder
        mock_builder.build_from_database.return_value = {}

        mock_graph = MagicMock()
        mock_graph.nodes.return_value = [
            ("paper_1", {"type": "PAPER", "label": "P1"}),
            ("algorithm_yolo", {"type": "ALGORITHM", "label": "YOLO"}),
            ("keyword_ai", {"type": "KEYWORD", "label": "AI"})
        ]
        mock_graph.edges.return_value = [
            ("paper_1", "algorithm_yolo", {"relation": "USES_ALGORITHM"}),
            ("paper_1", "keyword_ai", {"relation": "HAS_KEYWORD"})
        ]
        mock_builder.graph_service.get_graph.return_value = mock_graph

        resp = client.get("/api/knowledge-graph?type=ALGORITHM")
        self.assertEqual(resp.status_code, 200)
        nodes = resp.json()["nodes"]
        edges = resp.json()["edges"]

        node_types = {n["type"] for n in nodes}
        self.assertIn("PAPER", node_types)
        self.assertIn("ALGORITHM", node_types)
        self.assertNotIn("KEYWORD", node_types)

        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["target"], "algorithm_yolo")

    # 6. Invalid node type parameter
    def test_06_invalid_node_type_parameter(self):
        """Verify invalid node type parameter returns HTTP 400 Bad Request."""
        resp = client.get("/api/knowledge-graph?type=INVALID_TYPE")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("detail", resp.json())

    # 7. Empty graph
    @patch("app.api.knowledge_graph_api.KnowledgeGraphBuilder")
    def test_07_empty_graph(self, mock_builder_cls):
        """Verify empty graph returns nodes: [], edges: [], and stats 0."""
        mock_builder = MagicMock()
        mock_builder_cls.return_value = mock_builder
        mock_builder.build_from_database.return_value = {
            "total_papers": 0, "total_nodes": 0, "total_edges": 0,
            "paper_nodes": 0, "keyword_nodes": 0, "algorithm_nodes": 0,
            "dataset_nodes": 0, "methodology_nodes": 0, "domain_nodes": 0
        }
        mock_graph = MagicMock()
        mock_graph.nodes.return_value = []
        mock_graph.edges.return_value = []
        mock_builder.graph_service.get_graph.return_value = mock_graph

        resp = client.get("/api/knowledge-graph")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data["nodes"], [])
        self.assertEqual(data["edges"], [])
        self.assertEqual(data["statistics"]["total_nodes"], 0)

    # 8. GET /api/knowledge-graph/statistics
    @patch("app.api.knowledge_graph_api.KnowledgeGraphBuilder")
    def test_08_get_statistics_endpoint(self, mock_builder_cls):
        """Verify GET /api/knowledge-graph/statistics returns statistics JSON."""
        mock_builder = MagicMock()
        mock_builder_cls.return_value = mock_builder
        mock_builder.build_from_database.return_value = {
            "total_nodes": 84, "total_edges": 126, "paper_nodes": 7,
            "keyword_nodes": 50, "algorithm_nodes": 14, "dataset_nodes": 2,
            "methodology_nodes": 5, "domain_nodes": 6
        }

        resp = client.get("/api/knowledge-graph/statistics")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data["total_nodes"], 84)
        self.assertEqual(data["paper_nodes"], 7)

    # 9. GET /api/knowledge-graph/top-entities
    @patch("app.api.knowledge_graph_api.KnowledgeGraphBuilder")
    def test_09_get_top_entities_endpoint(self, mock_builder_cls):
        """Verify GET /api/knowledge-graph/top-entities returns formatted top entity categories."""
        mock_builder = MagicMock()
        mock_builder_cls.return_value = mock_builder
        mock_builder.get_top_entities.return_value = {
            "top_algorithms": [{"label": "LSTM", "paper_count": 5}],
            "top_datasets": [{"label": "COCO", "paper_count": 1}],
            "top_methodologies": [{"label": "Deep Learning", "paper_count": 7}],
            "top_domains": [{"label": "Transportation", "paper_count": 2}],
            "top_keywords": [{"label": "Machine Learning", "paper_count": 4}]
        }

        resp = client.get("/api/knowledge-graph/top-entities?top_k=5")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertIn("algorithms", data)
        self.assertEqual(data["algorithms"][0]["name"], "LSTM")
        self.assertEqual(data["algorithms"][0]["paper_count"], 5)

    # 10. top_k parameter validation
    def test_10_top_k_parameter_validation(self):
        """Verify top_k <= 0 or top_k > 20 returns error status code."""
        resp1 = client.get("/api/knowledge-graph/top-entities?top_k=0")
        self.assertIn(resp1.status_code, [400, 422])

        resp2 = client.get("/api/knowledge-graph/top-entities?top_k=50")
        self.assertIn(resp2.status_code, [400, 422])

    # 11. Database/graph error exception handling
    @patch("app.api.knowledge_graph_api.KnowledgeGraphBuilder")
    def test_11_error_handling(self, mock_builder_cls):
        """Verify unexpected database/graph exception returns HTTP 500 Internal Server Error."""
        mock_builder = MagicMock()
        mock_builder_cls.return_value = mock_builder
        mock_builder.build_from_database.side_effect = Exception("Fatal database error")

        resp = client.get("/api/knowledge-graph")
        self.assertEqual(resp.status_code, 500)
        self.assertIn("detail", resp.json())


if __name__ == "__main__":
    unittest.main()
