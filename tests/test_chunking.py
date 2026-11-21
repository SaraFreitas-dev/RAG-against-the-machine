"""Tests for the public Chunker.chunk_file() workflow."""

import unittest
from pathlib import Path
from src.chunking import Chunker


class TestChunker(unittest.TestCase):
    """Verify chunk content, offsets and size limits for each strategy."""

    def setUp(self) -> None:
        self.chunker = Chunker(max_size=100)

    def assert_valid_chunks(self, original: str, chunks: list) -> None:
        """Check that every chunk points to the exact original substring."""
        for chunk in chunks:
            source = chunk.source
            start = source.first_character_index
            end = source.last_character_index

            self.assertGreaterEqual(start, 0)
            self.assertLess(start, end)
            self.assertLessEqual(end, len(original))
            self.assertLessEqual(end - start, self.chunker.max_size)
            self.assertEqual(chunk.text, original[start:end])
            self.assertEqual(chunk.index_text, chunk.text)

    def test_python_chunking(self) -> None:
        code = (
            "import os\n"
            "import sys\n\n"
            "@staticmethod\n"
            "def greet(name):\n"
            "    return f'Olá, {name}! 👋'\n\n"
            "class Example:\n"
            "    def run(self):\n"
            "        return 42\n"
        )
        chunks = self.chunker.chunk_file(code, "example.py")

        self.assertTrue(chunks)
        self.assertTrue(all(
            c.source.file_path == "example.py"
            for c in chunks))
        self.assert_valid_chunks(code, chunks)
        self.assertTrue(any("def greet" in c.text for c in chunks))

    def test_markdown_chunking(self) -> None:
        markdown = (
            "# RAG Project\n\n"
            "## Indexing\n\n"
            + "Index source documents carefully. " * 8
            + "\n\n## Retrieval\n\n"
            + "Find useful information in the index. " * 8
        )
        chunks = self.chunker.chunk_file(markdown, "README.md")

        self.assertGreater(len(chunks), 1)
        self.assert_valid_chunks(markdown, chunks)

    def test_txt_chunking(self) -> None:
        sample_path = Path(__file__).parent / "files" / "sample.txt"
        text = sample_path.read_text(encoding="utf-8")
        chunks = self.chunker.chunk_file(text, str(sample_path))

        self.assertGreater(len(chunks), 1)
        self.assert_valid_chunks(text, chunks)
        self.assertTrue(all(
            c.source.file_path == str(sample_path)
            for c in chunks))

    def test_cmakelists_txt_uses_text_strategy(self) -> None:
        cmake = (
            "# Minimum compiler version\n"
            "if(CMAKE_CUDA_COMPILER_VERSION VERSION_GREATER_EQUAL 12.8)\n"
            "  set(CUDA_SUPPORTED_ARCHS \"9.0;10.0;12.0\")\n"
            "endif()\n"
        )
        chunks = self.chunker.chunk_file(cmake, "CMakeLists.txt")
        self.assertTrue(chunks)
        self.assert_valid_chunks(cmake, chunks)

    def test_empty_file(self) -> None:
        self.assertEqual(self.chunker.chunk_file("", "empty.py"), [])
        self.assertEqual(self.chunker.chunk_file("", "empty.md"), [])
        self.assertEqual(self.chunker.chunk_file("", "empty.txt"), [])

    def test_invalid_max_size(self) -> None:
        for invalid in (0, -1, 2001):
            with self.subTest(max_size=invalid):
                with self.assertRaises(ValueError):
                    Chunker(max_size=invalid)

    def test_python_syntax_error_fallback(self) -> None:
        code = "def broken(:\n    pass\n"
        chunks = self.chunker.chunk_file(code, "invalid.py")
        self.assertTrue(chunks)
        self.assert_valid_chunks(code, chunks)

    def test_chunk_text_matches_source_for_every_strategy(self) -> None:
        for file_path in ("example.py", "README.md", "sample.txt"):
            with self.subTest(file_path=file_path):
                text = "A line with café and 🐍.\n" * 15
                chunks = self.chunker.chunk_file(text, file_path)
                self.assertTrue(chunks)
                self.assert_valid_chunks(text, chunks)


if __name__ == "__main__":
    unittest.main()
