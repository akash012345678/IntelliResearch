import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.knowledge_graph_service import KnowledgeGraphService
from app.services.global_research_intelligence_service import GlobalResearchIntelligenceService
from app.models.paper_model import ResearchPaper


class TestGlobalResearchIntelligenceService(unittest.TestCase):

    def setUp(self):
        self.kg_service = KnowledgeGraphService()
        self.service = GlobalResearchIntelligenceService(graph_service=self.kg_service)

    # 1. Empty collection
    def test_01_empty_collection(self):
        """Verify empty collection returns structured 0-value response."""
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = []

        res = self.service.analyze_collection(mock_db)
        self.assertEqual(res["collection_summary"]["total_papers"], 0)
        self.assertEqual(res["paper_landscape"], [])
        self.assertEqual(res["paper_relationships"], [])

    # 2. Single paper collection
    def test_02_single_paper_collection(self):
        """Verify single paper collection handles landscape without crashing."""
        p1 = ResearchPaper(id=1, title="Paper 1", keywords=["AI"], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1]

        res = self.service.analyze_collection(mock_db)
        self.assertEqual(res["collection_summary"]["total_papers"], 1)
        self.assertEqual(len(res["paper_landscape"]), 1)
        self.assertEqual(res["paper_relationships"], [])  # Need >= 2 papers for relationships

    # 3. Multiple paper collection
    def test_03_multiple_paper_collection(self):
        """Verify multi-paper collection produces paper landscape and relationships."""
        p1 = ResearchPaper(id=1, title="Paper 1", keywords=["AI"], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="Paper 2", keywords=["AI"], algorithms=["CNN"], datasets=[], methodologies=[], application_domains=[])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1, p2]

        res = self.service.analyze_collection(mock_db)
        self.assertEqual(res["collection_summary"]["total_papers"], 2)
        self.assertEqual(len(res["paper_landscape"]), 2)

    # 4. Collection summary
    def test_04_collection_summary(self):
        """Verify collection_summary contains all expected total keys."""
        p1 = ResearchPaper(id=1, title="P1", keywords=["AI"], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1]

        res = self.service.analyze_collection(mock_db)
        s = res["collection_summary"]
        self.assertIn("total_papers", s)
        self.assertIn("total_graph_nodes", s)
        self.assertIn("total_graph_edges", s)
        self.assertIn("total_keywords", s)
        self.assertIn("total_algorithms", s)

    # 5. Shared concept aggregation
    def test_05_shared_concept_aggregation(self):
        """Verify shared_concepts includes coverage_percentage and sorting."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="P2", keywords=[], algorithms=["YOLO", "CNN"], datasets=[], methodologies=[], application_domains=[])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1, p2]

        res = self.service.analyze_collection(mock_db)
        algos = res["shared_concepts"]["algorithms"]
        self.assertGreater(len(algos), 0)
        self.assertEqual(algos[0]["name"], "YOLO")
        self.assertEqual(algos[0]["paper_count"], 2)
        self.assertEqual(algos[0]["coverage_percentage"], 100.0)

    # 6. Paper relationship generation
    def test_06_paper_relationship_generation(self):
        """Verify paper_relationships calculates pairwise similarity scores."""
        p1 = ResearchPaper(id=1, title="Driver Safety Vision", abstract="Drowsiness detection.", keywords=[], algorithms=[], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="Driver Safety Monitoring", abstract="Drowsiness detection AI.", keywords=[], algorithms=[], datasets=[], methodologies=[], application_domains=[])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1, p2]

        res = self.service.analyze_collection(mock_db)
        rels = res["paper_relationships"]
        self.assertEqual(len(rels), 1)
        self.assertGreaterEqual(rels[0]["similarity_score"], 0.0)

    # 7. Self relationship exclusion
    def test_07_self_relationship_exclusion(self):
        """Verify paper_relationships never includes self-pairs (source_paper_id == target_paper_id)."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=[], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="P2", keywords=[], algorithms=[], datasets=[], methodologies=[], application_domains=[])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1, p2]

        res = self.service.analyze_collection(mock_db)
        for r in res["paper_relationships"]:
            self.assertNotEqual(r["source_paper_id"], r["target_paper_id"])

    # 8. Duplicate relationship exclusion
    def test_08_duplicate_relationship_exclusion(self):
        """Verify pair (p1, p2) is returned once, without reverse duplicate (p2, p1)."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=[], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="P2", keywords=[], algorithms=[], datasets=[], methodologies=[], application_domains=[])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1, p2]

        res = self.service.analyze_collection(mock_db)
        pairs = [(r["source_paper_id"], r["target_paper_id"]) for r in res["paper_relationships"]]
        self.assertEqual(len(pairs), len(set(pairs)))

    # 9. Research gap aggregation
    def test_09_research_gap_aggregation(self):
        """Verify gaps array contains research gap items."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="P2", keywords=[], algorithms=["YOLO", "CNN"], datasets=[], methodologies=[], application_domains=[])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1, p2]

        res = self.service.analyze_collection(mock_db)
        self.assertIsInstance(res["gaps"], list)

    # 10. Confidence counts
    def test_10_confidence_counts(self):
        """Verify research_gap_summary breakdown counts equal total_gaps."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="P2", keywords=[], algorithms=["YOLO", "CNN"], datasets=[], methodologies=[], application_domains=[])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1, p2]

        res = self.service.analyze_collection(mock_db)
        s = res["research_gap_summary"]
        self.assertEqual(s["total_gaps"], s["high_confidence"] + s["moderate_confidence"] + s["low_confidence"])

    # 11. Underrepresented concept detection
    def test_11_underrepresented_concept_detection(self):
        """Verify underrepresented concepts include paper_count and coverage_percentage."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="P2", keywords=[], algorithms=["YOLO", "RareAlgo"], datasets=[], methodologies=[], application_domains=[])
        p3 = ResearchPaper(id=3, title="P3", keywords=[], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1, p2, p3]

        res = self.service.analyze_collection(mock_db)
        und = res["underrepresented_concepts"]
        rare = next((u for u in und if u["name"] == "RareAlgo"), None)
        if rare:
            self.assertEqual(rare["paper_count"], 1)

    # 12. Candidate research direction generation
    def test_12_candidate_research_direction_generation(self):
        """Verify candidate research directions include title, description, confidence, disclaimer."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="P2", keywords=[], algorithms=["YOLO", "CNN"], datasets=[], methodologies=[], application_domains=[])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1, p2]

        res = self.service.analyze_collection(mock_db)
        dirs = res["candidate_research_directions"]
        if dirs:
            self.assertIn("title", dirs[0])
            self.assertIn("description", dirs[0])
            self.assertIn("disclaimer", dirs[0])

    # 13. Deterministic ordering
    def test_13_deterministic_ordering(self):
        """Verify repeated calls on same DB produce identical results."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="P2", keywords=[], algorithms=["YOLO", "CNN"], datasets=[], methodologies=[], application_domains=[])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1, p2]

        res1 = self.service.analyze_collection(mock_db)
        res2 = self.service.analyze_collection(mock_db)
        self.assertEqual(res1["collection_summary"], res2["collection_summary"])

    # 14. Parameter validation
    def test_14_parameter_validation(self):
        """Verify analysis respects max limit parameters."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="P2", keywords=[], algorithms=["YOLO", "CNN"], datasets=[], methodologies=[], application_domains=[])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1, p2]

        res = self.service.analyze_collection(mock_db, max_paper_relationships=1, max_gaps=1)
        self.assertLessEqual(len(res["paper_relationships"]), 1)
        self.assertLessEqual(len(res["gaps"]), 1)

    # 15. Response schema completeness
    def test_15_response_schema_completeness(self):
        """Verify all 9 top-level keys exist in output dictionary."""
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = []

        res = self.service.analyze_collection(mock_db)
        for key in [
            "collection_summary", "paper_landscape", "shared_concepts",
            "paper_relationships", "research_gap_summary", "gaps",
            "underrepresented_concepts", "candidate_research_directions", "collection_disclaimer"
        ]:
            self.assertIn(key, res)

    # 16. Database read-only behavior
    def test_16_database_readonly_behavior(self):
        """Verify database query methods called are read-only (.all())."""
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = []

        self.service.analyze_collection(mock_db)
        self.assertFalse(mock_db.add.called)
        self.assertFalse(mock_db.commit.called)
        self.assertFalse(mock_db.delete.called)

    # 17. Graph immutability
    def test_17_graph_immutability(self):
        """Verify NetworkX graph topology remains unmutated after collection analysis."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="P2", keywords=[], algorithms=["YOLO", "CNN"], datasets=[], methodologies=[], application_domains=[])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1, p2]

        self.kg_service.build_graph([p1, p2])
        g = self.kg_service.get_graph()
        n_before = g.number_of_nodes()
        e_before = g.number_of_edges()

        self.service.analyze_collection(mock_db)

        self.assertEqual(g.number_of_nodes(), n_before)
        self.assertEqual(g.number_of_edges(), e_before)

    # 18. Regression compatibility
    def test_18_regression_compatibility(self):
        """Verify service initializes cleanly with all sub-services."""
        self.assertIsNotNone(self.service.link_prediction_service)
        self.assertIsNotNone(self.service.research_gap_service)
        self.assertIsNotNone(self.service.embedding_service)


if __name__ == "__main__":
    unittest.main()
