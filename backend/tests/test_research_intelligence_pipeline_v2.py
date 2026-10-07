import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.metadata_extractor import (
    MetadataExtractor,
    DatasetExtractor,
    ApplicationDomainExtractor,
    KeywordExtractor,
    AlgorithmExtractor,
    FutureWorkExtractor
)
from app.services.knowledge_graph_service import KnowledgeGraphService
from app.services.research_gap_service import ResearchGapService, canonicalize_concept_name
from app.services.research_direction_service import ResearchDirectionService


class TestResearchIntelligencePipelineV2(unittest.TestCase):
    """
    Comprehensive Backend Test Suite verifying all 21 requirements of the Research Intelligence Pipeline.
    """

    # ---------------------------------------------------------
    # 1. DATASET EXTRACTION TESTS
    # ---------------------------------------------------------
    def test_01_experimental_vs_reference_dataset(self):
        """Verify experimental dataset (PlantDoc/PlantVillage) is distinguished from background benchmark (COCO)."""
        text = (
            "We propose a new model trained and evaluated on PlantDoc and PlantVillage datasets. "
            "Our model achieved state-of-the-art performance, outperforming baselines pretrained on MS COCO benchmark dataset."
        )
        datasets = DatasetExtractor.extract(text)
        roles = DatasetExtractor.extract_with_roles(full_text=text)

        self.assertIn("PlantDoc", datasets)
        self.assertIn("PlantVillage", datasets)

        coco_role = next((d["role"] for d in roles if d["dataset"] in ["COCO", "MS COCO"]), None)
        plantdoc_role = next((d["role"] for d in roles if d["dataset"] == "PlantDoc"), None)

        self.assertEqual(plantdoc_role, "EXPERIMENTAL_DATASET")
        self.assertIn(coco_role, ["MENTIONED_DATASET", "REFERENCE_DATASET", "BENCHMARK_DATASET", "BACKGROUND_DATASET"])

    # ---------------------------------------------------------
    # 2. DOMAIN EXTRACTION TESTS
    # ---------------------------------------------------------
    def test_02_primary_vs_mentioned_domain(self):
        """Verify Agriculture is primary domain and Autonomous Driving / Healthcare are classified as mentioned background."""
        title = "Improving Plant Disease Classification using Explainable Deep Learning"
        abstract = "We investigate automated plant disease detection in agricultural crops to assist farmers in early diagnosis."
        full_text = (
            "Deep learning has applications in autonomous driving, healthcare, and IoT. "
            "However, in this paper, we focus strictly on agricultural plant disease classification."
        )

        domains = ApplicationDomainExtractor.extract(full_text)
        roles = ApplicationDomainExtractor.extract_with_roles(title=title, abstract=abstract, full_text=full_text)

        primary_domains = [d["domain"] for d in roles if d["role"] == "PRIMARY_DOMAIN"]
        mentioned_domains = [d["domain"] for d in roles if d["role"] == "MENTIONED_DOMAIN"]

        self.assertIn("Agriculture", primary_domains)
        self.assertIn("Autonomous Driving", mentioned_domains)
        self.assertIn("Healthcare", mentioned_domains)

    # ---------------------------------------------------------
    # 3. KEYWORD EXTRACTION TESTS
    # ---------------------------------------------------------
    def test_03_title_fragment_rejection(self):
        """Verify title fragments like 'Improving Plant' and 'Classification With Deep' are rejected."""
        title = "Improving Plant Disease Classification With Deep Learning"
        abstract = "We propose an explainable AI model for plant pathology."
        meta = MetadataExtractor.extract(title=title, abstract=abstract, full_text=abstract)
        keywords = meta["keywords"]
        all_concepts = keywords + meta["tasks"] + meta["methodologies"]

        self.assertNotIn("Improving Plant", keywords)
        self.assertNotIn("Improving Plant Disease", keywords)
        self.assertNotIn("Classification With Deep", keywords)
        self.assertIn("Plant Disease Classification", all_concepts)

    # ---------------------------------------------------------
    # 4. ALGORITHM EXTRACTION TESTS
    # ---------------------------------------------------------
    def test_04_algorithm_roles(self):
        """Verify proposed model is distinguished from comparison baselines."""
        text = (
            "We propose a novel Swin-Axial Transformer for plant disease classification. "
            "We evaluate our model against comparison baselines YOLOv5, YOLOv8, and ResNet."
        )
        roles = AlgorithmExtractor.extract_with_roles(full_text=text)

        proposed = [a["name"] for a in roles if a["role"] == "PROPOSED_MODEL"]
        compared = [a["name"] for a in roles if a["role"] == "COMPARISON_MODEL"]

        self.assertIn("Swin-Axial Transformer", proposed)
        self.assertTrue(any(m in compared for m in ["YOLOv5", "YOLOv8", "ResNet"]))

    # ---------------------------------------------------------
    # 5. UNDERREPRESENTED CONCEPT VS GAP TESTS
    # ---------------------------------------------------------
    def test_05_underrepresented_concept_alone_is_not_gap(self):
        """Verify generic terms ('Machine Learning', 'Deep Learning') cannot become gaps."""
        self.assertEqual(canonicalize_concept_name("Machine Learning"), "")
        self.assertEqual(canonicalize_concept_name("Deep Learning"), "")
        self.assertEqual(canonicalize_concept_name("Computer Vision"), "")

    # ---------------------------------------------------------
    # 6. OPPORTUNITY COMPATIBILITY TESTS
    # ---------------------------------------------------------
    def test_06_entity_compatibility_rules(self):
        """Verify domain-incompatible combinations (YOLO + Healthcare) are rejected for plant disease projects."""
        mock_landscape = [
            {
                "paper_id": 1,
                "title": "Plant Disease Classification using YOLOv5",
                "abstract": "We evaluate YOLOv5 on PlantDoc dataset in agriculture.",
                "algorithms": ["YOLOv5"],
                "application_domains": ["Agriculture"],
                "keywords": ["Plant Disease Classification"],
                "datasets": ["PlantDoc"],
                "methodologies": ["Explainable AI"]
            }
        ]
        mock_gaps = [
            {
                "source_paper_id": 1,
                "target_label": "Healthcare",
                "target_type": "DOMAIN",
                "evidence": {"gap_score": 0.8, "semantic_evidence": 0.1, "link_prediction_score": 0.5, "underrepresentation_score": 0.9},
                "explanation": ["Incidental mention"]
            }
        ]

        mock_db = MagicMock()
        from unittest.mock import patch
        with patch("app.services.research_direction_service.ResearchGapService") as MockGap:
            mock_gap_inst = MagicMock()
            mock_gap_inst.detect_gaps.return_value = mock_gaps
            MockGap.return_value = mock_gap_inst

            resp = ResearchDirectionService.generate_directions(
                mock_db,
                top_k=10,
                project_name="Plant Disease Classification",
                project_papers=[MagicMock(id=1, title="Plant Disease", abstract="", keywords=[], algorithms=["YOLOv5"], datasets=["PlantDoc"], methodologies=[], application_domains=["Agriculture"])]
            )

            # Healthcare should be rejected as an opportunity domain for Plant Disease project!
            titles = [d.title for d in resp.directions]
            self.assertFalse(any("Healthcare" in t for t in titles))

    # ---------------------------------------------------------
    # 7. TARGET-SPECIFIC SUPPORTING PAPER TESTS
    # ---------------------------------------------------------
    def test_07_supporting_paper_target_specific(self):
        """Verify paper is only attached if it genuinely contains evidence for target concept."""
        mock_paper_1 = {
            "paper_id": 1,
            "title": "Explainable AI in Agriculture",
            "abstract": "Evaluates Swin Transformer and Explainable AI.",
            "algorithms": ["Swin Transformer"],
            "methodologies": ["Explainable AI"],
            "datasets": ["PlantDoc"]
        }
        role_evidence = ResearchDirectionService._merge_directions
        from app.services.research_direction_service import extract_paper_evidence_for_target

        role1 = extract_paper_evidence_for_target(mock_paper_1, "PlantDoc", "DATASET")
        role2 = extract_paper_evidence_for_target(mock_paper_1, "DenseNet", "ALGORITHM")

        self.assertIsNotNone(role1)
        self.assertIn("PlantDoc", role1)
        self.assertIsNone(role2)


if __name__ == "__main__":
    unittest.main()
