```text
        chunk_file(text, file_path)
                    |
                    v
          Identify file extension
                    |
        +-----------+-----------+
        |           |           |
        v           v           v
       .py          .md         .txt
        |           |           |
        v           v           v
  _chunk_python  _chunk_markdown  _chunk_text
        |           |           |
        v           |           |
 _get_python_       |           |
  boundaries()      |           |
        |           |           |
        v           |           |
 _get_line_offsets()|           |
        |           |           |
        v           |           |
 _split_large_range()           |
        |           |           |
        +-----------+-----------+
                    |
                    v
         list[tuple[int, int]]
                    |
                    v
    _build_chunks(text, file_path, ranges)
                    |
                    |-- Extract text[start:end]
                    |
                    |-- Create MinimalSource
                    |     |-- file_path
                    |     |-- first_character_index
                    |     |-- last_character_index
                    |
                    |-- Create Chunk
                    |     |-- source: MinimalSource
                    |     |-- text: original content
                    |     |-- index_text: indexing content
                    |
                    v
               list[Chunk]
```