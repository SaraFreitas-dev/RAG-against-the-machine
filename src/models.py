from pydantic import (BaseModel, Field, model_validator)
from typing_extensions import Self
from typing import List
import uuid


class MinimalSource(BaseModel):
    """
    The MinimalSource model represents a single source of information
    """
    file_path: str
    first_character_index: int = Field(ge=0)
    last_character_index: int = Field(ge=0)

    @model_validator(mode='after')
    def check_range(self) -> Self:
        """Ensure the end index is not before the start index
        and its max size"""
        if (self.last_character_index < self.first_character_index):
            raise ValueError("Index error: "
                             "last_character_index < first_character_index")
        if (self.last_character_index - self.first_character_index > 2000):
            raise ValueError("Index error: "
                             "Source wider than 2000 characters")
        return self


class Chunk(BaseModel):
    """
    A piece of a corpus file: its address in the file, its original text,
    and the text used for indexing (the original text plus context such as
    the file path, the section heading or the class name)
    """
    source: MinimalSource
    text: str
    index_text: str


class UnansweredQuestion(BaseModel):
    """
    Represents an unanswered question
    """
    question_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str


class AnsweredQuestion(UnansweredQuestion):
    """
    Represents an answered question
    """
    sources: List[MinimalSource]
    answer: str


class RagDataset(BaseModel):
    """
    Represents a dataset of RAG questions
    """
    rag_questions: List[AnsweredQuestion | UnansweredQuestion]


class MinimalSearchResults(BaseModel):
    """
    Represents the search results
    """
    question_id: str
    question: str
    retrieved_sources: List[MinimalSource]


class MinimalAnswer(MinimalSearchResults):
    """
    Represents the answer result
    """
    answer: str


class StudentSearchResults(BaseModel):
    """
    Represents the search results
    """
    search_results: List[MinimalSearchResults]
    k: int = Field(ge=0)


class StudentSearchResultsAndAnswer(BaseModel):
    """
    Represents the search results with answer
    """
    search_results: List[MinimalAnswer]
    k: int = Field(ge=0)
