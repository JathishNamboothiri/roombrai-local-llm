# src/models/evaluation_models.py
from pydantic import BaseModel, Field, validator
from typing import List
from datetime import datetime

class AnswerPair(BaseModel):
    expected_answer: str = Field(..., min_length=1)
    student_answer: str = Field(..., min_length=1)

    @validator('expected_answer', 'student_answer')
    def validate_answers(cls, v):
        if not v.strip():
            raise ValueError("Answer cannot be empty or whitespace")
        return v.strip()

class AnswersEvaluationRequest(BaseModel):
    number_of_pairs: int = Field(..., gt=0)
    answer_pairs: List[AnswerPair]

    @validator('answer_pairs')
    def validate_pairs(cls, v, values):
        if 'number_of_pairs' in values and len(v) != values['number_of_pairs']:
            raise ValueError(f"Number of pairs ({values['number_of_pairs']}) does not match actual pairs provided ({len(v)})")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "number_of_pairs": 2,
                "answer_pairs": [
                    {
                        "expected_answer": "The process of photosynthesis converts light energy into chemical energy, producing glucose and oxygen from carbon dioxide and water.",
                        "student_answer": "Photosynthesis is how plants make food using sunlight, turning CO2 and water into sugar and oxygen."
                    },
                    {
                        "expected_answer": "Newton's First Law states that an object will remain at rest or in uniform motion unless acted upon by an external force.",
                        "student_answer": "Newton's First Law says things stay still or keep moving unless a force acts on them."
                    }
                ]
            }
        }

class EvaluationResult(BaseModel):
    score: float = Field(..., ge=0, le=100)
    justification: str = Field(..., min_length=1)

class EvaluationResponse(BaseModel):
    results: List[EvaluationResult]
    metadata: dict = Field(default_factory=lambda: {
        "timestamp": datetime.utcnow().isoformat()
    })