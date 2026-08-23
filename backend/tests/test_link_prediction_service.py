import sys
import unittest
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.knowledge_graph_service import KnowledgeGraphService
from app.services.link_prediction_service import LinkPredictionService
from app.models.paper_model import ResearchPaper


class TestLinkPredictionService(unittest.TestCase):

    def setUp(self):
        self.kg_service = KnowledgeGraphService()
        self.prediction_service = LinkPredictionService(graph_service=self.kg_service)

    # 1. Empty graph
    def test_01_empty_graph(self):
        """Verify empty graph produces zero predictions."""
        res = self.prediction_service.predict_links(top_k=10)
        self.assertEqual(res, [])

    # 2. Single paper graph
    def test_02_single_paper(self):
        """Verify single paper graph with no shared structure returns candidates or empty list cleanly."""
        paper = ResearchPaper(id=1, title="Paper 1", keywords=["AI"], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        self.kg_service.build_graph([paper])

        res = self.prediction_service.predict_links(top_k=10)
        self.assertIsInstance(res, list)

    # 3. Multiple papers candidate generation
    def test_03_multiple_papers(self):
        """Verify candidate generation across multiple papers sharing concepts."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=["YOLO"], datasets=["COCO"], methodologies=["Deep Learning"], application_domains=[])
        p2 = ResearchPaper(id=2, title="P2", keywords=[], algorithms=["YOLO"], datasets=["COCO"], methodologies=["Deep Learning"], application_domains=[])
        p3 = ResearchPaper(id=3, title="P3", keywords=[], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        self.kg_service.build_graph([p1, p2, p3])

        preds = self.prediction_service.predict_links(top_k=10)
        self.assertGreater(len(preds), 0)

    # 4. Jaccard calculation
    def test_04_jaccard_calculation(self):
        """Verify Jaccard calculation accuracy on shared neighbors."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="P2", keywords=[], algorithms=["YOLO", "CNN"], datasets=[], methodologies=[], application_domains=[])
        self.kg_service.build_graph([p1, p2])

        preds = self.prediction_service.predict_links(top_k=10)
        # Paper 1 candidate for CNN algorithm (shared YOLO node)
        cnn_pred = next((p for p in preds if p["source_paper_id"] == 1 and p["target_node_id"] == "algorithm_cnn"), None)
        self.assertIsNotNone(cnn_pred)
        self.assertGreater(cnn_pred["scores"]["jaccard"], 0.0)

    # 5. Adamic-Adar calculation
    def test_05_adamic_adar_calculation(self):
        """Verify Adamic-Adar score is > 0 for candidate linked via shared node."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="P2", keywords=[], algorithms=["YOLO", "ResNet"], datasets=[], methodologies=[], application_domains=[])
        self.kg_service.build_graph([p1, p2])

        preds = self.prediction_service.predict_links(top_k=10)
        resnet_pred = next((p for p in preds if p["target_node_id"] == "algorithm_resnet"), None)
        self.assertIsNotNone(resnet_pred)
        self.assertGreater(resnet_pred["scores"]["adamic_adar"], 0.0)

    # 6. Resource Allocation calculation
    def test_06_resource_allocation_calculation(self):
        """Verify Resource Allocation score is > 0 for shared neighbor."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="P2", keywords=[], algorithms=["YOLO", "Transformer"], datasets=[], methodologies=[], application_domains=[])
        self.kg_service.build_graph([p1, p2])

        preds = self.prediction_service.predict_links(top_k=10)
        tf_pred = next((p for p in preds if p["target_node_id"] == "algorithm_transformer"), None)
        self.assertIsNotNone(tf_pred)
        self.assertGreater(tf_pred["scores"]["resource_allocation"], 0.0)

    # 7. Combined score calculation
    def test_07_combined_score_calculation(self):
        """Verify combined score is bounded between 0.0 and 1.0."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=["A1"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="P2", keywords=[], algorithms=["A1", "A2"], datasets=[], methodologies=[], application_domains=[])
        self.kg_service.build_graph([p1, p2])

        preds = self.prediction_service.predict_links(top_k=10)
        for pred in preds:
            combined = pred["scores"]["combined"]
            self.assertGreaterEqual(combined, 0.0)
            self.assertLessEqual(combined, 1.0)

    # 8. Existing edges excluded
    def test_08_existing_edges_excluded(self):
        """Verify candidate predictions do not include already connected concept nodes."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        self.kg_service.build_graph([p1])

        preds = self.prediction_service.predict_links(top_k=10)
        # Should not predict (Paper 1 -> YOLO)
        existing = [p for p in preds if p["source_paper_id"] == 1 and p["target_node_id"] == "algorithm_yolo"]
        self.assertEqual(len(existing), 0)

    # 9. Self-links excluded
    def test_09_self_links_excluded(self):
        """Verify target_node_id is never the source paper node itself."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        self.kg_service.build_graph([p1])

        preds = self.prediction_service.predict_links(top_k=10)
        for pred in preds:
            self.assertNotEqual(str(pred["source_paper_id"]), str(pred["target_node_id"]))

    # 10. Duplicate predictions excluded
    def test_10_duplicate_predictions_excluded(self):
        """Verify candidate list contains unique (source_paper_id, target_node_id) tuples."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="P2", keywords=[], algorithms=["YOLO", "CNN"], datasets=[], methodologies=[], application_domains=[])
        self.kg_service.build_graph([p1, p2])

        preds = self.prediction_service.predict_links(top_k=50)
        pairs = [(p["source_paper_id"], p["target_node_id"]) for p in preds]
        self.assertEqual(len(pairs), len(set(pairs)))

    # 11. Correct relationship type
    def test_11_relationship_type_mapping(self):
        """Verify relationship_type is accurately mapped per concept node type."""
        p1 = ResearchPaper(id=1, title="P1", keywords=["K1"], algorithms=["A1"], datasets=["D1"], methodologies=["M1"], application_domains=["Dom1"])
        p2 = ResearchPaper(id=2, title="P2", keywords=["K1"], algorithms=["A1"], datasets=["D1"], methodologies=["M1"], application_domains=["Dom1"])
        self.kg_service.build_graph([p1, p2])

        preds = self.prediction_service.predict_links(top_k=50)
        for p in preds:
            if p["target_type"] == "ALGORITHM":
                self.assertEqual(p["relationship_type"], "USES_ALGORITHM")
            elif p["target_type"] == "DATASET":
                self.assertEqual(p["relationship_type"], "USES_DATASET")
            elif p["target_type"] == "METHODOLOGY":
                self.assertEqual(p["relationship_type"], "USES_METHODOLOGY")
            elif p["target_type"] == "DOMAIN":
                self.assertEqual(p["relationship_type"], "HAS_DOMAIN")
            elif p["target_type"] == "KEYWORD":
                self.assertEqual(p["relationship_type"], "HAS_KEYWORD")

    # 12. Correct ranking
    def test_12_correct_ranking(self):
        """Verify candidate predictions are sorted in descending order of combined score."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=["A1", "A2"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="P2", keywords=[], algorithms=["A1", "A2", "A3"], datasets=[], methodologies=[], application_domains=[])
        p3 = ResearchPaper(id=3, title="P3", keywords=[], algorithms=["A1", "A4"], datasets=[], methodologies=[], application_domains=[])
        self.kg_service.build_graph([p1, p2, p3])

        preds = self.prediction_service.predict_links(top_k=10)
        scores = [p["scores"]["combined"] for p in preds]
        self.assertEqual(scores, sorted(scores, reverse=True))

    # 13. Deterministic ordering
    def test_13_deterministic_ordering(self):
        """Verify two calls with identical graph produce identical predictions list."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=["A1"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="P2", keywords=[], algorithms=["A1", "A2"], datasets=[], methodologies=[], application_domains=[])
        self.kg_service.build_graph([p1, p2])

        preds1 = self.prediction_service.predict_links(top_k=10)
        preds2 = self.prediction_service.predict_links(top_k=10)
        self.assertEqual(preds1, preds2)

    # 14. top_k behavior
    def test_14_top_k_behavior(self):
        """Verify returned predictions list is truncated to top_k limit."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=["A1"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="P2", keywords=[], algorithms=["A1", "A2", "A3", "A4", "A5"], datasets=[], methodologies=[], application_domains=[])
        self.kg_service.build_graph([p1, p2])

        preds = self.prediction_service.predict_links(top_k=2)
        self.assertLessEqual(len(preds), 2)

    # 15. Graph remains unchanged
    def test_15_graph_remains_unchanged(self):
        """Verify NetworkX graph node and edge counts are identical before and after link prediction."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="P2", keywords=[], algorithms=["YOLO", "CNN"], datasets=[], methodologies=[], application_domains=[])
        self.kg_service.build_graph([p1, p2])

        g = self.kg_service.get_graph()
        initial_nodes = g.number_of_nodes()
        initial_edges = g.number_of_edges()

        self.prediction_service.predict_links(top_k=10)

        self.assertEqual(g.number_of_nodes(), initial_nodes)
        self.assertEqual(g.number_of_edges(), initial_edges)


if __name__ == "__main__":
    unittest.main()
