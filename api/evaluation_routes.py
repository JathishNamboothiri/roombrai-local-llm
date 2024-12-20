# src/api/evaluation_routes.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime

from models.evaluation_models import (
    AnswersEvaluationRequest,
    EvaluationResult
)
from services.evaluation_services import EvaluationService
from utils.exceptions import ValidationError, LLMServiceError
from utils.logger import logger, log_async_function_call

# Create router with prefix
evaluation_router = APIRouter(
    prefix="/evaluation",
    tags=["evaluation"]
)

@evaluation_router.post("/evaluate-answers", response_model=Dict[str, Any])
@log_async_function_call
async def evaluate_answers(request: AnswersEvaluationRequest):
    """
    Evaluate student answers against expected answers using few-shot prompting.
    
    Args:
        request (AnswersEvaluationRequest): Contains:
            - number_of_pairs: Number of answer pairs to evaluate
            - answer_pairs: List of expected and student answer pairs
            
    Returns:
        Dict containing:
            - results: List of evaluation results with scores and justifications
            - metadata: Evaluation statistics and timestamp
            
    Raises:
        HTTPException: 
            - 400: For validation errors
            - 503: For LLM service errors
            - 500: For unexpected errors
    """
    try:
        logger.info("Received answer evaluation request", {
            "number_of_pairs": request.number_of_pairs,
            "endpoint": "/evaluate-answers"
        })
        
        evaluation_service = EvaluationService()
        result = await evaluation_service.evaluate_answers(request)
        
        logger.info("Successfully completed answer evaluation", {
            "successful_evaluations": result["metadata"]["successful_evaluations"],
            "average_score": result["metadata"]["average_score"]
        })
        
        return result
        
    except ValidationError as e:
        logger.error("Validation error in answer evaluation", {
            "error": str(e),
            "details": e.details if hasattr(e, 'details') else None
        })
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Invalid request parameters",
                "details": e.details if hasattr(e, 'details') else [str(e)]
            }
        )
        
    except LLMServiceError as e:
        logger.error("LLM service error in answer evaluation", {
            "error": str(e)
        })
        raise HTTPException(
            status_code=503,
            detail={
                "message": "Answer evaluation service temporarily unavailable",
                "details": [str(e)]
            }
        )
        
    except Exception as e:
        logger.error("Unexpected error in answer evaluation", {
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Internal server error",
                "details": ["An unexpected error occurred"]
            }
        )
    
    finally:
        logger.info("Answer evaluation request completed", {
            "endpoint": "/evaluate-answers",
            "timestamp": datetime.utcnow().isoformat()
        })

# You would include this router in your main.py like this:
"""
# src/main.py
from fastapi import FastAPI
from api.evaluation_routes import evaluation_router

app = FastAPI()
app.include_router(evaluation_router)
"""

# Example usage:
"""
curl -X POST "http://localhost:8000/api/v1/evaluation/evaluate-answers" \
    -H "Content-Type: application/json" \
    -d '{
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
    }'
"""