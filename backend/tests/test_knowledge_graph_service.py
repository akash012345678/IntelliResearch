import sys
import unittest
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.knowledge_graph_service import (
    KnowledgeGraphService,
    normalize_entity,
    NODE_TYPE_PAPER,
    NODE_TYPE_KEYWORD,
    NODE_TYPE_ALGORITHM,
    NODE_TYPE_DATASET,
    NODE_TYPE_METHODOLOGY,
    NODE_TYPE_DOMAIN,
    REL_HAS_KEYWORD,
    REL_USES_ALGORITHM,
    REL_USES_DATASET,
    REL_USES_METHODOLOGY,
    REL_HAS_DOMAIN
)


class TestKnowledgeGraphService(unittest.TestCase):

    def setUp(self):
        self.service = KnowledgeGraphService()

    # 1. Empty graph
    def test_01_empty_graph(self):
        """Verify initial graph is empty and statistics return all zeros."""
        stats = self.service.get_statistics()
        self.assertEqual(stats["total_nodes"], 0)
        self.assertEqual(stats["total_edges"], 0)
        self.assertEqual(stats["paper_nodes"], 0)
        self.assertEqual(stats["keyword_nodes"], 0)
        self.assertEqual(stats["algorithm_nodes"], 0)

    # 2. Single paper graph
    def test_02_single_paper_graph(self):
        """Verify graph construction for a single paper."""
        paper = {
            "id": 101,
            "title": "Driver Drowsiness Detection",
            "keywords": ["drowsiness", "computer vision"],
            "algorithms": ["CNN", "YOLOv5"],
            "datasets": ["NTHU-DDD"],
            "methodologies": ["Deep Learning"],
            "application_domains": ["Automotive Safety"]
        }
        self.service.add_paper(paper)
        stats = self.service.get_statistics()

        self.assertEqual(stats["paper_nodes"], 1)
        self.assertEqual(stats["keyword_nodes"], 2)
        self.assertEqual(stats["algorithm_nodes"], 2)
        self.assertEqual(stats["dataset_nodes"], 1)
        self.assertEqual(stats["methodology_nodes"], 1)
        self.assertEqual(stats["domain_nodes"], 1)
        self.assertEqual(stats["total_nodes"], 8)
        self.assertEqual(stats["total_edges"], 7)

    # 3. Multiple paper graph
    def test_03_multiple_paper_graph(self):
        """Verify build_graph with multiple paper records."""
        papers = [
            {
                "id": 1,
                "title": "Paper 1",
                "keywords": ["AI"],
                "algorithms": ["CNN"],
                "datasets": [],
                "methodologies": [],
                "application_domains": []
            },
            {
                "id": 2,
                "title": "Paper 2",
                "keywords": ["ML"],
                "algorithms": ["RNN"],
                "datasets": [],
                "methodologies": [],
                "application_domains": []
            }
        ]
        stats = self.service.build_graph(papers)
        self.assertEqual(stats["paper_nodes"], 2)
        self.assertEqual(stats["keyword_nodes"], 2)
        self.assertEqual(stats["algorithm_nodes"], 2)
        self.assertEqual(stats["total_nodes"], 6)

    # 4. PAPER node creation
    def test_04_paper_node_creation(self):
        """Verify PAPER node attributes."""
        self.service.add_paper({"id": 10, "title": "Test Title"})
        graph = self.service.get_graph()

        self.assertTrue(graph.has_node("paper_10"))
        node_attrs = graph.nodes["paper_10"]
        self.assertEqual(node_attrs["id"], "paper_10")
        self.assertEqual(node_attrs["type"], NODE_TYPE_PAPER)
        self.assertEqual(node_attrs["label"], "Test Title")
        self.assertEqual(node_attrs["paper_id"], 10)

    # 5. KEYWORD node creation
    def test_05_keyword_node_creation(self):
        """Verify KEYWORD node creation."""
        self.service.add_paper({"id": 1, "title": "P1", "keywords": ["Neural Networks"]})
        graph = self.service.get_graph()

        node_id = "keyword_neural networks"
        self.assertTrue(graph.has_node(node_id))
        attrs = graph.nodes[node_id]
        self.assertEqual(attrs["type"], NODE_TYPE_KEYWORD)
        self.assertEqual(attrs["label"], "Neural Networks")

    # 6. ALGORITHM node creation
    def test_06_algorithm_node_creation(self):
        """Verify ALGORITHM node creation."""
        self.service.add_paper({"id": 1, "title": "P1", "algorithms": ["Random Forest"]})
        graph = self.service.get_graph()

        node_id = "algorithm_random forest"
        self.assertTrue(graph.has_node(node_id))
        attrs = graph.nodes[node_id]
        self.assertEqual(attrs["type"], NODE_TYPE_ALGORITHM)
        self.assertEqual(attrs["label"], "Random Forest")

    # 7. DATASET node creation
    def test_07_dataset_node_creation(self):
        """Verify DATASET node creation."""
        self.service.add_paper({"id": 1, "title": "P1", "datasets": ["ImageNet"]})
        graph = self.service.get_graph()

        node_id = "dataset_imagenet"
        self.assertTrue(graph.has_node(node_id))
        attrs = graph.nodes[node_id]
        self.assertEqual(attrs["type"], NODE_TYPE_DATASET)
        self.assertEqual(attrs["label"], "ImageNet")

    # 8. METHODOLOGY node creation
    def test_08_methodology_node_creation(self):
        """Verify METHODOLOGY node creation."""
        self.service.add_paper({"id": 1, "title": "P1", "methodologies": ["Transfer Learning"]})
        graph = self.service.get_graph()

        node_id = "methodology_transfer learning"
        self.assertTrue(graph.has_node(node_id))
        attrs = graph.nodes[node_id]
        self.assertEqual(attrs["type"], NODE_TYPE_METHODOLOGY)
        self.assertEqual(attrs["label"], "Transfer Learning")

    # 9. DOMAIN node creation
    def test_09_domain_node_creation(self):
        """Verify DOMAIN node creation."""
        self.service.add_paper({"id": 1, "title": "P1", "application_domains": ["Healthcare"]})
        graph = self.service.get_graph()

        node_id = "domain_healthcare"
        self.assertTrue(graph.has_node(node_id))
        attrs = graph.nodes[node_id]
        self.assertEqual(attrs["type"], NODE_TYPE_DOMAIN)
        self.assertEqual(attrs["label"], "Healthcare")

    # 10. Correct edge relationships
    def test_10_correct_edge_relationships(self):
        """Verify correct relationship types on directed edges."""
        paper = {
            "id": 5,
            "title": "P5",
            "keywords": ["kw"],
            "algorithms": ["algo"],
            "datasets": ["ds"],
            "methodologies": ["method"],
            "application_domains": ["domain"]
        }
        self.service.add_paper(paper)
        graph = self.service.get_graph()

        self.assertEqual(graph.edges["paper_5", "keyword_kw"]["relation"], REL_HAS_KEYWORD)
        self.assertEqual(graph.edges["paper_5", "algorithm_algo"]["relation"], REL_USES_ALGORITHM)
        self.assertEqual(graph.edges["paper_5", "dataset_ds"]["relation"], REL_USES_DATASET)
        self.assertEqual(graph.edges["paper_5", "methodology_method"]["relation"], REL_USES_METHODOLOGY)
        self.assertEqual(graph.edges["paper_5", "domain_domain"]["relation"], REL_HAS_DOMAIN)

    # 11. Duplicate entity prevention
    def test_11_duplicate_entity_prevention(self):
        """Verify adding identical entities creates only one node."""
        self.service.add_entity(NODE_TYPE_ALGORITHM, "YOLO")
        self.service.add_entity(NODE_TYPE_ALGORITHM, "YOLO")
        self.service.add_entity(NODE_TYPE_ALGORITHM, " yolo ")

        stats = self.service.get_statistics()
        self.assertEqual(stats["algorithm_nodes"], 1)

    # 12. Duplicate edge prevention
    def test_12_duplicate_edge_prevention(self):
        """Verify duplicate relationship additions do not create multiple edges."""
        self.service.add_paper_node(1, "Title 1")
        self.service.add_entity(NODE_TYPE_KEYWORD, "AI")

        added1 = self.service.add_relationship("paper_1", "keyword_ai", REL_HAS_KEYWORD)
        added2 = self.service.add_relationship("paper_1", "keyword_ai", REL_HAS_KEYWORD)

        self.assertTrue(added1)
        self.assertFalse(added2)
        self.assertEqual(self.service.get_graph().number_of_edges(), 1)

    # 13. Entity normalization
    def test_13_entity_normalization(self):
        """Verify whitespace trimming and case normalization."""
        key1, label1 = normalize_entity("Deep Learning")
        key2, label2 = normalize_entity("deep learning")
        key3, label3 = normalize_entity("  DEEP  LEARNING  ")

        self.assertEqual(key1, "deep learning")
        self.assertEqual(key2, "deep learning")
        self.assertEqual(key3, "deep learning")
        self.assertEqual(label1, "Deep Learning")
        self.assertEqual(label3, "DEEP LEARNING")

    # 14. Different algorithms remain distinct
    def test_14_different_algorithms_remain_distinct(self):
        """Verify technical variations like YOLO, YOLOv5, YOLOv8 are preserved distinctly."""
        self.service.add_entity(NODE_TYPE_ALGORITHM, "YOLO")
        self.service.add_entity(NODE_TYPE_ALGORITHM, "YOLOv5")
        self.service.add_entity(NODE_TYPE_ALGORITHM, "YOLOv8")

        stats = self.service.get_statistics()
        self.assertEqual(stats["algorithm_nodes"], 3)
        graph = self.service.get_graph()
        self.assertTrue(graph.has_node("algorithm_yolo"))
        self.assertTrue(graph.has_node("algorithm_yolov5"))
        self.assertTrue(graph.has_node("algorithm_yolov8"))

    # 15. Shared entities across multiple papers
    def test_15_shared_entities_across_multiple_papers(self):
        """Verify multiple papers using the same algorithm connect to one shared node."""
        p1 = {"id": 1, "title": "Paper 1", "algorithms": ["YOLO"]}
        p2 = {"id": 2, "title": "Paper 2", "algorithms": ["YOLO"]}
        p3 = {"id": 3, "title": "Paper 3", "algorithms": ["YOLO"]}

        self.service.add_paper(p1)
        self.service.add_paper(p2)
        self.service.add_paper(p3)

        stats = self.service.get_statistics()
        self.assertEqual(stats["paper_nodes"], 3)
        self.assertEqual(stats["algorithm_nodes"], 1)

        graph = self.service.get_graph()
        # Shared node 'algorithm_yolo' should have in-degree of 3
        self.assertEqual(graph.in_degree("algorithm_yolo"), 3)

    # 16. Graph statistics
    def test_16_graph_statistics(self):
        """Verify get_statistics calculates accurate counts from NetworkX graph."""
        paper = {
            "id": 99,
            "title": "Comprehensive Paper",
            "keywords": ["kw1", "kw2"],
            "algorithms": ["algo1"],
            "datasets": ["ds1", "ds2", "ds3"],
            "methodologies": ["m1"],
            "application_domains": ["dom1"]
        }
        self.service.add_paper(paper)
        stats = self.service.get_statistics()

        self.assertEqual(stats["paper_nodes"], 1)
        self.assertEqual(stats["keyword_nodes"], 2)
        self.assertEqual(stats["algorithm_nodes"], 1)
        self.assertEqual(stats["dataset_nodes"], 3)
        self.assertEqual(stats["methodology_nodes"], 1)
        self.assertEqual(stats["domain_nodes"], 1)
        self.assertEqual(stats["total_nodes"], 9)
        self.assertEqual(stats["total_edges"], 8)

    # 17. clear_graph()
    def test_17_clear_graph(self):
        """Verify clear_graph resets all nodes and edges."""
        self.service.add_paper({"id": 1, "title": "P1", "keywords": ["K1"]})
        self.assertGreater(self.service.get_graph().number_of_nodes(), 0)

        self.service.clear_graph()
        stats = self.service.get_statistics()
        self.assertEqual(stats["total_nodes"], 0)
        self.assertEqual(stats["total_edges"], 0)

    # 18. Rebuilding the graph after clearing
    def test_18_rebuilding_graph_after_clearing(self):
        """Verify rebuilding the graph after clear_graph works correctly."""
        papers = [{"id": 1, "title": "P1", "algorithms": ["CNN"]}]
        self.service.build_graph(papers)
        self.assertEqual(self.service.get_statistics()["paper_nodes"], 1)

        self.service.clear_graph()
        self.assertEqual(self.service.get_statistics()["total_nodes"], 0)

        self.service.build_graph(papers)
        self.assertEqual(self.service.get_statistics()["paper_nodes"], 1)
        self.assertEqual(self.service.get_statistics()["algorithm_nodes"], 1)


if __name__ == "__main__":
    unittest.main()
