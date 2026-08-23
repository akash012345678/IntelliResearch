import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.knowledge_graph_builder import KnowledgeGraphBuilder
from app.services.knowledge_graph_service import KnowledgeGraphService
from app.database.session import SessionLocal
from app.models.paper_model import ResearchPaper


class TestKnowledgeGraphBuilder(unittest.TestCase):

    def setUp(self):
        self.service = KnowledgeGraphService()
        self.builder = KnowledgeGraphBuilder(graph_service=self.service)

    # 1. Empty database handling
    def test_01_empty_database(self):
        """Verify building from an empty database returns 0 papers and 0 nodes."""
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = []

        res = self.builder.build_from_database(mock_db)
        self.assertEqual(res["total_papers"], 0)
        self.assertEqual(res["total_nodes"], 0)
        self.assertEqual(res["total_edges"], 0)
        self.assertEqual(res["top_entities"]["top_algorithms"], [])

    # 2. One paper processing
    def test_02_one_paper(self):
        """Verify building from 1 paper record."""
        p = MagicMock(id=1, title="Paper 1", keywords=["AI"], algorithms=["CNN"], datasets=[], methodologies=[], application_domains=[])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p]

        res = self.builder.build_from_database(mock_db)
        self.assertEqual(res["total_papers"], 1)
        self.assertEqual(res["paper_nodes"], 1)
        self.assertEqual(res["algorithm_nodes"], 1)

    # 3. Multiple papers processing
    def test_03_multiple_papers(self):
        """Verify building from multiple paper records."""
        p1 = MagicMock(id=1, title="P1", keywords=["K1"], algorithms=["A1"], datasets=[], methodologies=[], application_domains=[])
        p2 = MagicMock(id=2, title="P2", keywords=["K2"], algorithms=["A2"], datasets=[], methodologies=[], application_domains=[])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1, p2]

        res = self.builder.build_from_database(mock_db)
        self.assertEqual(res["total_papers"], 2)
        self.assertEqual(res["paper_nodes"], 2)

    # 4. Complete metadata handling
    def test_04_complete_metadata(self):
        """Verify processing paper with complete metadata fields."""
        p = MagicMock(
            id=10,
            title="Complete Paper",
            keywords=["kw"],
            algorithms=["algo"],
            datasets=["ds"],
            methodologies=["method"],
            application_domains=["domain"]
        )
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p]

        res = self.builder.build_from_database(mock_db)
        self.assertEqual(res["paper_nodes"], 1)
        self.assertEqual(res["keyword_nodes"], 1)
        self.assertEqual(res["algorithm_nodes"], 1)
        self.assertEqual(res["dataset_nodes"], 1)
        self.assertEqual(res["methodology_nodes"], 1)
        self.assertEqual(res["domain_nodes"], 1)
        self.assertEqual(res["total_nodes"], 6)

    # 5. Empty metadata list handling ([])
    def test_05_empty_metadata_lists(self):
        """Verify paper with empty metadata lists ([]) still creates PAPER node cleanly."""
        p = MagicMock(id=20, title="Empty Lists Paper", keywords=[], algorithms=[], datasets=[], methodologies=[], application_domains=[])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p]

        res = self.builder.build_from_database(mock_db)
        self.assertEqual(res["total_papers"], 1)
        self.assertEqual(res["paper_nodes"], 1)
        self.assertEqual(res["total_nodes"], 1)
        self.assertEqual(res["total_edges"], 0)

    # 6. None metadata field handling
    def test_06_none_metadata_fields(self):
        """Verify paper with None metadata fields does not crash."""
        p = MagicMock(id=30, title="None Metadata Paper", keywords=None, algorithms=None, datasets=None, methodologies=None, application_domains=None)
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p]

        res = self.builder.build_from_database(mock_db)
        self.assertEqual(res["total_papers"], 1)
        self.assertEqual(res["paper_nodes"], 1)

    # 7. Shared algorithms node linking
    def test_07_shared_algorithms(self):
        """Verify multiple papers referencing same algorithm link to one shared node."""
        p1 = MagicMock(id=1, title="P1", keywords=[], algorithms=["YOLOv5"], datasets=[], methodologies=[], application_domains=[])
        p2 = MagicMock(id=2, title="P2", keywords=[], algorithms=["YOLOv5"], datasets=[], methodologies=[], application_domains=[])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1, p2]

        res = self.builder.build_from_database(mock_db)
        self.assertEqual(res["algorithm_nodes"], 1)
        self.assertEqual(res["top_entities"]["top_algorithms"][0]["label"], "YOLOv5")
        self.assertEqual(res["top_entities"]["top_algorithms"][0]["paper_count"], 2)

    # 8. Shared datasets node linking
    def test_08_shared_datasets(self):
        """Verify multiple papers sharing a dataset."""
        p1 = MagicMock(id=1, title="P1", keywords=[], algorithms=[], datasets=["COCO"], methodologies=[], application_domains=[])
        p2 = MagicMock(id=2, title="P2", keywords=[], algorithms=[], datasets=["COCO"], methodologies=[], application_domains=[])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1, p2]

        res = self.builder.build_from_database(mock_db)
        self.assertEqual(res["dataset_nodes"], 1)
        self.assertEqual(res["top_entities"]["top_datasets"][0]["label"], "COCO")

    # 9. Shared methodologies node linking
    def test_09_shared_methodologies(self):
        """Verify multiple papers sharing a methodology."""
        p1 = MagicMock(id=1, title="P1", keywords=[], algorithms=[], datasets=[], methodologies=["Deep Learning"], application_domains=[])
        p2 = MagicMock(id=2, title="P2", keywords=[], algorithms=[], datasets=[], methodologies=["Deep Learning"], application_domains=[])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1, p2]

        res = self.builder.build_from_database(mock_db)
        self.assertEqual(res["methodology_nodes"], 1)
        self.assertEqual(res["top_entities"]["top_methodologies"][0]["label"], "Deep Learning")

    # 10. Shared domains node linking
    def test_10_shared_domains(self):
        """Verify multiple papers sharing an application domain."""
        p1 = MagicMock(id=1, title="P1", keywords=[], algorithms=[], datasets=[], methodologies=[], application_domains=["Transportation"])
        p2 = MagicMock(id=2, title="P2", keywords=[], algorithms=[], datasets=[], methodologies=[], application_domains=["Transportation"])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1, p2]

        res = self.builder.build_from_database(mock_db)
        self.assertEqual(res["domain_nodes"], 1)
        self.assertEqual(res["top_entities"]["top_domains"][0]["label"], "Transportation")

    # 11. Duplicate & normalized metadata handling
    def test_11_duplicate_normalized_metadata(self):
        """Verify case & whitespace variations unify into single concept node."""
        p1 = MagicMock(id=1, title="P1", keywords=[], algorithms=["CNN"], datasets=[], methodologies=[], application_domains=[])
        p2 = MagicMock(id=2, title="P2", keywords=[], algorithms=[" cnn "], datasets=[], methodologies=[], application_domains=[])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1, p2]

        res = self.builder.build_from_database(mock_db)
        self.assertEqual(res["algorithm_nodes"], 1)

    # 12. Correct paper-node count
    def test_12_correct_paper_node_count(self):
        """Verify paper node count matches input records."""
        papers = [MagicMock(id=i, title=f"P{i}", keywords=[], algorithms=[], datasets=[], methodologies=[], application_domains=[]) for i in range(1, 6)]
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = papers

        res = self.builder.build_from_database(mock_db)
        self.assertEqual(res["paper_nodes"], 5)

    # 13. Correct graph statistics
    def test_13_correct_graph_statistics(self):
        """Verify total nodes & edges match NetworkX graph state."""
        p1 = MagicMock(id=1, title="P1", keywords=["AI"], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1]

        res = self.builder.build_from_database(mock_db)
        self.assertEqual(res["total_nodes"], 3)  # Paper + Keyword + Algorithm
        self.assertEqual(res["total_edges"], 2)

    # 14. Database failure handling
    def test_14_database_failure_handling(self):
        """Verify database exception raises RuntimeError."""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("DB Connection Timeout")

        with self.assertRaises(RuntimeError):
            self.builder.build_from_database(mock_db)

    # 15. Controlled Real Supabase Integration Test
    def test_15_real_supabase_integration(self):
        """
        Controlled read-only integration test querying live Supabase PostgreSQL database
        and building the NetworkX Knowledge Graph.
        """
        try:
            db_session = SessionLocal()
            res = self.builder.build_from_database(db_session)
            db_session.close()

            print("\n=== Real Supabase PostgreSQL Knowledge Graph Integration Results ===")
            print(f"Total Papers Processed: {res['total_papers']}")
            print(f"Total Graph Nodes: {res['total_nodes']}")
            print(f"Total Graph Edges: {res['total_edges']}")
            print(f"Paper Nodes: {res['paper_nodes']}")
            print(f"Keyword Nodes: {res['keyword_nodes']}")
            print(f"Algorithm Nodes: {res['algorithm_nodes']}")
            print(f"Dataset Nodes: {res['dataset_nodes']}")
            print(f"Methodology Nodes: {res['methodology_nodes']}")
            print(f"Domain Nodes: {res['domain_nodes']}")

            print("\n--- Top Shared Research Entities ---")
            for cat, items in res["top_entities"].items():
                print(f"  {cat}: {[item['label'] + ' (' + str(item['paper_count']) + ')' for item in items]}")

            self.assertGreaterEqual(res["total_papers"], 0)
        except Exception as e:
            self.fail(f"Real Supabase integration test failed with exception: {e}")


if __name__ == "__main__":
    unittest.main()
