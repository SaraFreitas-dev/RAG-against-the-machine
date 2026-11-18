
# RAG Documentation

This document is used to test Markdown chunking.

## Introduction

Retrieval-Augmented Generation combines information retrieval
with language models to generate contextual answers.

## Installation

Install the project dependencies:

```bash
uv sync
```

## Usage

The system supports indexing and retrieval.

### Indexing

The indexer reads Python and Markdown files,
splits them into chunks, and stores the results.

### Retrieval

The retriever searches the indexed chunks
and returns the most relevant sources.

## Configuration

The maximum chunk size is configurable.

- Maximum allowed size: 2000 characters
- Supported formats: Python and Markdown
- Source offsets must match the original files

## Conclusion

Accurate chunking improves retrieval quality.
