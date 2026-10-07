import sys
import unittest
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.metadata_extractor import (
    MetadataExtractor,
    DatasetExtractor,
    AlgorithmExtractor,
    MethodologyExtractor,
    KeywordExtractor,
    is_grammatical_noise_or_fragment
)
from app.database.session import SessionLocal
from app.models.paper_model import ResearchPaper
from app.models.project_model import ResearchProject
from app.services.project_intelligence_service import ProjectIntelligenceService


class TestPaperMetadataProvenanceRegression(unittest.TestCase):

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    # TEST A: PlantDoc is extracted from Paper 14 when actually used.
    def test_A_plantdoc_extracted_from_paper_14(self):
        p14 = self.db.query(ResearchPaper).filter(ResearchPaper.id == 14).first()
        if p14:
            meta = MetadataExtractor.extract(p14.title, p14.abstract, p14.full_text)
            self.assertIn("PlantDoc", meta["datasets"], "PlantDoc must be detected in Paper 14 datasets.")
            exp_ds = [d for d in meta.get("dataset_details", []) if d["name"] == "PlantDoc"]
            self.assertTrue(len(exp_ds) > 0, "PlantDoc detail must exist.")
            self.assertEqual(exp_ds[0]["role"], "experimental", "PlantDoc in Paper 14 must have role experimental.")

    # TEST B: Swin-Axial Transformer is classified as PRIMARY for Paper 15.
    def test_B_swin_axial_transformer_is_primary_for_paper_15(self):
        p15 = self.db.query(ResearchPaper).filter(ResearchPaper.id == 15).first()
        if p15:
            meta = MetadataExtractor.extract(p15.title, p15.abstract, p15.full_text)
            self.assertIn("Swin-Axial Transformer", meta["algorithms"])
            algo_details = meta.get("algorithm_details", [])
            primary = [a for a in algo_details if a["name"] == "Swin-Axial Transformer"]
            self.assertTrue(len(primary) > 0)
            self.assertEqual(primary[0]["role"], "primary", "Swin-Axial Transformer must be classified as PRIMARY.")

    # TEST C: Comparison/reference models are not incorrectly promoted to PRIMARY.
    def test_C_comparison_models_not_promoted_to_primary(self):
        sample_text = (
            "Plant Disease Detection Using an Innovative Swin-Axial Transformer. "
            "We compare our proposed model with baseline models such as ResNet, DenseNet, and CNN."
        )
        meta = MetadataExtractor.extract("Plant Disease Detection Using an Innovative Swin-Axial Transformer", "Abstract", sample_text)
        algo_details = meta.get("algorithm_details", [])
        resnet = next((a for a in algo_details if a["name"] == "ResNet"), None)
        cnn = next((a for a in algo_details if a["name"] == "CNN"), None)
        if resnet:
            self.assertNotEqual(resnet["role"], "primary", "Comparison model ResNet must not be promoted to PRIMARY.")
        if cnn:
            self.assertNotEqual(cnn["role"], "primary", "Comparison model CNN must not be promoted to PRIMARY.")

    # TEST D: PlantDoc and PlantDoc Dataset normalize to the same canonical dataset.
    def test_D_plantdoc_alias_normalization(self):
        t1 = "PlantDoc Dataset for Plant Pathology"
        meta1 = MetadataExtractor.extract("Paper 1", "Abstract", t1)
        meta2 = MetadataExtractor.extract("Paper 2", "Abstract", "Experiments evaluated on PlantDoc.")
        self.assertIn("PlantDoc", meta1["datasets"])
        self.assertIn("PlantDoc", meta2["datasets"])

    # TEST E: Explicit PDF keywords are preferred when available.
    def test_E_explicit_pdf_keywords_preferred(self):
        full_text = (
            "Title of Paper\n"
            "Abstract text...\n"
            "Keywords: Axial Compression, Attention Mechanisms, Computational Efficiency\n"
            "Body of paper..."
        )
        kws = KeywordExtractor.extract_explicit_pdf_keywords(full_text)
        self.assertIn("Axial Compression", kws)
        self.assertIn("Attention Mechanisms", kws)

    # TEST F: Generic prose fragments are rejected as noise.
    def test_F_generic_prose_fragments_rejected(self):
        noise_phrases = [
            "Training Process", "Actual Bounding Boxes", "Detail Enhancement Module",
            "Established Best Practices", "Addressed The Significant", "Plant Species", "General Process"
        ]
        for phrase in noise_phrases:
            self.assertTrue(
                is_grammatical_noise_or_fragment(phrase),
                f"Phrase '{phrase}' must be rejected as noise."
            )

    # TEST G: Dataset mentioned only in related work is not marked experimental.
    def test_G_related_work_dataset_not_experimental(self):
        text = "Prior work introduced the MS COCO dataset for general object detection. In this paper, we evaluate on PlantDoc."
        ds_roles = DatasetExtractor.extract_with_roles(text, "Title", "Abstract")
        coco = next((d for d in ds_roles if d["name"] == "COCO" or d["name"] == "MS COCO"), None)
        if coco:
            self.assertNotEqual(coco["role"], "experimental", "Background mention of COCO should not be experimental.")

    # TEST H: Methodology extraction does not classify generic prose or application goals as methodology.
    def test_H_methodology_filters_generic_prose(self):
        text_sample = "Training Process, Food Security, Actual Bounding Boxes, Detail Enhancement Module, and Established Best Practices were discussed."
        meths = MethodologyExtractor.extract(text_sample)
        self.assertNotIn("Training Process", meths)
        self.assertNotIn("Food Security", meths)
        self.assertNotIn("Detail Enhancement Module", meths)
        self.assertNotIn("Established Best Practices", meths)

    # TEST I: Existing project intelligence service runs cleanly for Project 6.
    def test_I_project_intelligence_service_integrity(self):
        p6 = self.db.query(ResearchProject).filter(ResearchProject.id == 6).first()
        if p6:
            res = ProjectIntelligenceService.analyze_project(project_id=6, db=self.db, refresh=True)
            self.assertGreaterEqual(res.collection_summary.total_papers, 1)

    # TEST J: Research gaps and candidate directions co-exist.
    def test_J_gap_and_direction_coexistence(self):
        p6 = self.db.query(ResearchProject).filter(ResearchProject.id == 6).first()
        if p6:
            res = ProjectIntelligenceService.analyze_project(project_id=6, db=self.db, refresh=True)
            self.assertIsNotNone(res.research_gaps)
            self.assertIsNotNone(res.candidate_research_directions)

    # TEST K: Connections and paper relationships are present.
    def test_K_connections_and_relationships(self):
        p6 = self.db.query(ResearchProject).filter(ResearchProject.id == 6).first()
        if p6:
            res = ProjectIntelligenceService.analyze_project(project_id=6, db=self.db, refresh=True)
            self.assertIsNotNone(res.paper_relationships)

    # TEST L: No fabricated evidence snippets are produced.
    def test_L_no_fabricated_evidence_snippets(self):
        p14 = self.db.query(ResearchPaper).filter(ResearchPaper.id == 14).first()
        if p14:
            meta = MetadataExtractor.extract(p14.title, p14.abstract, p14.full_text)
            for cat in ["algorithm_details", "dataset_details", "methodology_details", "keyword_details"]:
                for item in meta.get(cat, []):
                    snippet = item.get("evidence_text", "")
                    if snippet and not snippet.endswith("extracted from paper text."):
                        self.assertTrue(
                            snippet.lower() in p14.title.lower() or snippet.lower() in (p14.abstract or "").lower() or snippet.lower() in p14.full_text.lower() or item["name"].lower() in p14.full_text.lower(),
                            f"Evidence snippet '{snippet}' for '{item['name']}' must be grounded in actual paper text."
                        )


if __name__ == "__main__":
    unittest.main()
