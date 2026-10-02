"""
Each command writes a JSON file that conforms to the provided pydantic models:
• For search operations: Use StudentSearchResults model with:
◦ search_results: List of MinimalSearchResults containing question_id, question and retrieved_sources
◦ k: Number of results requested
• For answer generation: Use StudentSearchResultsAndAnswer model with:
◦ search_results: List of MinimalAnswer containing question_id, question,
retrieved_sources, and answer
◦ k: Number of results requested
• Source information: Each MinimalSource contains:
◦ file_path: path to the source file, relative to your project root and written exactly as in the ingested corpus (e.g. data/raw/vllm-0.10.1/...); it is
compared verbatim to the reference
◦ first_character_index: Starting character position
◦ last_character_index: Ending character position

Output Format
The output must respect the minimal basis of the provided models but can be enhanced
as follows:
Example: StudentSearchResults Output
"search_results": [
{
"question_id": "q1",
"question": "How to configure OpenAI server?",
"retrieved_sources": [
{
"file_path": "data/raw/vllm-0.10.1/docs/serving/openai_compatible_server.md",
"first_character_index": 9867,
"last_character_index": 10100
},
{
"file_path": "data/raw/vllm-0.10.1/vllm/entrypoints/openai/api_server.py",
"first_character_index": 267,
"last_character_index": 400
}
]
}
],
"k": 10
For answers, the output should follow the StudentSearchResultsAndAnswer model:
Example: StudentSearchResultsAndAnswer Output
"search_results": [
{
"question_id": "q1",
"question": "How to configure OpenAI server?",
"retrieved_sources": [
{
"file_path": "data/raw/vllm-0.10.1/docs/serving/openai_compatible_server.md",
"first_character_index": 9867,
"last_character_index": 10100
},
{
"file_path": "data/raw/vllm-0.10.1/vllm/entrypoints/openai/api_server.py",
"first_character_index": 267,
"last_character_index": 400
}
],
"answer": "To configure the OpenAI compatible server in vLLM..."
}
],
"k": 10
"""