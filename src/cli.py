import time
from .indexer import Indexer
from .searcher import Searcher
from .chunking import Chunker
from .models import MinimalSource


class CLI:
    """
    Command-line interface for the RAG project.
    """

    def index(self, max_chunk_size: int = 2000) -> None:
        """
        Build and save the BM25 index from the source files.

        Split files into chunks, build the searchable index,
        and display indexing statistics.
        """
        try:
            chunker = Chunker(max_size=max_chunk_size)
        except ValueError as e:
            print(f"ValueError: {e}")
            raise SystemExit(1)

        indexer = Indexer("data/raw", "data/processed", chunker)
        start = time.perf_counter()

        try:
            indexer.build_index()
        except (FileNotFoundError, NotADirectoryError, ValueError) as e:
            print(f"{type(e).__name__}: {e}")
            raise SystemExit(1)

        end = time.perf_counter()

        print("Ingestion complete! Indices saved under data/processed/")
        print(f"Total chunks: {len(indexer.chunks_lst)}")
        print(f"Total indexing time: {end - start:.2f} seconds")
