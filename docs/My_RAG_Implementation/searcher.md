O Indexer é a pessoa que lê os livros e cria um catálogo onde regista os assuntos e as páginas relevantes.
O Searcher é a pessoa que recebe uma pergunta, consulta esse catálogo e indica onde encontrar a informação.

```text

CLI: search "How does GPU memory work?" --k 5
    │
    ▼
Criar Searcher
    │
    ▼
Carregar índice BM25
    │
    ▼
search(question, k=5)
    │
    ├── Tokenizar pergunta
    ├── Consultar BM25
    ├── Recuperar os chunks relevantes
    └── Converter para MinimalSource
    │
    ▼
Devolver list[MinimalSource]

```