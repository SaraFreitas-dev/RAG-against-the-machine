
"""Unit and integration tests for the BM25 Searcher."""

import tempfile
import unittest
from pathlib import Path

from src.chunking import Chunker
from src.indexer import Indexer
from src.models import MinimalSource
from src.searcher import Searcher


class TestSearcher(unittest.TestCase):
    """Test BM25 index loading, validation, and source retrieval."""

    def setUp(self) -> None:
        """Create temporary directories and test documents."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.root: Path = Path(self.temp_dir.name)
        self.input_path: Path = self.root / "raw"
        self.index_path: Path = self.root / "processed"

        self.input_path.mkdir()

        self.documents: dict[str, str] = {
            "python.txt": "Python programming functions and classes.",
            "gpu.txt": "GPU memory allocation and management.",
            "space.txt": "Quasar astronomy observation.",
        }

        for name, content in self.documents.items():
            path = self.input_path / name
            path.write_text(content, encoding="utf-8")

        self.searcher = Searcher(str(self.index_path))

    def build_test_index(self) -> None:
        """Build a small BM25 index using the temporary documents."""
        chunker = Chunker(max_size=2000)
        indexer = Indexer(
            str(self.input_path),
            str(self.index_path),
            chunker,
        )
        indexer.build_index()

    def test_initial_state(self) -> None:
        """Verify that the BM25 index is initially unloaded."""
        self.assertIsNone(self.searcher.bm25)
        self.assertEqual(self.searcher.index_path, self.index_path)

    def test_missing_directory(self) -> None:
        """Raise FileNotFoundError for a missing index directory."""
        with self.assertRaises(FileNotFoundError):
            self.searcher.load_index()

    def test_not_a_directory(self) -> None:
        """Raise NotADirectoryError when the index path is a file."""
        file_path = self.root / "index.txt"
        file_path.write_text("Not a directory.", encoding="utf-8")

        self.searcher = Searcher(str(file_path))

        with self.assertRaises(NotADirectoryError):
            self.searcher.load_index()

    def test_load_index(self) -> None:
        """Load a previously saved BM25 index and its corpus."""
        self.build_test_index()
        self.searcher.load_index()

        bm25 = self.searcher.bm25

        self.assertIsNotNone(bm25)
        assert bm25 is not None

        self.assertIsNotNone(bm25.corpus)
        assert bm25.corpus is not None

        self.assertEqual(len(bm25.corpus), 3)

    def test_search_without_loading(self) -> None:
        """Raise RuntimeError when searching before loading the index."""
        with self.assertRaises(RuntimeError):
            self.searcher.search("GPU memory", k=1)

    def test_empty_query(self) -> None:
        """Reject an empty search query."""
        self.build_test_index()
        self.searcher.load_index()

        with self.assertRaises(ValueError):
            self.searcher.search("", k=1)

    def test_whitespace_query(self) -> None:
        """Reject search queries containing only whitespace."""
        self.build_test_index()
        self.searcher.load_index()

        with self.assertRaises(ValueError):
            self.searcher.search("   ", k=1)

    def test_invalid_k(self) -> None:
        """Reject zero and negative values of k."""
        self.build_test_index()
        self.searcher.load_index()

        for k in (0, -1, -5):
            with self.subTest(k=k):
                with self.assertRaises(ValueError):
                    self.searcher.search("GPU memory", k=k)

    def test_basic_retrieval(self) -> None:
        """Retrieve the source matching a distinctive query term."""
        self.build_test_index()
        self.searcher.load_index()

        sources = self.searcher.search("quasar", k=1)

        self.assertEqual(len(sources), 1)
        self.assertIsInstance(sources[0], MinimalSource)
        self.assertTrue(sources[0].file_path.endswith("space.txt"))

    def test_source_offsets(self) -> None:
        """Verify that retrieved offsets identify the original text."""
        self.build_test_index()
        self.searcher.load_index()

        sources = self.searcher.search("quasar", k=1)
        source = sources[0]

        with open(
            source.file_path,
            "r",
            encoding="utf-8",
            newline="",
        ) as file:
            original_text = file.read()

        start = source.first_character_index
        end = source.last_character_index

        self.assertTrue(0 <= start < end <= len(original_text))
        self.assertEqual(
            original_text[start:end],
            self.documents["space.txt"],
        )
        self.assertLessEqual(end - start, 2000)

    def test_top_k(self) -> None:
        """Return the requested number of source references."""
        self.build_test_index()
        self.searcher.load_index()

        sources_one = self.searcher.search("memory", k=1)
        sources_two = self.searcher.search("memory", k=2)

        self.assertEqual(len(sources_one), 1)
        self.assertEqual(len(sources_two), 2)
        self.assertEqual(sources_one[0], sources_two[0])

    def test_multiple_searches(self) -> None:
        """Reuse the loaded index for consecutive search queries."""
        self.build_test_index()
        self.searcher.load_index()

        loaded_index = self.searcher.bm25

        python_sources = self.searcher.search("python", k=1)
        gpu_sources = self.searcher.search("gpu", k=1)

        self.assertIs(self.searcher.bm25, loaded_index)

        self.assertTrue(
            python_sources[0].file_path.endswith("python.txt")
        )
        self.assertTrue(
            gpu_sources[0].file_path.endswith("gpu.txt")
        )


if __name__ == "__main__":
    unittest.main()
