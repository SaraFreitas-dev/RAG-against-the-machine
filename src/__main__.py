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

    chunker = Chunker(max_size=2000)
    blocks = chunker._get_python_boundaries(text)

    for i, (start, end) in enumerate(blocks, 1):
        print(f"\n--- Block {i} [{start}:{end}] ---")
        print(repr(text[start:end]))


if __name__ == "__main__":
    main()