# src/api/routes.py

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Dict, Any
from models.question_models import QuestionRequest, QuestionResponse
from services.question_service import QuestionService
from utils.exceptions import QuestionGenerationError, ValidationError
from utils.logger import logger, log_async_function_call
from utils.validators import validate_request


router = APIRouter(
                   prefix="/qp-generation", 
                   tags=["questions"]
                   )

@router.post("/generate-questions", response_model=QuestionResponse)
@log_async_function_call
async def generate_questions(request: QuestionRequest):
    """
    Generate questions based on indexed chapter content.
    
    Args:
        request: QuestionRequest containing:
            - standard: Educational standard (e.g., "10th")
            - subject: Subject name
            - chapter: Chapter name
            - language: Content language (default: "English")
            - syllabus: Syllabus type (default: "NCERT")
            - question_type: Type of questions to generate
            - num_questions: Number of questions to generate
            - difficulty_level: Difficulty level of questions
            
    Returns:
        QuestionResponse containing generated questions and metadata
    """
    try:
        logger.info("Received question generation request", {
            "request": request.model_dump(),
            "endpoint": "/generate-questions"
        })

        question_service = QuestionService()
        result = await question_service.generate_questions(request)
        
        logger.info("Successfully generated questions", {
            "question_count": len(result.questions),
            "chapter": request.chapter,
            "subject": request.subject
        })
        
        return result
        
    except ValidationError as e:
        logger.error("Validation error", {
            "error": str(e),
            "request_id": request.request_id
        })
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Invalid request parameters",
                "details": e.details if hasattr(e, 'details') else [str(e)]
            }
        )
        
    except QuestionGenerationError as e:
        logger.error("Question generation error", {
            "error": str(e),
            "request_id": request.request_id
        })
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to generate questions",
                "details": [str(e)]
            }
        )
        
    except Exception as e:
        logger.error("Unexpected error", {
            "error": str(e),
            "type": type(e).__name__,
            "request_id": request.request_id
        })
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Internal server error",
                "details": ["An unexpected error occurred"]
            }
        )

@router.get("/health")
async def health_check():
    """
    Health check endpoint for the API.
    """
    return {"status": "healthy", "service": "question-generator"}