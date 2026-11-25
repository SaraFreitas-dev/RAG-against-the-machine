from .models import MinimalSource
from pathlib import Path
import bm25s


class Searcher:
    """
    Search a previously generated BM25 index to retrieve
    the most relevant source references for a given query.
    """
    def __init__(self, index_path: str) -> None:
        self.index_path: Path = Path(index_path)
        self.bm25: bm25s.BM25 | None = None
        
    def load_index(self) -> None:
        """
        Load the previously saved BM25 index and its corpus.
        Validate the index directory before loading the index
        and its associated chunk metadata.
        """
        if not self.index_path.exists():
            raise FileNotFoundError(
                f"Index directory does not exist: '{self.index_path}'"
            )

        if not self.index_path.is_dir():
            raise NotADirectoryError(
                f"Index path is not a directory: '{self.index_path}'"
            )
        self.bm25 = bm25s.BM25.load(str(self.index_path),
                                    load_corpus=True)
        
    def search(self, query: str, k: int) -> list[MinimalSource]:
        """
        Search for a question and return possible results
        """
        minimal_sources: list[MinimalSource] = []
        if not self.bm25:
            return []
        query_tokens = bm25s.tokenize(query)
        retriever = bm25s.BM25()
        retriever.index(query_tokens)
        # Get top-k results as a tuple of (doc ids, scores)
        results, scores = retriever.retrieve(query_tokens,
                                             corpus=query,
                                             k=k)
        for i in range(results.shape[1]):
            doc, score = results[0, i], scores[0, i]
