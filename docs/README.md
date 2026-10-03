# Docs — RAG against the machine

Study notes written while building this project. They explain the **concepts** behind each stage of the pipeline for someone who has never worked with RAG before.

These docs explain *what* and *why*, not *how*.

## The pipeline at a glance

```
 Corpus ──► Chunking ──► Index ──► Retrieve ──► Augment ──► Generate ──► Answer
(vLLM repo)            (BM25 /    (top-k      (build      (Qwen3-0.6B)  (JSON)
                        TF-IDF)    sources)    context)
                                      │
                                      └──► Evaluate (recall@k)
```

## Reading order

| # | Doc | What it covers |
|---|-----|----------------|
| 00 | [What is RAG](00-what-is-rag.md) | The problem (a "frozen" LLM), the four stages (index → retrieve → augment → generate), and why we retrieve instead of retraining |
| 01 | [The corpus and character offsets](01-corpus-and-offsets.md) | A file seen as one long string, what `first_character_index` / `last_character_index` mean, and why `file_path` must match exactly |
| 02 | [Chunking](02-chunking.md) | Why we split text, chunk size and overlap and how they affect recall, and why code and Markdown are split differently |
| 03 | [Tokenization](03-tokenization.md) | From text to terms: lowercasing, `snake_case` / `camelCase`, stopwords, and the trade-off between exact identifiers and paraphrased questions |
| 04 | [TF-IDF](04-tf-idf.md) | How often a term appears vs how rare it is, with the intuition and the formula explained step by step |
| 05 | [BM25](05-bm25.md) | What BM25 improves over TF-IDF (term saturation and length normalization), and what the `k1` and `b` parameters control |
| 06 | [Inverted index and persistence](06-inverted-index.md) | How a search can take milliseconds, what to save to disk, and the 5-minute indexing limit |
| 07 | [Evaluation: recall@k and IoU](07-evaluation.md) | How the grader decides a source was found, and why an IoU of 0.05 is a permissive bar |
| 08 | [Augment and generate with Qwen](08-augment-and-generate.md) | Context windows and tokens, building a prompt, grounding vs hallucination, and Qwen3's "thinking mode" |
| 09 | [Pydantic in practice](09-pydantic.md) | Models, `Field` constraints, `before` vs `after` validators, and validating data between stages |
| 10 | [A robust CLI](10-robust-cli.md) | Python Fire, tqdm progress bars, and handling degenerate inputs without tracebacks |
| 11 | *(bonus)* [Embeddings and hybrid retrieval](11-embeddings-and-hybrid.md) | Semantic vs lexical search and how to combine two rankings into one |

## Where to start

- **New to the topic?** Read 00 → 01 → 07 first. They explain what the system must produce and how it is judged.
- **Working on recall?** Focus on 02, 03 and 05. Chunking, tokenization and ranking decide whether retrieval reaches the thresholds (80% recall@5 on docs, 50% on code).
- **Working on answers?** Go to 08.

## Glossary

| Term | Meaning |
|------|---------|
| **Corpus** | The full collection of documents being searched (here, the vLLM repository) |
| **Chunk** | A slice of a file, identified by its path and character range |
| **Token / term** | The unit of text the search engine compares (usually a word or word part) |
| **Index** | A precomputed structure that makes search fast |
| **top-k** | The *k* best-ranked results for a query |
| **Recall@k** | The share of correct sources found within the top *k* results |
| **Grounding** | An answer that relies on the retrieved context instead of the model's memory |
| **Hallucination** | A confident answer that the sources do not support |