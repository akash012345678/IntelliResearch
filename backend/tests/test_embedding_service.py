import unittest
import math
import sys
from pathlib import Path

# Add backend directory to sys.path so imports resolve
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.embedding_service import EmbeddingService, EXPECTED_DIMENSION


class TestEmbeddingService(unittest.TestCase):

    def test_01_singleton_model_loading(self):
        """Verify model is loaded as a singleton instance."""
        model1 = EmbeddingService.get_model()
        model2 = EmbeddingService.get_model()
        self.assertIsNotNone(model1)
        self.assertIs(model1, model2, "Model instance must be identical (singleton).")

    def test_02_generate_embedding_dimension_and_norm(self):
        """Verify generated embedding vector dimension (384) and L2 normalization."""
        sample_text = "Artificial Intelligence and Machine Learning in Academic Research Discovery."
        embedding = EmbeddingService.generate_embedding(sample_text)

        self.assertIsInstance(embedding, list)
        self.assertEqual(len(embedding), EXPECTED_DIMENSION, f"Dimension must be {EXPECTED_DIMENSION}.")

        # Check L2 unit norm: sqrt(sum(x^2)) approx equal to 1.0
        l2_norm = math.sqrt(sum(x ** 2 for x in embedding))
        self.assertAlmostEqual(l2_norm, 1.0, places=4, msg="Embedding vector must be L2 normalized.")

    def test_03_generate_paper_embedding_full_structured(self):
        """Verify generate_paper_embedding with complete title, abstract, keywords, and metadata."""
        title = "Graph Neural Networks for Research Gap Analysis"
        abstract = "This paper presents a novel approach for identifying research gaps using GraphRAG and semantic vectors."
        keywords = ["Graph Neural Networks", "Semantic Vectors", "Research Gap"]
        metadata = {
            "algorithms": ["GCN", "MiniLM"],
            "datasets": ["arXiv CS"],
            "methodologies": ["Supervised Learning"],
            "application_domains": ["Bibliometrics"]
        }

        embedding = EmbeddingService.generate_paper_embedding(
            title=title,
            abstract=abstract,
            keywords=keywords,
            metadata=metadata
        )

        self.assertIsInstance(embedding, list)
        self.assertEqual(len(embedding), EXPECTED_DIMENSION)
        l2_norm = math.sqrt(sum(x ** 2 for x in embedding))
        self.assertAlmostEqual(l2_norm, 1.0, places=4)

    def test_04_generate_paper_embedding_missing_abstract_fallback(self):
        """Verify fallback behavior using full_text snippet when abstract is missing."""
        title = "Unsupervised Clustering of Academic Papers"
        full_text = "Introduction: In this study we explore text clustering... " * 30  # >500 chars

        embedding = EmbeddingService.generate_paper_embedding(
            title=title,
            abstract=None,
            full_text=full_text
        )

        self.assertIsInstance(embedding, list)
        self.assertEqual(len(embedding), EXPECTED_DIMENSION)

    def test_05_empty_input_fallback(self):
        """Verify empty string returns zero vector of 384 dimensions."""
        embedding = EmbeddingService.generate_embedding("")
        self.assertEqual(len(embedding), EXPECTED_DIMENSION)
        self.assertTrue(all(x == 0.0 for x in embedding), "Empty text must produce a zero vector.")


if __name__ == "__main__":
    unittest.main()
