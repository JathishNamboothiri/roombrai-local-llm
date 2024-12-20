# src/utils/helpers.py
import os
from pathlib import Path
import base64
from typing import Any, Dict, List, Optional
from models.question_models import QuestionRequest, QuestionType
from utils.logger import logger

def encode_image_to_base64(image_path: str) -> Optional[str]:
    """
    Encode an image file to base64 string.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Optional[str]: Base64 encoded string of the image, or None if encoding fails
    """
    try:
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
            return base64.b64encode(image_data).decode('utf-8')
    except Exception as e:
        logger.error(f"Error encoding image to base64: {str(e)}", {
            "image_path": image_path
        })
        return None

def validate_file_path(path: str) -> bool:
    """
    Validate if file path exists and is accessible.
    
    Args:
        path: File path to validate
        
    Returns:
        bool: True if path exists and is accessible, False otherwise
    """
    try:
        path_obj = Path(path)
        return path_obj.exists()
    except Exception as e:
        logger.error(f"Error validating file path: {str(e)}", {
            "path": path
        })
        return False

def get_images(base_path: str, filters: List[str] = [".jpg", ".jpeg", ".png"]) -> List[str]:
    """
    Retrieve a sorted list of image file paths based on the provided base path and filters.
    
    Args:
        base_path: Base directory path
        filters: List of valid file extensions to include
        
    Returns:
        List[str]: Sorted list of image file paths
    """
    try:
        if not validate_file_path(base_path):
            logger.error(f"Invalid base path: {base_path}")
            return []
            
        image_paths = []
        for root, _, files in os.walk(base_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in filters):
                    image_paths.append(os.path.join(root, file))
        
        sorted_paths = sorted(image_paths)
        logger.info(f"Found {len(sorted_paths)} images in {base_path}")
        return sorted_paths
        
    except Exception as e:
        logger.error(f"Error getting images: {str(e)}", {
            "base_path": base_path
        })
        return []

def format_prompt(context: str, question_type: str, count: int, request: QuestionRequest, difficulty_level: str) -> str:
    """
    Generate a detailed prompt for the model based on question type and context.
    
    Args:
        context: Extracted context from images
        question_type: Type of questions to generate
        count: Number of questions to generate
        request: Original request object
        difficulty_level: Difficulty level for questions
        
    Returns:
        str: Formatted prompt for the LLM
    """
    prompt = f"""Generate EXACTLY {count} NEW {question_type} questions at {difficulty_level} level based on the following context:

    {context}

    Chapter: {request.chapter}
    {f'Topic: {request.topic}' if request.topic else 'Scope: Entire chapter'}

    CRITICAL REQUIREMENTS:
    1. Generate EXACTLY {count} questions - no more, no less
    2. Each question must include all required fields
    3. All content must be in {request.language}
    4. All questions must be at {difficulty_level} difficulty level
    5. Questions must be based on the provided context
    """

    if question_type == QuestionType.MCQ.value:
        prompt += """
        Requirements for Multiple Choice Questions:
        - Include clear and unambiguous question text
        - EXACTLY 4 options per question
        - Only ONE correct answer
        - All options must be plausible and related to the topic
        Format:
        {
            "type": "Multiple Choice",
            "difficulty": "Easy/Medium/Hard",
            "question": "Question text",
            "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
            "correct_answer": "Correct option"
        }
        """
    elif question_type == QuestionType.MSQ.value:
        prompt += """
        Requirements for Multiple Select Questions:
        - Include clear question text indicating multiple selections
        - EXACTLY 4 options per question
        - EXACTLY 2 correct answers
        - All options must be plausible and related to the topic
        Format:
        {
            "type": "Multiple Select",
            "difficulty": "Easy/Medium/Hard",
            "question": "Question text",
            "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
            "correct_answers": ["Correct option 1", "Correct option 2"]
        }
        """
    elif question_type == QuestionType.SDQ.value:
        prompt += """
        Requirements for Short Descriptive Questions:
        - Questions should require 1-2 sentence answers
        - Include 3-5 relevant keywords
        - Answers should be concise and focused
        Format:
        {
            "type": "Short Descriptive Answer",
            "difficulty": "Easy/Medium/Hard",
            "question": "Question text",
            "answer": "1-2 sentence answer",
            "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
        }
        """
    else:  # LDQ
        prompt += """
        Requirements for Long Descriptive Questions:
        - Questions should require detailed explanations
        - Include 5-7 relevant keywords
        - Answers should be comprehensive paragraphs
        Format:
        {
            "type": "Long Descriptive Answer",
            "difficulty": "Easy/Medium/Hard",
            "question": "Question text",
            "answer": "Detailed paragraph answer",
            "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6", "keyword7"]
        }
        """

    prompt += """
    FINAL CHECKLIST:
    1. Verify EXACTLY the requested number of questions are generated
    2. Each question has all required fields
    3. Correct number of options/keywords as specified
    4. No duplicate questions
    5. All questions are at the specified difficulty level
    6. All content in specified language
    7. Questions should be challenging but fair for the given difficulty level

    Return ONLY a JSON array of questions without prefixes or decorators.
    """
    return prompt

def format_question_response(questions: List[Dict[str, Any]], request: QuestionRequest) -> Dict[str, Any]:
    """
    Format the final question response with metadata.
    
    Args:
        questions: List of generated questions
        request: Original request object
        
    Returns:
        Dict[str, Any]: Formatted response with questions and metadata
    """
    return {
        "title": f"{request.standard} {request.subject} Assessment - {request.chapter}",
        "questions": questions,
        "metadata": {
            "standard": request.standard,
            "subject": request.subject,
            "chapter": request.chapter,
            "language": request.language,
            "syllabus": request.syllabus,
            "total_questions": len(questions),
            "distribution": {
                "multiple_choice": request.question_distribution.multiple_choice,
                "multiple_select": request.question_distribution.multiple_select,
                "short_descriptive": request.question_distribution.short_descriptive,
                "long_descriptive": request.question_distribution.long_descriptive
            },
            "difficulty_distribution": {
                "easy": request.difficulty_distribution.easy,
                "medium": request.difficulty_distribution.medium,
                "hard": request.difficulty_distribution.hard
            }
        }
    }