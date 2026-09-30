🚧 **Under Construction** 🚧

```text
In practice, RAG has four stages:
• Indexing: organise the data so it can be searched.
• Retrieving: match a question against the index and pull the most relevant snippets.
• Augmenting: filter those snippets and place them in the model’s context window.
• Generating: read that context and produce the answer.

A Retrieval-Augmented Generation system that answers questions about a codebase.
Ingest the provided vLLM repository into a searchable index,
retrieve the most relevant snippets for a question, 
generate an answer from them with Qwen/Qwen3-0.6B, 
and measure retrieval quality with recall@k. 
The system is judged on whether it retrieves the right source locations and produces answers grounded in them.

A Python file and a Markdown page do not break apart the same way, so the program implements two distinct chunking strategies:
• Python code chunking,
• Markdown / text chunking.
For retrieval itself, implemented one of the two classic lexical methods:
• TF-IDF,
• BM25.

Chunk size is configurable through a CLI argument (--max_chunk_size), with a default of 2000 characters.
The indexer chunks every file and persists the index under data/processed/.

system returns the top-k most relevant snippets. 
Each result is a source location: a file_path and the character range (first_character_index, last_character_index) it covers, 
at most 2000 characters wide.

Retrieval must work for a single query and in batch over a whole dataset of questions read from JSON. 
On the reference datasets, the system must reach at least 80 % recall@5 on docs questions and 
50 % on code questions (the metric is defined in the Evaluation chapter).

With the right snippets retrieved, the system generates a natural-language answer using Qwen/Qwen3-0.6B. 
Pass the retrieved context to the model within its token budget, and produce structured JSON following the provided pydantic models.
```