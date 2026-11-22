from .chunking import Chunker
from .indexer import Indexer
import time


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

    try:
        chunker = Chunker(max_size=2000)
    except ValueError as e:
        print(f"ValueError: {e}")

    start = time.perf_counter()
    indexer = Indexer("data/raw", chunker)
    chunks = indexer._collect_chunks()

    end = time.perf_counter()

    for chunk in chunks:
        print("-------------------------")
        print(chunk)
    print(f"Total chunks: {len(chunks)}")
    print(f"Execution time: {end - start:.2f} seconds")


if __name__ == "__main__":
    main()
