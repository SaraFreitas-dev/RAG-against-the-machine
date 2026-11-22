from .chunking import Chunker
from .models import Chunk
from pathlib import Path
import logging
from tqdm import tqdm
import bm25s
from bm25s.tokenization import Tokenized
from typing import Any


class Indexer:
    """
    Index files from a given root directory.
    Recursively discover and read supported files, split their contents
    into chunks using the Chunker, and build a searchable index.
    """
    def __init__(self, root_path: str,
                 output_path: str, chunker: Chunker) -> None:
        self.root_path: Path = Path(root_path)
        self.output_path: Path = Path(output_path)
        self.chunker = chunker
        self.bm25: bm25s.BM25 | None = None
        self.chunks_lst: list[Chunk] = []

    def _discover_files(self) -> list[Path]:
        """
        Recursively discover supported files within the root directory.

        Return a list of paths to Python, Markdown, and plain text files.
        """
        if not self.root_path.exists():
            raise FileNotFoundError(
                f"Source directory does not exist: '{self.root_path}'"
            )

        if not self.root_path.is_dir():
            raise NotADirectoryError(
                f"Source path is not a directory: '{self.root_path}'"
            )
        paths_lst: list[Path] = []

        for path in self.root_path.rglob("*"):
            if (
                path.is_file()
                and path.suffix.lower() in {".py", ".md", ".txt"}
            ):
                paths_lst.append(path)
        return sorted(paths_lst)

    def _collect_chunks(self) -> list[Chunk]:
        """
        Read supported files and collect their chunks.

        Discover files recursively, read their contents, and use the
        Chunker to split each file into chunks.

        Skip unreadable files and return a combined list of Chunk objects.
        """
        chunk_lst: list[Chunk] = []
        paths_lst: list[Path] = self._discover_files()

        for path in tqdm(paths_lst, desc="Processing files", unit="file"):
            try:
                with path.open("r", encoding="utf-8", newline="") as file:
                    text = file.read()
            except (UnicodeDecodeError, OSError) as e:
                logging.warning(f"WARNING: Failed to read file '{path}': {e}")
                continue
            chunk_lst.extend(self.chunker.chunk_file(text, str(path)))
        return chunk_lst
    
    def build_index(self) -> None:
        """
        Discover and chunk source files, tokenize their content,
        build the BM25 index, and persist the index and chunk metadata.
        """
        self.chunks_lst = self._collect_chunks()
        if not self.chunks_lst:
            raise ValueError("No valid chunks found to build the BM25 index.")

        print("\n============================")
        print("Building BM25 index...")
        print("============================\n")

        # Extracting text of each chunk to the BM25 Analyzer
        corpus: list[str] = [chunk.index_text for chunk in self.chunks_lst]
        # Tokenize the corpus
        corpus_tokens: Tokenized = bm25s.tokenize(corpus)
        # Create the BM25 model and index the corpus
        self.bm25 = bm25s.BM25()
        if self.bm25 is not None:
            self.bm25.index(corpus_tokens)

        print("\n=============================================")
        print(f"There was {len(self.chunks_lst)} chunks generated.")
        print("Storing indexes...")
        print("=============================================\n")

        # Transform each chunk on a dictionary with the chunk info
        chunk_store: list[dict[str, Any]] = [
            chunk.model_dump() for chunk in self.chunks_lst
        ]
        # Create the output directory if it doesn't exist
        self.output_path.mkdir(parents=True, exist_ok=True)

        # Save the BM25 index and chunk metadata
        if self.bm25 is not None:
            self.bm25.save(str(self.output_path), corpus=chunk_store)
