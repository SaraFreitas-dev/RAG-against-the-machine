from .models import MinimalSource, Chunk


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
        pass

    def _get_python_boundaries(self, text: str) -> list[tuple[int, int]]:
        pass
    
    # Markdown / text strategy
    def _chunk_markdown(self, text: str) -> list[tuple[int, int]]:
        pass

    def _get_markdown_boundaries(self, text: str) -> list[tuple[int, int]]:
        pass
    
    # Shared logic
    def _split_large_range(self, text: str, start: int, end: int) -> list[tuple[int, int]]:
        pass

    def _build_chunks(self, text: str, file_path: str, ranges: list[tuple[int, int]]) -> list[Chunk]:
        pass
