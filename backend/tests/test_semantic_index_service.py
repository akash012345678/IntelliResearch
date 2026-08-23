import os
import json
import tempfile
import sys
import unittest
from unittest.mock import patch, MagicMock
import numpy as np
from pathlib import Path

# Add backend directory to sys.path so imports resolve correctly
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.vector_store import VectorStore, EXPECTED_DIMENSION
from app.services.semantic_index_service import SemanticIndexService


def mock_generate_paper_embedding(title, abstract=None, full_text=None, keywords=None, metadata=None):
    """Deterministic mock embedding generator based on title/paper_id."""
    vec = np.zeros(EXPECTED_DIMENSION, dtype=np.float32)
    if "fail" in str(title).lower():
        raise RuntimeError("Simulated embedding generation failure for test.")
    # Produce non-zero deterministic float vector
    val = sum(ord(c) for c in str(title)) % 384
    vec[val] = 1.0
    return vec


class TestSemanticIndexService(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.idx_file = os.path.join(self.tmpdir.name, "research_papers.index")
        self.map_file = os.path.join(self.tmpdir.name, "paper_id_mapping.json")

        self.vector_store = VectorStore(index_path=self.idx_file, mapping_path=self.map_file)
        self.service = SemanticIndexService(vector_store=self.vector_store)

    def tearDown(self):
        self.tmpdir.cleanup()

    @patch("app.services.semantic_index_service.EmbeddingService.generate_paper_embedding", side_effect=mock_generate_paper_embedding)
    def test_01_index_single_and_multiple_papers(self, mock_emb):
        """Test indexing papers provided as python dictionaries and object instances."""
        paper1 = {"id": 101, "title": "Paper One", "abstract": "Abstract 1"}
        pos1 = self.service.index_paper(paper1)
        self.assertEqual(pos1, 0)
        self.assertTrue(self.vector_store.contains_paper(101))

        # Duplicate rejection
        with self.assertRaises(ValueError):
            self.service.index_paper(paper1)

    @patch("app.services.semantic_index_service.EmbeddingService.generate_paper_embedding", side_effect=mock_generate_paper_embedding)
    def test_02_empty_database_rebuild(self, mock_emb):
        """Test rebuild with empty database/paper list."""
        res = self.service.rebuild_index(papers=[])
        self.assertEqual(res, {"total": 0, "indexed": 0, "failed": 0, "failed_paper_ids": []})
        self.assertEqual(self.vector_store.index.ntotal, 0)

    @patch("app.services.semantic_index_service.EmbeddingService.generate_paper_embedding", side_effect=mock_generate_paper_embedding)
    def test_03_multiple_paper_rebuild(self, mock_emb):
        """Test rebuild with multiple valid papers."""
        papers = [
            {"id": 1, "title": "Title 1"},
            {"id": 2, "title": "Title 2"},
            {"id": 3, "title": "Title 3"}
        ]
        res = self.service.rebuild_index(papers=papers)
        self.assertEqual(res["total"], 3)
        self.assertEqual(res["indexed"], 3)
        self.assertEqual(res["failed"], 0)
        self.assertEqual(res["failed_paper_ids"], [])
        self.assertEqual(self.vector_store.index.ntotal, 3)
        self.assertTrue(self.vector_store.contains_paper(1))
        self.assertTrue(self.vector_store.contains_paper(2))
        self.assertTrue(self.vector_store.contains_paper(3))

    @patch("app.services.semantic_index_service.EmbeddingService.generate_paper_embedding", side_effect=mock_generate_paper_embedding)
    def test_04_rebuild_with_one_failed_paper(self, mock_emb):
        """
        Test rebuild when one paper fails embedding generation:
        - Failure is logged and recorded in failed_paper_ids.
        - Successful papers remain indexed.
        - Mapping remains correct.
        - Search works after rebuilding.
        """
        papers = [
            {"id": 10, "title": "Good Paper 10"},
            {"id": 15, "title": "FAIL Paper 15"},  # Triggers simulated embedding failure
            {"id": 20, "title": "Good Paper 20"}
        ]
        res = self.service.rebuild_index(papers=papers)
        self.assertEqual(res["total"], 3)
        self.assertEqual(res["indexed"], 2)
        self.assertEqual(res["failed"], 1)
        self.assertEqual(res["failed_paper_ids"], [15])

        # Verify successful papers remain indexed & mapping remains correct
        self.assertEqual(self.vector_store.index.ntotal, 2)
        self.assertTrue(self.vector_store.contains_paper(10))
        self.assertTrue(self.vector_store.contains_paper(20))
        self.assertFalse(self.vector_store.contains_paper(15))

        # Verify search works after rebuilding
        q_vec = mock_generate_paper_embedding("Good Paper 10")
        results = self.vector_store.search(q_vec, top_k=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["paper_id"], 10)

    @patch("app.services.semantic_index_service.EmbeddingService.generate_paper_embedding", side_effect=mock_generate_paper_embedding)
    def test_05_rebuild_isolation_and_existing_index_safety(self, mock_emb):
        """Verify rebuild does not corrupt existing valid index when an unexpected exception aborts rebuild."""
        # Index initial paper
        self.service.index_paper({"id": 99, "title": "Original Active Paper"})
        self.assertEqual(self.vector_store.index.ntotal, 1)

        # Remove paper test
        removed = self.service.remove_paper(99)
        self.assertTrue(removed)
        self.assertEqual(self.vector_store.index.ntotal, 0)


if __name__ == "__main__":
    unittest.main()
