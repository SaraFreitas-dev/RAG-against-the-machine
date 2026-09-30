# Moulinette



Evaluation system for RAG submissions. Validates your search results and calculates recall metrics.



## Installation



```bash

uv venv && uv sync

direnv allow  # or source .envrc

```


## CLI Commands



### evaluate_student_search_results



Evaluate your search results against the ground truth dataset.



```bash

uv run python -m moulinette evaluate_student_search_results \

    <student_results_path> \

    <dataset_path> \

    [--k K] \

    [--max_context_length MAX_LENGTH]

```




**Arguments:**

| Argument | Type | Default | Description |

|----------|------|---------|-------------|

| `student_results_path` | str | required | Path to student search results JSON |

| `dataset_path` | str | required | Path to ground truth dataset JSON |

| `--k` | int | 10 | Maximum number of sources per question |

| `--max_context_length` | int | 2000 | Maximum context length per source |



**Example:**

```bash

uv run python -m moulinette evaluate_student_search_results \

    ../data/output/search_results/dataset_code_public.json \

    ../data/datasets/AnsweredQuestions/dataset_code_public.json \

    --k 10 \

    --max_context_length 2000

```



**Output:**

- Validates student data format

- Calculates Recall@1, Recall@3, Recall@5, Recall@10

- Returns `True` if Recall@5 >= 50%, `False` otherwise




### evaluate_student_answers



Evaluate your generated answers (not yet implemented).



```bash

uv run python -m moulinette evaluate_student_answers <student_answer_path>

```



## Pass Criteria


| Dataset | Metric | Threshold |

|---------|--------|-----------|

| Code | Recall@5 | >= 50% |

| Docs | Recall@5 | >= 80% |



## Input File Formats



### Your Search Results (`student_results_path`)

```json

{

  "search_results": [

    {

      "question_id": "uuid",

      "question": "What is the question text?",

      "retrieved_sources": [

        {

          "file_path": "data/raw/vllm-0.10.1/path/to/file",

          "first_character_index": 0,

          "last_character_index": 500

        }

      ]

    }

  ],

  "k": 10

}

```



### Ground Truth Dataset (`dataset_path`)

```json

{

  "rag_questions": [

    {

      "question_id": "uuid",

      "question": "What is...",

      "answer": "The answer is...",

      "sources": [

        {

          "file_path": "data/raw/vllm-0.10.1/path/to/file",

          "first_character_index": 0,

          "last_character_index": 500

        }

      ]

    }

  ]

}
