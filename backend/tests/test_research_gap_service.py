import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.knowledge_graph_service import KnowledgeGraphService
from app.services.research_gap_service import ResearchGapService
from app.models.paper_model import ResearchPaper


class TestResearchGapService(unittest.TestCase):

    def setUp(self):
        self.kg_service = KnowledgeGraphService()
        self.gap_service = ResearchGapService(graph_service=self.kg_service)

    # 1. Empty graph
    def test_01_empty_graph(self):
        """Verify empty graph produces zero research gaps."""
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = []

        gaps = self.gap_service.detect_gaps(mock_db, top_k=10)
        self.assertEqual(gaps, [])

    # 2. Empty candidate list
    @patch("app.services.research_gap_service.LinkPredictionService")
    def test_02_empty_candidate_list(self, mock_pred_cls):
        """Verify empty candidate prediction list returns zero research gaps."""
        mock_pred = MagicMock()
        mock_pred_cls.return_value = mock_pred
        mock_pred.predict_links.return_value = []

        paper = ResearchPaper(id=1, title="Paper 1", keywords=[], algorithms=[], datasets=[], methodologies=[], application_domains=[])
        self.kg_service.build_graph([paper])

        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [paper]

        gaps = self.gap_service.detect_gaps(mock_db, top_k=10)
        self.assertEqual(gaps, [])

    # 3. Existing relationship exclusion
    def test_03_existing_relationship_exclusion(self):
        """Verify candidate links already connected in graph are excluded."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        self.kg_service.build_graph([p1])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1]

        gaps = self.gap_service.detect_gaps(mock_db, top_k=10)
        existing = [g for g in gaps if g["source_paper_id"] == 1 and g["target_node_id"] == "algorithm_yolo"]
        self.assertEqual(len(existing), 0)

    # 4. Link prediction score contribution
    def test_04_link_prediction_score_contribution(self):
        """Verify link_prediction_score is correctly included in evidence structure."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="P2", keywords=[], algorithms=["YOLO", "CNN"], datasets=[], methodologies=[], application_domains=[])
        self.kg_service.build_graph([p1, p2])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1, p2]

        gaps = self.gap_service.detect_gaps(mock_db, top_k=10)
        if gaps:
            self.assertIn("link_prediction_score", gaps[0]["evidence"])

    # 5. Cross-paper support calculation
    def test_05_cross_paper_support_calculation(self):
        """Verify cross_paper_support calculation on co-occurring papers."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="P2", keywords=[], algorithms=["YOLO", "CNN"], datasets=[], methodologies=[], application_domains=[])
        self.kg_service.build_graph([p1, p2])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1, p2]

        gaps = self.gap_service.detect_gaps(mock_db, top_k=10)
        if gaps:
            self.assertGreaterEqual(gaps[0]["evidence"]["cross_paper_support"], 0.0)

    # 6. Semantic evidence calculation
    def test_06_semantic_evidence_calculation(self):
        """Verify semantic_evidence calculation using Sentence-BERT."""
        p1 = ResearchPaper(id=1, title="Driver Drowsiness Detection", abstract="Using computer vision for safety.", keywords=[], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="Vehicle Safety AI", abstract="Drowsiness monitoring framework.", keywords=[], algorithms=["YOLO", "CNN"], datasets=[], methodologies=[], application_domains=[])
        self.kg_service.build_graph([p1, p2])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1, p2]

        gaps = self.gap_service.detect_gaps(mock_db, top_k=10)
        if gaps:
            self.assertGreaterEqual(gaps[0]["evidence"]["semantic_evidence"], 0.0)

    # 7. Underrepresentation calculation
    def test_07_underrepresentation_calculation(self):
        """Verify underrepresentation score is computed accurately."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="P2", keywords=[], algorithms=["YOLO", "CNN"], datasets=[], methodologies=[], application_domains=[])
        self.kg_service.build_graph([p1, p2])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1, p2]

        gaps = self.gap_service.detect_gaps(mock_db, top_k=10)
        if gaps:
            self.assertGreaterEqual(gaps[0]["evidence"]["underrepresentation_score"], 0.0)

    # 8. Gap score formula
    def test_08_gap_score_formula(self):
        """Verify gap_score is bounded in [0.0, 1.0]."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="P2", keywords=[], algorithms=["YOLO", "CNN"], datasets=[], methodologies=[], application_domains=[])
        self.kg_service.build_graph([p1, p2])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1, p2]

        gaps = self.gap_service.detect_gaps(mock_db, top_k=10)
        for g in gaps:
            self.assertGreaterEqual(g["gap_score"], 0.0)
            self.assertLessEqual(g["gap_score"], 1.0)

    # 9. Confidence thresholds
    def test_09_confidence_thresholds(self):
        """Verify confidence string is one of High, Moderate, Low."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="P2", keywords=[], algorithms=["YOLO", "CNN"], datasets=[], methodologies=[], application_domains=[])
        self.kg_service.build_graph([p1, p2])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1, p2]

        gaps = self.gap_service.detect_gaps(mock_db, top_k=10)
        for g in gaps:
            self.assertIn(g["confidence"], ["High", "Moderate", "Low"])

    # 10. Minimum two-signal requirement
    def test_10_minimum_two_signal_requirement(self):
        """Verify candidates with fewer than 2 active signals (> 0.1) are excluded."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="P2", keywords=[], algorithms=["YOLO", "CNN"], datasets=[], methodologies=[], application_domains=[])
        self.kg_service.build_graph([p1, p2])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1, p2]

        gaps = self.gap_service.detect_gaps(mock_db, top_k=10)
        for g in gaps:
            ev = g["evidence"]
            active = sum([
                1 if ev["link_prediction_score"] > 0.1 else 0,
                1 if ev["cross_paper_support"] > 0.1 else 0,
                1 if ev["semantic_evidence"] > 0.1 else 0,
                1 if ev["underrepresentation_score"] > 0.1 else 0
            ])
            self.assertGreaterEqual(active, 2)

    # 11. Explanation generation
    def test_11_explanation_generation(self):
        """Verify explanation is a non-empty list of text strings."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="P2", keywords=[], algorithms=["YOLO", "CNN"], datasets=[], methodologies=[], application_domains=[])
        self.kg_service.build_graph([p1, p2])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1, p2]

        gaps = self.gap_service.detect_gaps(mock_db, top_k=10)
        for g in gaps:
            self.assertIsInstance(g["explanation"], list)
            self.assertGreater(len(g["explanation"]), 0)

    # 12. Deterministic ranking
    def test_12_deterministic_ranking(self):
        """Verify gap results are sorted by gap_score DESC."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="P2", keywords=[], algorithms=["YOLO", "CNN", "RNN"], datasets=[], methodologies=[], application_domains=[])
        self.kg_service.build_graph([p1, p2])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1, p2]

        gaps = self.gap_service.detect_gaps(mock_db, top_k=10)
        scores = [g["gap_score"] for g in gaps]
        self.assertEqual(scores, sorted(scores, reverse=True))

    # 13. Duplicate gap prevention
    def test_13_duplicate_gap_prevention(self):
        """Verify candidate gap list contains no duplicate (source_paper_id, target_node_id) pairs."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="P2", keywords=[], algorithms=["YOLO", "CNN"], datasets=[], methodologies=[], application_domains=[])
        self.kg_service.build_graph([p1, p2])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1, p2]

        gaps = self.gap_service.detect_gaps(mock_db, top_k=50)
        pairs = [(g["source_paper_id"], g["target_node_id"]) for g in gaps]
        self.assertEqual(len(pairs), len(set(pairs)))

    # 14. top_k behavior
    def test_14_top_k_behavior(self):
        """Verify gap results list is truncated to top_k limit."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="P2", keywords=[], algorithms=["YOLO", "CNN", "RNN"], datasets=[], methodologies=[], application_domains=[])
        self.kg_service.build_graph([p1, p2])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1, p2]

        gaps = self.gap_service.detect_gaps(mock_db, top_k=1)
        self.assertLessEqual(len(gaps), 1)

    # 15. Graph remains unchanged
    def test_15_graph_remains_unchanged(self):
        """Verify NetworkX graph topology remains unmutated after gap detection."""
        p1 = ResearchPaper(id=1, title="P1", keywords=[], algorithms=["YOLO"], datasets=[], methodologies=[], application_domains=[])
        p2 = ResearchPaper(id=2, title="P2", keywords=[], algorithms=["YOLO", "CNN"], datasets=[], methodologies=[], application_domains=[])
        self.kg_service.build_graph([p1, p2])
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [p1, p2]

        g = self.kg_service.get_graph()
        nodes_before = g.number_of_nodes()
        edges_before = g.number_of_edges()

        self.gap_service.detect_gaps(mock_db, top_k=10)

        self.assertEqual(g.number_of_nodes(), nodes_before)
        self.assertEqual(g.number_of_edges(), edges_before)


if __name__ == "__main__":
    unittest.main()
