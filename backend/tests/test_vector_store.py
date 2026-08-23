import os
import json
import tempfile
import sys
import unittest
import numpy as np
from pathlib import Path

# Add backend directory to sys.path so imports resolve correctly
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.vector_store import VectorStore, EXPECTED_DIMENSION


class TestVectorStore(unittest.TestCase):

    def test_01_empty_index_search(self):
        """1. Verify that searching an empty index safely returns an empty list []."""
        store = VectorStore()
        query = np.zeros(EXPECTED_DIMENSION, dtype=np.float32)
        query[0] = 1.0
        results = store.search(query_embedding=query, top_k=5)
        self.assertEqual(results, [])

    def test_02_search_with_one_vector(self):
        """2. Verify search with a single paper vector indexed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            idx_path = Path(tmpdir) / "research_papers.index"
            map_path = Path(tmpdir) / "paper_id_mapping.json"
            store = VectorStore(index_path=idx_path, mapping_path=map_path)

            v1 = np.zeros(EXPECTED_DIMENSION, dtype=np.float32)
            v1[0] = 1.0
            store.add_paper(paper_id=101, embedding=v1)

            results = store.search(query_embedding=v1, top_k=5)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["paper_id"], 101)
            self.assertAlmostEqual(results[0]["similarity_score"], 1.0, places=5)

    def test_03_search_ranking_and_mapping_resolution(self):
        """Verify search ranking order and paper ID mapping resolution."""
        store = VectorStore()

        v_a = np.zeros(EXPECTED_DIMENSION, dtype=np.float32)
        v_a[0] = 1.0

        v_b = np.zeros(EXPECTED_DIMENSION, dtype=np.float32)
        v_b[0] = 0.6
        v_b[1] = 0.8

        v_c = np.zeros(EXPECTED_DIMENSION, dtype=np.float32)
        v_c[1] = 1.0

        store.add_paper(paper_id=101, embedding=v_a)
        store.add_paper(paper_id=202, embedding=v_b)
        store.add_paper(paper_id=303, embedding=v_c)

        results = store.search(query_embedding=v_a, top_k=3)
        self.assertEqual(len(results), 3)

        self.assertEqual(results[0]["paper_id"], 101)
        self.assertAlmostEqual(results[0]["similarity_score"], 1.0, places=5)

        self.assertEqual(results[1]["paper_id"], 202)
        self.assertAlmostEqual(results[1]["similarity_score"], 0.6, places=5)

        self.assertEqual(results[2]["paper_id"], 303)
        self.assertAlmostEqual(results[2]["similarity_score"], 0.0, places=5)

    def test_04_save_load_persistence_and_auto_dir_creation(self):
        """Verify save_index and load_index, automatic directory creation, and vector count == mapping count."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = Path(tmpdir) / "nested" / "vector_store"
            idx_path = nested_dir / "research_papers.index"
            map_path = nested_dir / "paper_id_mapping.json"

            store = VectorStore(index_path=idx_path, mapping_path=map_path)
            v1 = np.zeros(EXPECTED_DIMENSION, dtype=np.float32)
            v1[0] = 1.0
            store.add_paper(paper_id=77, embedding=v1)

            # Auto directory creation check
            store.save_index()
            self.assertTrue(idx_path.exists())
            self.assertTrue(map_path.exists())

            # Load into new VectorStore instance
            reloaded = VectorStore(index_path=idx_path, mapping_path=map_path)
            reloaded.load_index()
            self.assertEqual(reloaded.index.ntotal, 1)
            self.assertEqual(reloaded.get_paper_id(0), 77)

    def test_05_desynchronization_handling(self):
        """Verify RuntimeError is raised when FAISS vector count != mapped paper IDs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            idx_path = Path(tmpdir) / "research_papers.index"
            map_path = Path(tmpdir) / "paper_id_mapping.json"

            store = VectorStore(index_path=idx_path, mapping_path=map_path)
            v1 = np.zeros(EXPECTED_DIMENSION, dtype=np.float32)
            v1[0] = 1.0
            store.add_paper(paper_id=1, embedding=v1)
            store.save_index()

            # Corrupt mapping file count to simulate desynchronization
            with open(map_path, "w", encoding="utf-8") as f:
                json.dump({"position_to_paper": {}, "paper_to_position": {}}, f)

            corrupted_store = VectorStore(index_path=idx_path, mapping_path=map_path)
            with self.assertRaises(RuntimeError) as ctx:
                corrupted_store.load_index()
            self.assertIn("VectorStore state inconsistent", str(ctx.exception))

    def test_06_vector_store_rebuild_index_and_remove_paper(self):
        """Verify rebuild_index and remove_paper functionality."""
        with tempfile.TemporaryDirectory() as tmpdir:
            idx_path = Path(tmpdir) / "research_papers.index"
            map_path = Path(tmpdir) / "paper_id_mapping.json"

            store = VectorStore(index_path=idx_path, mapping_path=map_path)

            v1 = np.zeros(EXPECTED_DIMENSION, dtype=np.float32)
            v1[0] = 1.0
            v2 = np.zeros(EXPECTED_DIMENSION, dtype=np.float32)
            v2[1] = 1.0

            # Rebuild with 2 papers
            records = [
                {"paper_id": 10, "embedding": v1},
                {"paper_id": 20, "embedding": v2}
            ]
            rebuilt_count = store.rebuild_index(records)
            self.assertEqual(rebuilt_count, 2)
            self.assertTrue(store.contains_paper(10))
            self.assertTrue(store.contains_paper(20))

            # Remove paper 10
            removed = store.remove_paper(10)
            self.assertTrue(removed)
            self.assertFalse(store.contains_paper(10))
            self.assertEqual(store.index.ntotal, 1)
            self.assertEqual(store.get_paper_id(0), 20)


if __name__ == "__main__":
    unittest.main()
