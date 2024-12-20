# src/utils/validators.py
from typing import List, Dict
from pathlib import Path
from models.question_models import (
    QuestionRequest,
    QuestionType,
    DifficultyLevel,
    Question
)
from utils.exceptions import ValidationError
from utils.helpers import get_images
from utils.logger import logger
from config.settings import settings

async def validate_request(request: QuestionRequest) -> None:
    """Validate the question generation request."""
    errors = []
    
    try:
        # Validate question counts and distribution
        total_questions = (
            request.question_distribution.multiple_choice +
            request.question_distribution.multiple_select +
            request.question_distribution.short_descriptive +
            request.question_distribution.long_descriptive
        )
        
        if total_questions == 0:
            errors.append("At least one question type must be requested")
            
        # Validate difficulty distribution
        total_difficulty = (
            request.difficulty_distribution.easy +
            request.difficulty_distribution.medium +
            request.difficulty_distribution.hard
        )
        
        if total_difficulty != total_questions:
            errors.append(
                f"Difficulty distribution ({total_difficulty}) must match total questions ({total_questions})"
            )

        # Validate long descriptive questions limit
        if request.question_distribution.long_descriptive > settings.MAX_LONG_DESCRIPTIVE:
            errors.append(f"Number of long descriptive questions cannot exceed {settings.MAX_LONG_DESCRIPTIVE}")

        # Validate content path exists
        content_path = (settings.CONTENT_DIR / 
                       request.language / 
                       "Teacher" /
                       request.syllabus / 
                       request.standard / 
                       request.subject / 
                       request.chapter)

        if not content_path.exists() or not content_path.is_dir():
            errors.append(f"Content not found for: {request.standard}/{request.subject}/{request.chapter}")
        else:
            # Check for images
            image_files = get_images(str(content_path), [".jpg", ".jpeg", ".png"])
            if not image_files:
                errors.append(f"No images found for chapter: {request.chapter}")

        if errors:
            raise ValidationError("Request validation failed", errors)

    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Unexpected validation error: {str(e)}")
        raise ValidationError("Request validation failed", [str(e)])

def validate_questions(questions: List[Dict], request: QuestionRequest) -> None:
    """Validate generated questions."""
    errors = []
    
    # Count questions by type
    type_counts = {
        QuestionType.MULTIPLE_CHOICE: 0,
        QuestionType.MULTIPLE_SELECT: 0,
        QuestionType.SHORT_DESCRIPTIVE: 0,
        QuestionType.LONG_DESCRIPTIVE: 0
    }
    
    for idx, question in enumerate(questions, 1):
        try:
            # Validate basic structure
            if not isinstance(question, dict):
                errors.append(f"Question {idx}: Invalid format")
                continue
                
            # Validate question type
            q_type = question.get('type')
            if not q_type or q_type not in [t.value for t in QuestionType]:
                errors.append(f"Question {idx}: Invalid question type")
                continue
                
            # Update count
            type_counts[QuestionType(q_type)] += 1
            
            # Type-specific validation
            if q_type in [QuestionType.MULTIPLE_CHOICE.value, QuestionType.MULTIPLE_SELECT.value]:
                _validate_mcq(question, idx, errors)
            elif q_type == QuestionType.SHORT_DESCRIPTIVE.value:
                _validate_descriptive(question, idx, errors, short=True)
            elif q_type == QuestionType.LONG_DESCRIPTIVE.value:
                _validate_descriptive(question, idx, errors, short=False)
                
        except Exception as e:
            errors.append(f"Question {idx}: Validation error - {str(e)}")
            
    # Validate counts match request
    if type_counts[QuestionType.MULTIPLE_CHOICE] != request.question_distribution.multiple_choice:
        errors.append("Incorrect number of multiple choice questions")
    if type_counts[QuestionType.MULTIPLE_SELECT] != request.question_distribution.multiple_select:
        errors.append("Incorrect number of multiple select questions")
    if type_counts[QuestionType.SHORT_DESCRIPTIVE] != request.question_distribution.short_descriptive:
        errors.append("Incorrect number of short descriptive questions")
    if type_counts[QuestionType.LONG_DESCRIPTIVE] != request.question_distribution.long_descriptive:
        errors.append("Incorrect number of long descriptive questions")
        
    if errors:
        raise ValidationError("Question validation failed", errors)

def _validate_mcq(question: Dict, idx: int, errors: List[str]) -> None:
    """Validate multiple choice/select questions."""
    if not question.get('options') or len(question['options']) != 4:
        errors.append(f"Question {idx}: Must have exactly 4 options")
        
    if question['type'] == QuestionType.MULTIPLE_CHOICE.value:
        if 'correct_answer' not in question:
            errors.append(f"Question {idx}: Missing correct answer")
        elif question['correct_answer'] not in question['options']:
            errors.append(f"Question {idx}: Correct answer must be one of the options")
            
    if question['type'] == QuestionType.MULTIPLE_SELECT.value:
        if 'correct_answers' not in question:
            errors.append(f"Question {idx}: Missing correct answers")
        elif len(question['correct_answers']) != 2:
            errors.append(f"Question {idx}: Must have exactly 2 correct answers")
        elif not all(ans in question['options'] for ans in question['correct_answers']):
            errors.append(f"Question {idx}: All correct answers must be in options")

def _validate_descriptive(question: Dict, idx: int, errors: List[str], short: bool) -> None:
    """Validate descriptive questions."""
    if 'answer' not in question:
        errors.append(f"Question {idx}: Missing answer")
        
    if not question.get('keywords'):
        errors.append(f"Question {idx}: Missing keywords")
    elif short and not (3 <= len(question['keywords']) <= 5):
        errors.append(f"Question {idx}: Short descriptive must have 3-5 keywords")
    elif not short and not (5 <= len(question['keywords']) <= 7):
        errors.append(f"Question {idx}: Long descriptive must have 5-7 keywords")