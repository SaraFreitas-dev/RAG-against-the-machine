from .chunking import Chunker
from .indexer import Indexer
from .searcher import Searcher
import time


def main() -> None:
    try:
        chunker = Chunker(max_size=2000)
    except ValueError as e:
        print(f"ValueError: {e}")
        return

    indexer = Indexer("data/raw", "data/processed", chunker)

    start = time.perf_counter()

    try:
        indexer.build_index()
    except (FileNotFoundError, NotADirectoryError, ValueError) as e:
        print(f"{type(e).__name__}: {e}")
        raise SystemExit(1)
    end = time.perf_counter()
    print(f"Total chunks: {len(indexer.chunks_lst)}")
    print(f"Total indexing time: {end - start:.2f} seconds")

    searcher = Searcher("data/processed")
    try:
        start = time.perf_counter()
        searcher.load_index()
        sources = searcher.search(
            "How does vLLM manage GPU memory?",
            k=5,
        )

        for source in sources:
            print(source)
        end = time.perf_counter()
        print(f"Total searching time: {end - start:.2f} seconds")

    except (FileNotFoundError, NotADirectoryError, ValueError) as e:
        print(f"{type(e).__name__}: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
