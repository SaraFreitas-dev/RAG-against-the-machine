import time
from .indexer import Indexer
from .searcher import Searcher
from .chunking import Chunker


class CLI:
    """
    Command-line interface for the RAG project.
    """

    def index(self,
              max_chunk_size: int = 2000,
              root_path: str = "data/raw",
              output_path: str = "data/processed/") -> None:
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

        try:
            indexer = Indexer(root_path, output_path, chunker)
            start = time.perf_counter()
            indexer.build_index()
        except (FileNotFoundError, NotADirectoryError, ValueError) as e:
            print(f"{type(e).__name__}: {e}")
            raise SystemExit(1)

        end = time.perf_counter()
        print(f"Total chunks: {len(indexer.chunks_lst)}")
        print(f"Total indexing time: {end - start:.2f} seconds")
        print(f"Ingestion complete! Indices saved under {output_path}")

    def search(self,
               query: str,
               k: int = 5,
               index_path: str = "data/processed") -> None:
        """
        Return the top-k sources for a single query
        """
        try:
            searcher = Searcher(index_path)
            start = time.perf_counter()
            searcher.load_index()
            sources = searcher.search(
                query,
                k=k,
            )

            for source in sources:
                print(source)
            end = time.perf_counter()
            print(f"Total searching time: {end - start:.2f} seconds")

        except (FileNotFoundError, NotADirectoryError,
                ValueError, RuntimeError) as e:
            print(f"{type(e).__name__}: {e}")
            raise SystemExit(1)
