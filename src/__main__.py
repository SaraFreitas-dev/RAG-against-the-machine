from .chunking import Chunker
from .indexer import Indexer
import time


def main() -> None:
    try:
        chunker = Chunker(max_size=2000)
    except ValueError as e:
        print(f"ValueError: {e}")
        return

    indexer = Indexer("data/raw", "data/processed", chunker)

    start = time.perf_counter()

    indexer.build_index()

    end = time.perf_counter()

    print(f"Total chunks: {len(indexer.chunks_lst)}")
    print(f"Total indexing time: {end - start:.2f} seconds")


if __name__ == "__main__":
    main()
