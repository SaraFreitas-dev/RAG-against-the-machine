import logging
import tempfile
import unittest
from pathlib import Path
import bm25s
from src.chunking import Chunker
from src.indexer import Indexer


class TestIndexer(unittest.TestCase):
    """Test file discovery, chunk collection, and BM25 indexing."""

    def setUp(self) -> None:
        """Create temporary directories and initialize test dependencies."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.root: Path = Path(self.temp_dir.name)
        self.input_path: Path = self.root / "raw"
        self.output_path: Path = self.root / "processed"

        self.input_path.mkdir()
        self.chunker = Chunker(max_size=2000)

    def create_file(self, name: str, content: str) -> Path:
        """Create a UTF-8 test file in the temporary source directory."""
        path = self.input_path / name
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8", newline="") as file:
            file.write(content)

        return path

    def create_indexer(self) -> Indexer:
        """Create an Indexer configured with temporary test paths."""
        return Indexer(
            str(self.input_path),
            str(self.output_path),
            self.chunker,
        )

    def test_missing_directory(self) -> None:
        """Raise FileNotFoundError when the source directory is missing."""
        self.input_path = self.root / "nonexistent"
        indexer = self.create_indexer()

        with self.assertRaises(FileNotFoundError):
            indexer.build_index()

    def test_not_a_directory(self) -> None:
        """Raise NotADirectoryError when the source path is a file."""
        self.input_path = self.create_file(
            "example.txt",
            "Example content.",
        )
        indexer = self.create_indexer()

        with self.assertRaises(NotADirectoryError):
            indexer.build_index()

    def test_empty_directory(self) -> None:
        """Raise ValueError when the source directory is empty."""
        indexer = self.create_indexer()

        with self.assertRaises(ValueError):
            indexer.build_index()

    def test_unsupported_files(self) -> None:
        """Ignore unsupported extensions and reject an empty corpus."""
        self.create_file("example.json", '{"test": true}')
        indexer = self.create_indexer()

        with self.assertRaises(ValueError):
            indexer.build_index()

    def test_invalid_encoding(self) -> None:
        """Skip invalid UTF-8 files while indexing valid files."""
        self.create_file(
            "valid.txt",
            "This is a valid test file.",
        )
        invalid_path = self.input_path / "invalid.txt"
        invalid_path.write_bytes(b"\xff\xfe")

        indexer = self.create_indexer()

        with self.assertLogs(level=logging.WARNING) as logs:
            indexer.build_index()

        self.assertEqual(len(indexer.chunks_lst), 1)
        self.assertTrue(
            any("invalid.txt" in message for message in logs.output)
        )

    def test_chunk_offsets(self) -> None:
        """Verify chunk text, source offsets, and maximum chunk size."""
        self.create_file(
            "example.py",
            "import os\n\n"
            "def hello():\n"
            "    return 'Hello world'\n",
        )
        self.create_file(
            "example.md",
            "# Heading\r\n\r\nSome Markdown content.\r\n",
        )
        self.create_file(
            "example.txt",
            "Some plain text content.\n",
        )

        indexer = self.create_indexer()
        indexer.build_index()

        self.assertGreater(len(indexer.chunks_lst), 0)

        for chunk in indexer.chunks_lst:
            source = chunk.source

            with self.subTest(file=source.file_path):
                with open(
                    source.file_path,
                    "r",
                    encoding="utf-8",
                    newline="",
                ) as file:
                    original = file.read()

                start = source.first_character_index
                end = source.last_character_index

                self.assertTrue(0 <= start < end <= len(original))
                self.assertEqual(chunk.text, original[start:end])
                self.assertLessEqual(
                    len(chunk.text),
                    self.chunker.max_size,
                )

    def test_save_and_load_index(self) -> None:
        """Verify that the saved index preserves chunk metadata."""
        self.create_file(
            "first.txt",
            "Python programming language.",
        )
        self.create_file(
            "second.txt",
            "GPU memory allocation.",
        )

        indexer = self.create_indexer()
        indexer.build_index()

        loaded = bm25s.BM25.load(
            str(self.output_path),
            load_corpus=True,
        )

        self.assertIsNotNone(loaded.corpus)
        self.assertEqual(
            len(loaded.corpus),
            len(indexer.chunks_lst),
        )

        for original, saved in zip(
            indexer.chunks_lst,
            loaded.corpus,
        ):
            with self.subTest(file=original.source.file_path):
                self.assertEqual(saved["text"], original.text)
                self.assertEqual(
                    saved["source"],
                    original.source.model_dump(),
                )

    def test_basic_retrieval(self) -> None:
        """Verify that BM25 retrieves the most relevant test chunk."""
        self.create_file(
            "python.txt",
            "Python programming language.",
        )
        self.create_file(
            "gpu.txt",
            "GPU memory allocation.",
        )
        self.create_file(
            "space.txt",
            "Quasar astronomy observation.",
        )

        indexer = self.create_indexer()
        indexer.build_index()

        loaded = bm25s.BM25.load(
            str(self.output_path),
            load_corpus=True,
        )

        query_tokens = bm25s.tokenize(["quasar"])
        results = loaded.retrieve(
            query_tokens,
            k=1,
            show_progress=False,
        )

        best_chunk = results.documents[0, 0]

        self.assertTrue(
            best_chunk["source"]["file_path"].endswith("space.txt")
        )
        self.assertIn("Quasar", best_chunk["text"])


if __name__ == "__main__":
    unittest.main()
