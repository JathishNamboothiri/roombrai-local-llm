# src/api/error_handlers.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
from utils.exceptions import (
    BaseServiceError,
    LLMServiceError,
    ImageProcessingError,
    QuestionGenerationError,
    ValidationError
)
from utils.logger import logger

async def validation_error_handler(request: Request, exc: ValidationError):
    logger.error("Validation error", {
        "error": exc.message,
        "details": exc.errors,
        "path": request.url.path
    })
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Validation Error",
            "message": exc.message,
            "details": exc.errors
        }
    )

async def llm_service_error_handler(request: Request, exc: LLMServiceError):
    logger.error("LLM service error", {
        "error": str(exc),
        "path": request.url.path
    })
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": "LLM Service Error",
            "message": str(exc)
        }
    )

async def image_processing_error_handler(request: Request, exc: ImageProcessingError):
    logger.error("Image processing error", {
        "error": str(exc),
        "path": request.url.path
    })
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Image Processing Error",
            "message": str(exc)
        }
    )

async def question_generation_error_handler(request: Request, exc: QuestionGenerationError):
    logger.error("Question generation error", {
        "error": str(exc),
        "path": request.url.path
    })
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Question Generation Error",
            "message": str(exc)
        }
    )

# Function to add error handlers to the app
def add_error_handlers(app):
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.add_exception_handler(LLMServiceError, llm_service_error_handler)
    app.add_exception_handler(ImageProcessingError, image_processing_error_handler)
    app.add_exception_handler(QuestionGenerationError, question_generation_error_handler)