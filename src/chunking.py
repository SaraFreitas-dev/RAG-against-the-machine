from .models import MinimalSource, Chunk
import ast


class Chunker:
    """
    Cuts corpus files into chunks no wider than max_size characters
    """
    def __init__(self, max_size: int) -> None:
        if max_size <= 0 or max_size > 2000:
            raise ValueError("max_size must be between 1 and 2000")
        self.max_size: int = max_size

    # Main entry point
    def chunk_file(self, text: str, file_path: str) -> list[Chunk]:
        pass

    # Python strategy
    def _chunk_python(self, text: str) -> list[tuple[int, int]]:
        pass

    def _get_line_offsets(self, text: str) -> list[int]:
        """
        Build a table of line starts,
        including the end of the text.
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
                        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                        and node.decorator_list
                    ):
                        first_decorator_line = min(
                            decorator.lineno for decorator in node.decorator_list
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
        

    # Markdown / text strategy
    def _chunk_markdown(self, text: str) -> list[tuple[int, int]]:
        pass

    def _get_markdown_boundaries(self, text: str) -> list[tuple[int, int]]:
        pass
    
    # Shared logic
    def _split_large_range(self, text: str, start: int, end: int) -> list[tuple[int, int]]:
        """
        Receives big chunks and divides it into chunks no longer
        than the max_size limit
        """
        pass

    def _build_chunks(self, text: str, file_path: str, ranges: list[tuple[int, int]]) -> list[Chunk]:
        pass
