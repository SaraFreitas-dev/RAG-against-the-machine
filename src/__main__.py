from .chunking import Chunker


def main() -> None:
    text = '''import os
import sys

# Configuração do sistema
MENSAGEM = "Olá, mundo! 🌍"
CIDADE = "São João da Madeira"

def saudacao(nome: str) -> str:
    """Devolve uma saudação em português."""
    return f"Olá, {nome}! 👋"


@dataclass
class Utilizador:
    nome: str
    descrição: str = "Programador 🐍"

    def apresentar(self) -> str:
        return f"Bem-vindo, {self.nome}!"


@decorator
def traduzir():
    palavras = ["coração", "ação", "日本語", "中文"]
    return palavras


# Fim do ficheiro 🚀
ULTIMO_VALOR = 42
'''

    chunker = Chunker(max_size=150)
    blocks = chunker._get_python_boundaries(text)

    for i, (start, end) in enumerate(blocks, 1):
        print(f"\n--- Block {i} [{start}:{end}] ---")
        print(repr(text[start:end]))

    chunk_pieces = chunker._chunk_python(text)

    print(f"\n=== SPLITTING BLOCK [{start}:{end}] ===")

    for piece_start, piece_end in chunk_pieces:
        print(
            f"[{piece_start}:{piece_end}] "
            f"{repr(text[piece_start:piece_end])}"
        )
        
    markdown_text = """# RAG Against the Machine

Retrieval-Augmented Generation (RAG) combines information retrieval
with language models to generate answers based on external documents.

## Introduction

The main goal of this project is to build a system capable of searching
through Python source code and Markdown documentation.

The system must preserve the original source references so that
retrieved information can be traced back to the correct files.

## Chunking Strategies

Chunking divides large documents into smaller pieces that can
be indexed and retrieved efficiently.

### Python Chunking

Python files are analyzed using the Abstract Syntax Tree (AST).

This approach identifies structural elements such as:
- Imports
- Functions
- Classes
- Decorators

Large blocks are divided using RecursiveCharacterTextSplitter.

### Markdown Chunking

Markdown files are split using language-specific separators.

The splitter considers:
- Headings
- Paragraphs
- Newlines
- Spaces

## Example Code

The following function demonstrates a simple calculation:

```python
def calculate_sum(a: int, b: int) -> int:
    return a + b
"""

    markdown_chunks = chunker._chunk_markdown(markdown_text)
    
    print(f"\n=== MARKDOWN CHUNKS ===\n")
    for piece_start, piece_end in markdown_chunks:
        print(
            f"[{piece_start}:{piece_end}] "
            f"{repr(markdown_text[piece_start:piece_end])}"
        )

if __name__ == "__main__":
    main()
