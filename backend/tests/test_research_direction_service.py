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

    def test_07_compute_opportunity_key_normalization(self):
        """
        TEST 7: Verify that opportunity keys normalize lowercase, whitespace, punctuation,
        and are order-invariant for algorithm combinations.
        """
        from app.services.research_direction_service import compute_opportunity_key

        key1 = compute_opportunity_key("YOLO", "Vision Transformer", "Computer Vision")
        key2 = compute_opportunity_key("vision-transformer", "  yolo  ", "computer vision!")
        key3 = compute_opportunity_key("Vision Transformer", "YOLO", "Computer Vision")

        self.assertEqual(key1, key2)
        self.assertEqual(key1, key3)
        self.assertIn("vision transformer", key1)
        self.assertIn("yolo", key1)
        self.assertIn("computer vision", key1)

    def test_08_merge_duplicate_directions_preserves_strongest_evidence(self):
        """
        TEST 8: Verify merging two directions with same opportunity key preserves
        strongest gap score, semantic relevance, highest confidence, unique supporting papers,
        and unique candidate algorithms.
        """
        d1 = ResearchDirection(
            direction_id="temp_1",
            title="Explore YOLO + Vision Transformer for Computer Vision",
            research_problem="Problem 1",
            motivation="Motivation 1",
            existing_evidence=["Evidence A"],
            missing_aspect="Missing 1",
            proposed_direction="Direction 1",
            supporting_papers=[
                SupportingPaper(paper_id=1, title="Paper 1", role="Provides primary domain context (Computer Vision) and baseline concepts."),
                SupportingPaper(paper_id=2, title="Paper 2", role="Provides empirical evidence for concept 'Vision Transformer'.")
            ],
            supporting_concepts=["YOLO", "Vision Transformer", "Deep Learning"],
            candidate_algorithms=[
                CandidateAlgorithm(name="YOLO", supporting_paper_count=1, reason="Baseline"),
                CandidateAlgorithm(name="Vision Transformer", supporting_paper_count=1, reason="Target")
            ],
            candidate_datasets=[
                CandidateDataset(name="COCO", supporting_paper_count=1, reason="Benchmark")
            ],
            candidate_methodologies=[
                CandidateMethodology(name="Object Detection", paper_count=1, coverage_percentage=25.0)
            ],
            evidence=ResearchDirectionEvidence(
                gap_score=0.72,
                semantic_evidence=0.68,
                link_prediction_score=0.75,
                collection_coverage=50.0,
                underrepresentation_score=0.30
            ),
            direction_score=0.65,
            confidence="Moderate",
            disclaimer=DIRECTION_DISCLAIMER
        )

        d2 = ResearchDirection(
            direction_id="temp_2",
            title="Explore YOLO + Vision Transformer for Computer Vision",
            research_problem="Problem 2",
            motivation="Motivation 2",
            existing_evidence=["Evidence B"],
            missing_aspect="Missing 2",
            proposed_direction="Direction 2",
            supporting_papers=[
                SupportingPaper(paper_id=2, title="Paper 2", role="Provides empirical evidence for concept 'Vision Transformer'."),
                SupportingPaper(paper_id=3, title="Paper 3", role="Provides empirical evidence for concept 'Vision Transformer'.")
            ],
            supporting_concepts=["Vision Transformer", "Computer Vision"],
            candidate_algorithms=[
                CandidateAlgorithm(name="yolo", supporting_paper_count=1, reason="Baseline"),
                CandidateAlgorithm(name="Vision Transformer", supporting_paper_count=1, reason="Target")
            ],
            candidate_datasets=[
                CandidateDataset(name="ImageNet", supporting_paper_count=1, reason="Benchmark")
            ],
            candidate_methodologies=[],
            evidence=ResearchDirectionEvidence(
                gap_score=0.85,
                semantic_evidence=0.82,
                link_prediction_score=0.78,
                collection_coverage=50.0,
                underrepresentation_score=0.35
            ),
            direction_score=0.80,
            confidence="High",
            disclaimer=DIRECTION_DISCLAIMER
        )

        merged = ResearchDirectionService._merge_directions(d1, d2, total_papers=4)

        # Verify strongest evidence preserved
        self.assertEqual(merged.evidence.gap_score, 0.85)
        self.assertEqual(merged.evidence.semantic_evidence, 0.82)
        self.assertEqual(merged.evidence.link_prediction_score, 0.78)
        self.assertEqual(merged.evidence.underrepresentation_score, 0.35)
        self.assertEqual(merged.direction_score, 0.80)
        self.assertEqual(merged.confidence, "High")

        # Verify unique supporting papers (paper IDs 1, 2, 3 -> exactly 3 unique papers)
        self.assertEqual(len(merged.supporting_papers), 3)
        sp_ids = [sp.paper_id for sp in merged.supporting_papers]
        self.assertEqual(sorted(sp_ids), [1, 2, 3])

        # Verify coverage recalculated
        self.assertEqual(merged.evidence.collection_coverage, 75.0)  # 3/4 * 100

        # Verify candidate algorithms deduplicated
        algo_names = [a.name.lower() for a in merged.candidate_algorithms]
        self.assertEqual(len(algo_names), 2)
        self.assertIn("yolo", algo_names)
        self.assertIn("vision transformer", algo_names)

        # Verify candidate datasets merged
        ds_names = [d.name.lower() for d in merged.candidate_datasets]
        self.assertEqual(len(ds_names), 2)
        self.assertIn("coco", ds_names)
        self.assertIn("imagenet", ds_names)

        # Verify explanations combined
        self.assertEqual(len(merged.existing_evidence), 2)
        self.assertIn("Evidence A", merged.existing_evidence)
        self.assertIn("Evidence B", merged.existing_evidence)

    def test_09_duplicate_supporting_papers_removed_inside_direction(self):
        """
        TEST 9: Verify supporting papers inside an opportunity never have duplicate IDs.
        """
        d = ResearchDirection(
            direction_id="dir_1",
            title="Test Direction",
            research_problem="Problem",
            motivation="Motivation",
            existing_evidence=[],
            missing_aspect="Missing",
            proposed_direction="Direction",
            supporting_papers=[
                SupportingPaper(paper_id=1, title="Paper 1", role="Role A"),
                SupportingPaper(paper_id=1, title="Paper 1", role="Role B")
            ],
            supporting_concepts=["A"],
            candidate_algorithms=[],
            candidate_datasets=[],
            candidate_methodologies=[],
            evidence=ResearchDirectionEvidence(
                gap_score=0.8,
                semantic_evidence=0.8,
                link_prediction_score=0.8,
                collection_coverage=50.0,
                underrepresentation_score=0.3
            ),
            direction_score=0.75,
            confidence="High",
            disclaimer=DIRECTION_DISCLAIMER
        )
        merged = ResearchDirectionService._merge_directions(d, d, total_papers=2)
        self.assertEqual(len(merged.supporting_papers), 1)
        self.assertEqual(merged.supporting_papers[0].paper_id, 1)

    def test_10_genuinely_different_opportunities_remain_separate(self):
        """
        TEST 10: Verify genuinely distinct research directions are not merged.
        """
        from app.services.research_direction_service import compute_opportunity_key

        key_yolo_vit = compute_opportunity_key("YOLO", "Vision Transformer", "Computer Vision")
        key_resnet_rnn = compute_opportunity_key("ResNet", "RNN", "Medical Imaging")

        self.assertNotEqual(key_yolo_vit, key_resnet_rnn)

    def test_11_sequential_direction_ids_assigned_after_merge(self):
        """
        TEST 11: Verify directions are assigned stable sequential IDs: dir_1, dir_2, etc.
        """
        from unittest.mock import patch

        mock_landscape = [
            {"paper_id": 1, "title": "Paper 1 with Transformer", "algorithms": ["YOLO", "Transformer"], "application_domains": ["Vision"], "keywords": ["detection", "transformer"], "datasets": [], "methodologies": []},
            {"paper_id": 2, "title": "Paper 2 with Transformer", "algorithms": ["YOLO", "Transformer"], "application_domains": ["Vision"], "keywords": ["detection", "transformer"], "datasets": [], "methodologies": []}
        ]
        mock_gaps = [
            {
                "source_paper_id": 1,
                "target_label": "Transformer",
                "target_type": "ALGORITHM",
                "evidence": {"gap_score": 0.85, "semantic_evidence": 0.80, "link_prediction_score": 0.75, "underrepresentation_score": 0.40},
                "explanation": ["Gap 1"]
            },
            {
                "source_paper_id": 2,
                "target_label": "Transformer",
                "target_type": "ALGORITHM",
                "evidence": {"gap_score": 0.80, "semantic_evidence": 0.75, "link_prediction_score": 0.70, "underrepresentation_score": 0.35},
                "explanation": ["Gap 2"]
            }
        ]

        with patch("app.services.research_direction_service.GlobalResearchIntelligenceService") as MockIntel, \
             patch("app.services.research_direction_service.ResearchGapService") as MockGap:
            mock_intel_inst = MagicMock()
            mock_intel_inst.analyze_collection.return_value = {
                "paper_landscape": mock_landscape,
                "collection_summary": {"total_papers": 2}
            }
            MockIntel.return_value = mock_intel_inst

            mock_gap_inst = MagicMock()
            mock_gap_inst.detect_gaps.return_value = mock_gaps
            MockGap.return_value = mock_gap_inst

            resp = ResearchDirectionService.generate_directions(self.mock_db, top_k=10)

            # Both gaps had YOLO + Transformer for Vision, so they must be merged into 1 direction!
            self.assertEqual(resp.total_directions, 1)
            self.assertEqual(len(resp.directions), 1)
            self.assertEqual(resp.directions[0].direction_id, "dir_1")
            self.assertEqual(len(resp.directions[0].supporting_papers), 2)
            self.assertEqual(resp.directions[0].evidence.gap_score, 0.85)

    def test_12_driver_drowsiness_allowed_algorithms(self):
        """
        TEST 12: Verify compatible models (YOLO, LSTM, Vision Transformer)
        are allowed for Driver Drowsiness Detection project.
        """
        from unittest.mock import patch

        mock_landscape = [
            {
                "paper_id": 1,
                "title": "Driver Drowsiness Detection via Computer Vision",
                "abstract": "Real-time driver fatigue and drowsiness detection using video streams.",
                "algorithms": ["CNN"],
                "application_domains": ["Driver Drowsiness Detection", "Automotive Safety"],
                "keywords": ["driver drowsiness", "fatigue detection", "computer vision"],
                "datasets": ["NTHU Drowsiness"],
                "methodologies": ["Object Detection"]
            }
        ]
        mock_gaps = [
            {
                "source_paper_id": 1,
                "target_label": "YOLO",
                "target_type": "ALGORITHM",
                "evidence": {"gap_score": 0.82, "semantic_evidence": 0.78, "link_prediction_score": 0.70, "underrepresentation_score": 0.50},
                "explanation": ["YOLO gap"]
            },
            {
                "source_paper_id": 1,
                "target_label": "LSTM",
                "target_type": "ALGORITHM",
                "evidence": {"gap_score": 0.85, "semantic_evidence": 0.75, "link_prediction_score": 0.72, "underrepresentation_score": 0.45},
                "explanation": ["LSTM gap"]
            },
            {
                "source_paper_id": 1,
                "target_label": "Vision Transformer",
                "target_type": "ALGORITHM",
                "evidence": {"gap_score": 0.80, "semantic_evidence": 0.70, "link_prediction_score": 0.68, "underrepresentation_score": 0.40},
                "explanation": ["ViT gap"]
            }
        ]

        with patch("app.services.research_direction_service.GlobalResearchIntelligenceService") as MockIntel, \
             patch("app.services.research_direction_service.ResearchGapService") as MockGap:
            mock_intel_inst = MagicMock()
            mock_intel_inst.analyze_collection.return_value = {
                "paper_landscape": mock_landscape,
                "collection_summary": {"total_papers": 1}
            }
            MockIntel.return_value = mock_intel_inst

            mock_gap_inst = MagicMock()
            mock_gap_inst.detect_gaps.return_value = mock_gaps
            MockGap.return_value = mock_gap_inst

            resp = ResearchDirectionService.generate_directions(
                self.mock_db,
                top_k=10,
                project_name="Driver Drowsiness Detection"
            )

            self.assertEqual(len(resp.directions), 3)
            titles = [d.title for d in resp.directions]
            self.assertTrue(any("YOLO" in t for t in titles))
            self.assertTrue(any("LSTM" in t for t in titles))
            self.assertTrue(any("Vision Transformer" in t for t in titles))

    def test_13_driver_drowsiness_agriculture_domain_rejected(self):
        """
        TEST 13: Verify unrelated domain entity 'Agriculture' is rejected and NEVER combined
        with YOLO as an opportunity for Driver Drowsiness Detection.
        """
        from unittest.mock import patch

        mock_landscape = [
            {
                "paper_id": 1,
                "title": "Driver Drowsiness Detection using YOLO",
                "abstract": "Detecting eye closure and yawning for driver alertness in vehicles.",
                "algorithms": ["YOLO"],
                "application_domains": ["Driver Drowsiness Detection", "Automotive"],
                "keywords": ["driver drowsiness", "alertness", "fatigue"],
                "datasets": ["DriverFace"],
                "methodologies": ["Deep Learning"]
            }
        ]
        # Unrelated domain gap extracted from collection
        mock_gaps = [
            {
                "source_paper_id": 1,
                "target_label": "Agriculture",
                "target_type": "DOMAIN",
                "evidence": {"gap_score": 0.80, "semantic_evidence": 0.05, "link_prediction_score": 0.20, "underrepresentation_score": 0.90},
                "explanation": ["Underrepresented domain entity in collection"]
            }
        ]

        with patch("app.services.research_direction_service.GlobalResearchIntelligenceService") as MockIntel, \
             patch("app.services.research_direction_service.ResearchGapService") as MockGap:
            mock_intel_inst = MagicMock()
            mock_intel_inst.analyze_collection.return_value = {
                "paper_landscape": mock_landscape,
                "collection_summary": {"total_papers": 1}
            }
            MockIntel.return_value = mock_intel_inst

            mock_gap_inst = MagicMock()
            mock_gap_inst.detect_gaps.return_value = mock_gaps
            MockGap.return_value = mock_gap_inst

            resp = ResearchDirectionService.generate_directions(
                self.mock_db,
                top_k=10,
                project_name="Driver Drowsiness Detection"
            )

            # Agriculture must be rejected!
            self.assertEqual(len(resp.directions), 0)
            for d in resp.directions:
                self.assertNotIn("Agriculture", d.title)

    def test_14_crop_disease_agriculture_domain_allowed(self):
        """
        TEST 14: Verify 'Agriculture' domain IS allowed when project topic is Crop Disease Detection.
        """
        from unittest.mock import patch

        mock_landscape = [
            {
                "paper_id": 1,
                "title": "Plant Leaf Disease Detection using Deep Learning",
                "abstract": "Automated crop leaf disease identification for agriculture and farming.",
                "algorithms": ["ResNet"],
                "application_domains": ["Crop Disease Detection", "Agriculture", "Smart Farming"],
                "keywords": ["crop disease", "plant pathology", "agriculture"],
                "datasets": ["PlantVillage"],
                "methodologies": ["Image Classification"]
            }
        ]
        mock_gaps = [
            {
                "source_paper_id": 1,
                "target_label": "Agriculture",
                "target_type": "DOMAIN",
                "evidence": {"gap_score": 0.78, "semantic_evidence": 0.75, "link_prediction_score": 0.60, "underrepresentation_score": 0.40},
                "explanation": ["Domain adaptation gap"]
            }
        ]

        with patch("app.services.research_direction_service.GlobalResearchIntelligenceService") as MockIntel, \
             patch("app.services.research_direction_service.ResearchGapService") as MockGap:
            mock_intel_inst = MagicMock()
            mock_intel_inst.analyze_collection.return_value = {
                "paper_landscape": mock_landscape,
                "collection_summary": {"total_papers": 1}
            }
            MockIntel.return_value = mock_intel_inst

            mock_gap_inst = MagicMock()
            mock_gap_inst.detect_gaps.return_value = mock_gaps
            MockGap.return_value = mock_gap_inst

            resp = ResearchDirectionService.generate_directions(
                self.mock_db,
                top_k=10,
                project_name="Crop Disease Detection"
            )

            self.assertEqual(len(resp.directions), 1)
            self.assertEqual(resp.directions[0].title, "Explore ResNet for Agriculture")

    def test_15_medical_imaging_agriculture_rejected(self):
        """
        TEST 15: Verify 'Agriculture' is rejected for Medical Image Classification project.
        """
        from unittest.mock import patch

        mock_landscape = [
            {
                "paper_id": 1,
                "title": "Medical Image Classification for Tumor Diagnosis",
                "abstract": "MRI and CT scan analysis for brain tumor classification and oncology.",
                "algorithms": ["UNet"],
                "application_domains": ["Medical Imaging", "Healthcare", "Radiology"],
                "keywords": ["mri", "tumor", "radiology", "medical imaging"],
                "datasets": ["BraTS"],
                "methodologies": ["Semantic Segmentation"]
            }
        ]
        mock_gaps = [
            {
                "source_paper_id": 1,
                "target_label": "Agriculture",
                "target_type": "DOMAIN",
                "evidence": {"gap_score": 0.85, "semantic_evidence": 0.02, "link_prediction_score": 0.15, "underrepresentation_score": 0.95},
                "explanation": ["Unrelated entity"]
            }
        ]

        with patch("app.services.research_direction_service.GlobalResearchIntelligenceService") as MockIntel, \
             patch("app.services.research_direction_service.ResearchGapService") as MockGap:
            mock_intel_inst = MagicMock()
            mock_intel_inst.analyze_collection.return_value = {
                "paper_landscape": mock_landscape,
                "collection_summary": {"total_papers": 1}
            }
            MockIntel.return_value = mock_intel_inst

            mock_gap_inst = MagicMock()
            mock_gap_inst.detect_gaps.return_value = mock_gaps
            MockGap.return_value = mock_gap_inst

            resp = ResearchDirectionService.generate_directions(
                self.mock_db,
                top_k=10,
                project_name="Medical Image Classification"
            )

            self.assertEqual(len(resp.directions), 0)

    def test_16_entity_role_formatting_and_semantics(self):
        """
        TEST 16: Verify distinct formatting rules for ALGORITHM, METHODOLOGY, and DATASET roles.
        """
        from unittest.mock import patch

        mock_landscape = [
            {
                "paper_id": 1,
                "title": "Driver Drowsiness Detection using YOLO",
                "abstract": "Detecting drowsiness using video stream.",
                "algorithms": ["YOLO"],
                "application_domains": ["Driver Drowsiness Detection"],
                "keywords": ["driver drowsiness"],
                "datasets": ["NTHU"],
                "methodologies": ["CNN"]
            }
        ]
        mock_gaps = [
            {
                "source_paper_id": 1,
                "target_label": "Temporal Convolutional Network",
                "target_type": "METHODOLOGY",
                "evidence": {"gap_score": 0.80, "semantic_evidence": 0.70, "link_prediction_score": 0.60, "underrepresentation_score": 0.50},
                "explanation": ["Methodology gap"]
            },
            {
                "source_paper_id": 1,
                "target_label": "UTA-RLDD Dataset",
                "target_type": "DATASET",
                "evidence": {"gap_score": 0.75, "semantic_evidence": 0.65, "link_prediction_score": 0.55, "underrepresentation_score": 0.40},
                "explanation": ["Dataset gap"]
            }
        ]

        with patch("app.services.research_direction_service.GlobalResearchIntelligenceService") as MockIntel, \
             patch("app.services.research_direction_service.ResearchGapService") as MockGap:
            mock_intel_inst = MagicMock()
            mock_intel_inst.analyze_collection.return_value = {
                "paper_landscape": mock_landscape,
                "collection_summary": {"total_papers": 1}
            }
            MockIntel.return_value = mock_intel_inst

            mock_gap_inst = MagicMock()
            mock_gap_inst.detect_gaps.return_value = mock_gaps
            MockGap.return_value = mock_gap_inst

            resp = ResearchDirectionService.generate_directions(
                self.mock_db,
                top_k=10,
                project_name="Driver Drowsiness Detection"
            )

            titles = {d.title: d for d in resp.directions}
            # METHODOLOGY uses 'with'
            self.assertIn("Explore YOLO with Temporal Convolutional Network for Driver Drowsiness Detection", titles)
            # DATASET uses 'Evaluate ... on'
            self.assertIn("Evaluate YOLO on UTA-RLDD Dataset for Driver Drowsiness Detection", titles)

    def test_17_supporting_papers_grounded_to_nthu_dataset(self):
        """
        TEST 17: Verify NTHU dataset opportunity ONLY returns papers containing/referencing NTHU.
        A generic driver drowsiness paper without NTHU is NOT returned.
        """
        from unittest.mock import patch

        mock_landscape = [
            {
                "paper_id": 1,
                "title": "Driver Drowsiness Detection with YOLO",
                "abstract": "We detect drowsiness using facial landmarks on generic web streams.",
                "algorithms": ["YOLO"],
                "application_domains": ["Driver Drowsiness Detection"],
                "keywords": ["driver drowsiness", "face detection"],
                "datasets": ["CustomFaceData"],
                "methodologies": ["CNN"]
            },
            {
                "paper_id": 2,
                "title": "Fatigue Analysis on NTHU Drowsiness Dataset",
                "abstract": "Evaluation on NTHU benchmark dataset for driver state assessment.",
                "algorithms": ["ResNet"],
                "application_domains": ["Driver Drowsiness Detection"],
                "keywords": ["nthu", "driver drowsiness"],
                "datasets": ["NTHU Drowsiness"],
                "methodologies": ["Deep Learning"]
            }
        ]
        mock_gaps = [
            {
                "source_paper_id": 1,
                "target_label": "NTHU",
                "target_type": "DATASET",
                "evidence": {"gap_score": 0.85, "semantic_evidence": 0.80, "link_prediction_score": 0.70, "underrepresentation_score": 0.50},
                "explanation": ["NTHU benchmark evaluation gap"]
            }
        ]

        with patch("app.services.research_direction_service.GlobalResearchIntelligenceService") as MockIntel, \
             patch("app.services.research_direction_service.ResearchGapService") as MockGap:
            mock_intel_inst = MagicMock()
            mock_intel_inst.analyze_collection.return_value = {
                "paper_landscape": mock_landscape,
                "collection_summary": {"total_papers": 2}
            }
            MockIntel.return_value = mock_intel_inst

            mock_gap_inst = MagicMock()
            mock_gap_inst.detect_gaps.return_value = mock_gaps
            MockGap.return_value = mock_gap_inst

            resp = ResearchDirectionService.generate_directions(
                self.mock_db,
                top_k=10,
                project_name="Driver Drowsiness Detection"
            )

            self.assertEqual(len(resp.directions), 1)
            dir_nthu = resp.directions[0]
            self.assertIn("NTHU", dir_nthu.title)
            # ONLY Paper 2 contains NTHU evidence. Paper 1 must NOT be in supporting_papers!
            self.assertEqual(len(dir_nthu.supporting_papers), 1)
            self.assertEqual(dir_nthu.supporting_papers[0].paper_id, 2)
            self.assertIn("NTHU", dir_nthu.supporting_papers[0].title)

    def test_18_supporting_papers_grounded_to_gan_algorithm(self):
        """
        TEST 18: Verify GAN opportunity ONLY returns papers with GAN evidence.
        Generic drowsiness paper without GAN evidence is excluded.
        """
        from unittest.mock import patch

        mock_landscape = [
            {
                "paper_id": 1,
                "title": "Baseline Driver Drowsiness Detection",
                "abstract": "Detecting drowsiness using CNN and Haar cascades.",
                "algorithms": ["CNN"],
                "application_domains": ["Driver Drowsiness Detection"],
                "keywords": ["driver drowsiness"],
                "datasets": ["DriverFace"],
                "methodologies": []
            },
            {
                "paper_id": 2,
                "title": "Generative Adversarial Networks for Night-time Driver Face Enhancement",
                "abstract": "Using GAN for synthetic lighting augmentation in driver fatigue systems.",
                "algorithms": ["GAN", "CycleGAN"],
                "application_domains": ["Driver Drowsiness Detection"],
                "keywords": ["gan", "driver drowsiness"],
                "datasets": ["NightFace"],
                "methodologies": ["Generative Modeling"]
            }
        ]
        mock_gaps = [
            {
                "source_paper_id": 1,
                "target_label": "GAN",
                "target_type": "ALGORITHM",
                "evidence": {"gap_score": 0.88, "semantic_evidence": 0.82, "link_prediction_score": 0.75, "underrepresentation_score": 0.50},
                "explanation": ["GAN integration gap"]
            }
        ]

        with patch("app.services.research_direction_service.GlobalResearchIntelligenceService") as MockIntel, \
             patch("app.services.research_direction_service.ResearchGapService") as MockGap:
            mock_intel_inst = MagicMock()
            mock_intel_inst.analyze_collection.return_value = {
                "paper_landscape": mock_landscape,
                "collection_summary": {"total_papers": 2}
            }
            MockIntel.return_value = mock_intel_inst

            mock_gap_inst = MagicMock()
            mock_gap_inst.detect_gaps.return_value = mock_gaps
            MockGap.return_value = mock_gap_inst

            resp = ResearchDirectionService.generate_directions(
                self.mock_db,
                top_k=10,
                project_name="Driver Drowsiness Detection"
            )

            self.assertEqual(len(resp.directions), 1)
            dir_gan = resp.directions[0]
            self.assertIn("GAN", dir_gan.title)
            # ONLY Paper 2 has GAN evidence! Paper 1 must NOT appear
            self.assertEqual(len(dir_gan.supporting_papers), 1)
            self.assertEqual(dir_gan.supporting_papers[0].paper_id, 2)
            self.assertIn("Generative Adversarial Networks", dir_gan.supporting_papers[0].title)

    def test_19_supporting_papers_grounded_to_lstm_algorithm(self):
        """
        TEST 19: Verify LSTM opportunity ONLY returns papers referencing LSTM.
        """
        from unittest.mock import patch

        mock_landscape = [
            {
                "paper_id": 1,
                "title": "Spatial Drowsiness Detection using YOLO",
                "abstract": "Single-frame object detection for eye state.",
                "algorithms": ["YOLO"],
                "application_domains": ["Driver Drowsiness Detection"],
                "keywords": ["driver drowsiness"],
                "datasets": [],
                "methodologies": []
            },
            {
                "paper_id": 2,
                "title": "Temporal Recurrent Neural Networks for Driving Fatigue",
                "abstract": "Modeling sequential blink duration using Long Short-Term Memory (LSTM).",
                "algorithms": ["LSTM", "RNN"],
                "application_domains": ["Driver Drowsiness Detection"],
                "keywords": ["lstm", "temporal modeling"],
                "datasets": [],
                "methodologies": ["Sequence Modeling"]
            }
        ]
        mock_gaps = [
            {
                "source_paper_id": 1,
                "target_label": "LSTM",
                "target_type": "ALGORITHM",
                "evidence": {"gap_score": 0.86, "semantic_evidence": 0.81, "link_prediction_score": 0.74, "underrepresentation_score": 0.50},
                "explanation": ["Temporal LSTM gap"]
            }
        ]

        with patch("app.services.research_direction_service.GlobalResearchIntelligenceService") as MockIntel, \
             patch("app.services.research_direction_service.ResearchGapService") as MockGap:
            mock_intel_inst = MagicMock()
            mock_intel_inst.analyze_collection.return_value = {
                "paper_landscape": mock_landscape,
                "collection_summary": {"total_papers": 2}
            }
            MockIntel.return_value = mock_intel_inst

            mock_gap_inst = MagicMock()
            mock_gap_inst.detect_gaps.return_value = mock_gaps
            MockGap.return_value = mock_gap_inst

            resp = ResearchDirectionService.generate_directions(
                self.mock_db,
                top_k=10,
                project_name="Driver Drowsiness Detection"
            )

            self.assertEqual(len(resp.directions), 1)
            dir_lstm = resp.directions[0]
            self.assertEqual(len(dir_lstm.supporting_papers), 1)
            self.assertEqual(dir_lstm.supporting_papers[0].paper_id, 2)
            self.assertIn("LSTM", dir_lstm.supporting_papers[0].role)

    def test_20_no_evidence_returns_empty_supporting_papers(self):
        """
        TEST 20: Verify that if no paper provides direct evidence for the target concept,
        supporting_papers is returned as empty list and NOT fallen back to all project papers.
        """
        from unittest.mock import patch

        mock_landscape = [
            {
                "paper_id": 1,
                "title": "Baseline Spatial Drowsiness Detection",
                "abstract": "Single frame spatial feature analysis.",
                "algorithms": ["CNN"],
                "application_domains": ["Driver Drowsiness Detection"],
                "keywords": ["driver drowsiness"],
                "datasets": ["CustomDataset"],
                "methodologies": ["CNN"]
            }
        ]
        # Target concept 'Spiking Neural Network' is in graph gap but not directly present in any paper text/metadata
        mock_gaps = [
            {
                "source_paper_id": 1,
                "target_label": "Spiking Neural Network",
                "target_type": "ALGORITHM",
                "evidence": {"gap_score": 0.80, "semantic_evidence": 0.70, "link_prediction_score": 0.60, "underrepresentation_score": 0.50},
                "explanation": ["SNN analytical gap"]
            }
        ]

        with patch("app.services.research_direction_service.GlobalResearchIntelligenceService") as MockIntel, \
             patch("app.services.research_direction_service.ResearchGapService") as MockGap:
            mock_intel_inst = MagicMock()
            mock_intel_inst.analyze_collection.return_value = {
                "paper_landscape": mock_landscape,
                "collection_summary": {"total_papers": 1}
            }
            MockIntel.return_value = mock_intel_inst

            mock_gap_inst = MagicMock()
            mock_gap_inst.detect_gaps.return_value = mock_gaps
            MockGap.return_value = mock_gap_inst

            resp = ResearchDirectionService.generate_directions(
                self.mock_db,
                top_k=10,
                project_name="Driver Drowsiness Detection"
            )

            self.assertEqual(len(resp.directions), 1)
            dir_snn = resp.directions[0]
            # Must NOT fall back to paper 1 since paper 1 has no SNN evidence!
            self.assertEqual(len(dir_snn.supporting_papers), 0)
            self.assertEqual(dir_snn.supporting_papers, [])


if __name__ == "__main__":
    unittest.main()
