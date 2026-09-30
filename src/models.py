"""
Implement the following pydantic models; they validate the data exchanged between the
stages. The MinimalSource model represents a single source of information:
MinimalSource Model

class MinimalSource(BaseModel):
file_path: str
first_character_index: int
last_character_index: int

-------------------------------------
The UnansweredQuestion and AnsweredQuestion models represent an unanswered
question and an answered question:
UnansweredQuestion and AnsweredQuestion Models

class UnansweredQuestion(BaseModel):
question_id: str = Field(default_factory=lambda:
str(uuid.uuid4()))
question: str

class AnsweredQuestion(UnansweredQuestion):
sources: List[MinimalSource]
answer: str

-------------------------------------
The RagDataset model represents a dataset of RAG questions:
RagDataset Model

class RagDataset(BaseModel):
rag_questions: List[AnsweredQuestion | UnansweredQuestion]

-------------------------------------
The MinimalSearchResults and MinimalAnswer models represent the search results
and an answer:
MinimalSearchResults and MinimalAnswer Models

class MinimalSearchResults(BaseModel):
question_id: str
question: str
retrieved_sources: List[MinimalSource]

class MinimalAnswer(MinimalSearchResults):
answer: str

-------------------------------------
The StudentSearchResults and StudentSearchResultsAndAnswer models represent search results and search results with answers:
StudentSearchResults and StudentSearchResultsAndAnswer Models

class StudentSearchResults(BaseModel):
search_results: List[MinimalSearchResults]
k: int

class StudentSearchResultsAndAnswer(BaseModel):
search_results: List[MinimalAnswer]
k: int

The provided models are a foundation. You can expand them by adding new models
or extra fields (for example in the search results model) if your implementation requires
it.
"""