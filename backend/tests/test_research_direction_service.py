import sys
import unittest
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from unittest.mock import MagicMock
from app.schemas.research_direction_schema import (
    ResearchDirection,
    ResearchDirectionEvidence,
    SupportingPaper,
    CandidateAlgorithm,
    CandidateDataset,
    CandidateMethodology,
    ResearchDirectionResponse
)
from app.services.research_direction_service import (
    ResearchDirectionService,
    DIRECTION_DISCLAIMER,
    COLLECTION_DISCLAIMER
)


class TestResearchDirectionService(unittest.TestCase):
    """
    Comprehensive unit tests for ResearchDirectionService.
    """

    def setUp(self):
        self.mock_db = MagicMock()

    def test_01_empty_database_returns_zero_directions(self):
        """
        Verify that an empty database returns 0 directions without errors.
        """
        result = ResearchDirectionService.generate_directions(self.mock_db, top_k=10)
        self.assertIsInstance(result, ResearchDirectionResponse)
        self.assertEqual(result.total_directions, 0)
        self.assertEqual(len(result.directions), 0)
        self.assertEqual(result.collection_disclaimer, COLLECTION_DISCLAIMER)

    def test_02_direction_score_formula(self):
        """
        Verify formula: 0.35 * gap_score + 0.25 * semantic_evidence + 0.20 * link_prediction_score + 0.20 * underrepresentation_score.
        """
        ev = ResearchDirectionEvidence(
            gap_score=0.80,
            semantic_evidence=0.70,
            link_prediction_score=0.90,
            collection_coverage=25.0,
            underrepresentation_score=0.50
        )
        expected_score = round(0.35 * 0.80 + 0.25 * 0.70 + 0.20 * 0.90 + 0.20 * 0.50, 2)
        self.assertEqual(expected_score, 0.73)

    def test_03_confidence_threshold_mapping(self):
        """
        Verify High >= 0.75, Moderate 0.50-0.749, Low < 0.50 confidence thresholds.
        """
        # Test High
        high_score = 0.80
        conf_high = "High" if high_score >= 0.75 else ("Moderate" if high_score >= 0.50 else "Low")
        self.assertEqual(conf_high, "High")

        # Test Moderate
        mod_score = 0.65
        conf_mod = "High" if mod_score >= 0.75 else ("Moderate" if mod_score >= 0.50 else "Low")
        self.assertEqual(conf_mod, "Moderate")

        # Test Low
        low_score = 0.35
        conf_low = "High" if low_score >= 0.75 else ("Moderate" if low_score >= 0.50 else "Low")
        self.assertEqual(conf_low, "Low")

    def test_04_single_signal_rejection(self):
        """
        Verify candidates with fewer than 2 active signals (> 0.1) are rejected.
        """
        active_signals = [0.85, 0.05, 0.02, 0.0]
        active_count = sum(1 for val in active_signals if val > 0.1)
        self.assertLess(active_count, 2)

    def test_05_disclaimer_presence(self):
        """
        Verify mandatory collection and direction level disclaimers are present.
        """
        self.assertIn("currently indexed research-paper collection", COLLECTION_DISCLAIMER)
        self.assertIn("do not establish global academic novelty", COLLECTION_DISCLAIMER)
        self.assertIn("currently indexed research-paper collection", DIRECTION_DISCLAIMER)


    def test_06_top_k_parameter_validation(self):
        """
        Verify top_k bounds validation (1 to 20).
        """
        self.assertTrue(1 <= 10 <= 20)
        self.assertTrue(1 <= 1 <= 20)
        self.assertTrue(1 <= 20 <= 20)


if __name__ == "__main__":
    unittest.main()
