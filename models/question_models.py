# src/models/question_models.py
from pydantic import BaseModel, Field, validator
from typing import Any, List, Dict, Optional
from datetime import datetime
from uuid import uuid4
from enum import Enum

class QuestionType(str, Enum):
    MCQ = "Multiple Choice"
    MSQ = "Multiple Select"
    SDQ = "Short Descriptive Answer"
    LDQ = "Long Descriptive Answer"

class DifficultyLevel(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"

class QuestionDistribution(BaseModel):
    multiple_choice: int = Field(..., ge=0)
    multiple_select: int = Field(..., ge=0)
    short_descriptive: int = Field(..., ge=0)
    long_descriptive: int = Field(..., ge=0, le=10)

    @validator('long_descriptive')
    def validate_long_descriptive(cls, v):
        if v > 10:
            raise ValueError("Number of long descriptive questions cannot exceed 10")
        return v

    def total_questions(self) -> int:
        """Get total number of questions."""
        return (self.multiple_choice + 
                self.multiple_select + 
                self.short_descriptive + 
                self.long_descriptive)

class DifficultyDistribution(BaseModel):
    easy: int = Field(..., ge=0)
    medium: int = Field(..., ge=0)
    hard: int = Field(..., ge=0)

    @validator('*')
    def validate_counts(cls, v):
        if v < 0:
            raise ValueError("Difficulty counts cannot be negative")
        return v

    def total_questions(self) -> int:
        """Get total number of questions across difficulties."""
        return self.easy + self.medium + self.hard
class Question(BaseModel):
    type: str
    difficulty: str
    question: str
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    correct_answers: Optional[List[str]] = None
    answer: Optional[str] = None
    keywords: Optional[List[str]] = None

class QuestionRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    standard: str = Field(..., min_length=1)
    subject: str = Field(..., min_length=1)
    chapter: str = Field(..., min_length=1)
    language: str = Field(default="English")
    syllabus: str = Field(default="NCERT")
    question_distribution: QuestionDistribution
    difficulty_distribution: DifficultyDistribution
    topic: Optional[str] = None

    @validator('difficulty_distribution')
    def validate_distribution_match(cls, v, values):
        if 'question_distribution' in values:
            q_total = values['question_distribution'].total_questions()
            d_total = v.total_questions()
            if q_total != d_total:
                raise ValueError(
                    f"Total questions in difficulty distribution ({d_total}) "
                    f"must match question distribution total ({q_total})"
                )
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "standard": "11th",
                "subject": "Biology",
                "chapter": "The Living World",
                "question_distribution": {
                    "multiple_choice": 3,
                    "multiple_select": 2,
                    "short_descriptive": 2,
                    "long_descriptive": 1
                },
                "difficulty_distribution": {
                    "easy": 3,
                    "medium": 3,
                    "hard": 2
                },
                "topic": "Kingdom"  # optional
            }
        }

class QuestionResponse(BaseModel):
    title: str
    questions: List[Question]
    metadata: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)