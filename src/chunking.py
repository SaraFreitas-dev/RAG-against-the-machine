from .models import MinimalSource, Chunk
import ast
from langchain_text_splitters import (RecursiveCharacterTextSplitter,
                                      Language)
from langchain_core.documents import Document
from pathlib import Path


class Chunker:
    """
    Cuts corpus files into chunks no wider than max_size characters
    """
    def __init__(self, max_size: int) -> None:
        if max_size <= 0 or max_size > 2000:
            raise ValueError("max_size must be between 1 and 2000")
        self.max_size: int = max_size

    # ---------------- Main entry point ----------------
    def chunk_file(self, text: str, file_path: str) -> list[Chunk]:
        """
        Split a file into chunks based on its file type.

        Select the appropriate chunking strategy for Python, Markdown,
        or plain text files.

        Return a list of Chunk objects containing the extracted content
        and their original source references.
        """
        ranges: list[tuple[int, int]] = []
        path = Path(file_path)
        if path.suffix.lower() == ".py":
            ranges = self._chunk_python(text)
        elif path.suffix.lower() == ".md":
            ranges = self._chunk_markdown(text)
        else:
            ranges = self._chunk_text(text)
        return self._build_chunks(text, file_path, ranges)

    # ---------------- Python strategy ----------------
    def _chunk_python(self, text: str) -> list[tuple[int, int]]:
        """
        Split Python source code into chunks using AST boundaries.

        Identify top-level code blocks and split any blocks that exceed
        the configured maximum size.

        Return a list of (start, end) character offsets referencing
        the original source text.
        """
        chunk_pieces: list[tuple[int, int]] = []
        blocks: list[tuple[int, int]] = self._get_python_boundaries(text)

        for start, end in blocks:
            chunk_pieces.extend(self._split_large_range(text, start, end))
        return chunk_pieces

    def _get_line_offsets(self, text: str) -> list[int]:
        """
        Build a table of line starts, including the end of the text.
        Converts each line into a position
        """
        line_starts: list[int] = [0]
        for line in text.splitlines(keepends=True):
            line_starts.append(line_starts[-1] + len(line))
        return line_starts

    def _get_python_boundaries(self, text: str) -> list[tuple[int, int]]:
        """
        Identify natural boundaries in Python source code.

        Return character ranges for top-level code blocks,
        including functions, classes, and other statements.

        Large blocks are split during the chunking stage.
        """
        blocks: list[tuple[int, int]] = []
        try:
            tree = ast.parse(text)
            line_starts = self._get_line_offsets(text)
            previous_end: int = 0
            previous_was_import = False

            for node in tree.body:
                is_import = isinstance(node, (ast.Import, ast.ImportFrom))
                if isinstance(node, (
                    ast.Import,
                    ast.ImportFrom,
                    ast.ClassDef,
                    ast.FunctionDef,
                    ast.AsyncFunctionDef
                )):
                    if node.end_lineno is None:
                        previous_was_import = False
                        continue
                    start = line_starts[node.lineno - 1]
                    end = line_starts[node.end_lineno]

                    # Group the decorators into the same function chunk
                    if (
                        isinstance(node, (ast.FunctionDef,
                                          ast.AsyncFunctionDef,
                                          ast.ClassDef))
                        and node.decorator_list
                    ):
                        first_decorator_line = min(
                            decorator.lineno for
                            decorator in node.decorator_list
                        )
                        start = line_starts[first_decorator_line - 1]

                    # Group all imports in one single chunk
                    if is_import and previous_was_import:
                        blocks[-1] = (blocks[-1][0], end)
                    else:
                        # Checks for any missing information in the gaps
                        if start > previous_end:
                            gap = text[previous_end:start]
                            if gap.strip():
                                blocks.append((previous_end, start))
                        blocks.append((start, end))
                    previous_end = end
                previous_was_import = is_import

            # Include any remaining content at the end of the file
            if previous_end < len(text):
                tail = text[previous_end:]

                if tail.strip():
                    blocks.append((previous_end, len(text)))
            return blocks

        except SyntaxError:
            return [(0, len(text))] if text else []

    # ---------------- Markdown / text strategy ----------------
    def _chunk_markdown(self, text: str) -> list[tuple[int, int]]:
        """
        Divide the Markdown content into chunks
        """
        res: list[tuple[int, int]] = []
        splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.MARKDOWN,
            chunk_size=self.max_size,
            chunk_overlap=min(15, self.max_size // 6),
            length_function=len,
            add_start_index=True,
            strip_whitespace=False,
        )
        chunks: list[Document] = splitter.create_documents([text])
        for chunk in chunks:
            doc_start: int = chunk.metadata["start_index"]
            doc_end: int = doc_start + len(chunk.page_content)

            res.append((doc_start, doc_end))
        return res

    def _chunk_text(self, text: str) -> list[tuple[int, int]]:
        """
        Divide the txt files into chunks
        """
        res: list[tuple[int, int]] = []
        splitter = RecursiveCharacterTextSplitter(
            separators=["\nclass ", "\ndef ", "\n\n", "\n", " ", ""],
            chunk_size=self.max_size,
            chunk_overlap=min(15, self.max_size // 6),
            length_function=len,
            add_start_index=True,
            strip_whitespace=False,
        )
        chunks: list[Document] = splitter.create_documents([text])
        for chunk in chunks:
            doc_start: int = chunk.metadata["start_index"]
            doc_end: int = doc_start + len(chunk.page_content)

            res.append((doc_start, doc_end))
        return res

    # ---------------- Shared logic ----------------
    def _split_large_range(self, text: str, start: int,
                           end: int) -> list[tuple[int, int]]:
        """
        Receives big chunks and divides it into chunks no longer
        than the max_size limit
        """
        res: list[tuple[int, int]] = []
        curr_size: int = end - start

        if curr_size <= self.max_size:
            return [(start, end)]

        section: str = text[start:end]
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.max_size,
            chunk_overlap=min(15, self.max_size // 6),
            length_function=len,
            add_start_index=True,
            strip_whitespace=False,
        )

        chunks: list[Document] = splitter.create_documents([section])
        for chunk in chunks:
            doc_start: int = start + chunk.metadata["start_index"]
            doc_end: int = doc_start + len(chunk.page_content)

            res.append((doc_start, doc_end))
        return res

    def _build_chunks(self, text: str, file_path: str,
                      ranges: list[tuple[int, int]]) -> list[Chunk]:
        """
        Build Chunk objects from character ranges in the original text.

        For each range, create a MinimalSource containing the file path
        and character offsets, then extract the corresponding text.

        Return a list of Chunk objects with their source references
        and content for indexing.
        """
        chunks: list[Chunk] = []
        for (start, end) in ranges:
            source = MinimalSource(file_path=file_path,
                                   first_character_index=start,
                                   last_character_index=end)
            chunks.append(Chunk(source=source,
                                text=text[start:end],
                                index_text=text[start:end]))
        return chunks
