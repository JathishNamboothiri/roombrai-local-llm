# src/models/question_models.py
from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, validator
from uuid import uuid4
from datetime import datetime

class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "Multiple Choice"
    MULTIPLE_SELECT = "Multiple Select"
    SHORT_DESCRIPTIVE = "Short Descriptive Answer"
    LONG_DESCRIPTIVE = "Long Descriptive Answer"

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

class DifficultyDistribution(BaseModel):
    easy: int = Field(..., ge=0)
    medium: int = Field(..., ge=0)
    hard: int = Field(..., ge=0)

    @validator('*')
    def validate_counts(cls, v):
        if v < 0:
            raise ValueError("Difficulty counts cannot be negative")
        return v

class Question(BaseModel):
    type: QuestionType
    difficulty: DifficultyLevel
    question: str
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    correct_answers: Optional[List[str]] = None
    answer: Optional[str] = None
    keywords: Optional[List[str]] = None

    @validator('options')
    def validate_options(cls, v, values):
        if 'type' in values:
            if values['type'] in [QuestionType.MULTIPLE_CHOICE, QuestionType.MULTIPLE_SELECT]:
                if not v or len(v) != 4:
                    raise ValueError("Multiple choice/select questions must have exactly 4 options")
        return v

class QuestionRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    standard: str = Field(..., min_length=1, max_length=50)
    subject: str = Field(..., min_length=1, max_length=100)
    chapter: str = Field(..., min_length=1, max_length=200)
    language: str = Field(default="English", min_length=1, max_length=50)
    question_distribution: QuestionDistribution
    difficulty_distribution: DifficultyDistribution
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class QuestionResponse(BaseModel):
    title: str
    questions: List[Question]
    metadata: Dict[str, str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)