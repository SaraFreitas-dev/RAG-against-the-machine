```text
data/raw/vllm-0.10.1/
        |
        v
      INDEXER
        |
        |-- Discover files recursively
        |-- Filter supported extensions (.py, .md, .txt)
        |-- Read file contents
        |-- Preserve original file paths
        |
        v
    chunk_file()
        |
        v
    list[Chunk]
        |
        |-- Collect chunks from all files
        |-- Extract index_text from each chunk
        |
        v
    BM25 / TF-IDF
        |
        |-- Build a searchable index
        |-- Store chunks and source references
        |-- Persist the index
        |
        v
    SEARCHABLE INDEX
        |
        v
      RETRIEVER

rglob("*") → encontra caminhos em todas as subpastas.
path.is_file() → verifica se o caminho corresponde a um ficheiro.
path.suffix → permite verificar a extensão.
path.open() → abre efetivamente o ficheiro para ler o conteúdo.
```