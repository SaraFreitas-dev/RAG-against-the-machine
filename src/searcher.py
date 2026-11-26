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
        Search the loaded BM25 index for relevant source chunks.
        Tokenize the query, retrieve the top-k matching documents,
        and return their source references.
        """
        minimal_sources: list[MinimalSource] = []
        if self.bm25 is None:
            raise RuntimeError("BM25 index has not been loaded.")
        if not query.strip():
            raise ValueError("Query not provided.")
        if k <= 0:
            raise ValueError("k must be greater than zero.")

        query_tokens = bm25s.tokenize([query])

        # results: Contains the recovered chunks, in order of relevance
        # Scores: Contains the BM25 ranks matching each document
        # res, score _ but score its not needed since its return by value order
        results, _ = self.bm25.retrieve(query_tokens, k=k)

        # shape[0]: Number of questions
        # shape[1]: Number of results per question (k)
        # Iterate over the retrieved documents in relevance order
        for i in range(results.shape[1]):
            doc = results[0, i]
            # Extract the source metadata from each document
            minimal_source = MinimalSource(
                file_path=doc["source"]["file_path"],
                first_character_index=doc["source"]["first_character_index"],
                last_character_index=doc["source"]["last_character_index"]
            )
            minimal_sources.append(minimal_source)
        return minimal_sources
