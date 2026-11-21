from .chunking import Chunker


def main() -> None:
    text = """import os

@dataclass
class Person:
    name: str

@decorator1
@decorator2
def hello():
    print("Hello")
"""

    chunker = Chunker(max_size=30)
    blocks = chunker._get_python_boundaries(text)

    for i, (start, end) in enumerate(blocks, 1):
        print(f"\n--- Block {i} [{start}:{end}] ---")
        print(repr(text[start:end]))

    for start, end in blocks:
        chunk_pieces = chunker._split_large_range(text, start, end)

        print(f"\n=== SPLITTING BLOCK [{start}:{end}] ===")

        for piece_start, piece_end in chunk_pieces:
            print(
                f"[{piece_start}:{piece_end}] "
                f"{repr(text[piece_start:piece_end])}"
            )

if __name__ == "__main__":
    main()
