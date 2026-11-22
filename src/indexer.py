from .chunking import Chunker
from .models import Chunk
from pathlib import Path
import logging


class Indexer:
    """
    Index files from a given root directory.

    Recursively discover and read supported files, split their contents
    into chunks using the Chunker, and build a searchable index.
    """
    def __init__(self, root_path: str, chunker: Chunker) -> None:
        self.root_path: Path = Path(root_path)
        self.chunker = chunker

    def _discover_files(self) -> list[Path]:
        """
        Recursively discover supported files within the root directory.

        Return a list of paths to Python, Markdown, and plain text files.
        """
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

        for path in paths_lst:
            try:
                with path.open("r", encoding="utf-8", newline="") as file:
                    text = file.read()
            except (UnicodeDecodeError, OSError) as e:
                logging.warning(f"Failed to read file '{path}': {e}")
                continue
            chunk_lst.extend(self.chunker.chunk_file(text, str(path)))
        return chunk_lst

"""rglob("*") path.is_file() path.suffix
_discover_files()	Encontrar recursivamente os ficheiros .py, .md e .txt
_collect_chunks()	Ler os ficheiros e chamar chunk_file()
build_index()	Coordenar a construção do índice BM25
"""
