# src/utils/__init__.py
from .logger import logger, log_function_call, log_async_function_call
from .exceptions import (
    BaseServiceError,
    ValidationError,
    LLMServiceError,
    QuestionGenerationError,
    ImageProcessingError,
    ResourceNotFoundError,
    ConfigurationError
)
from .validators import (
    validate_request, 
    validate_questions,
    _validate_mcq,
    _validate_descriptive
)
from .helpers import (
    format_prompt,
    encode_image_to_base64,

    format_question_response,
    validate_file_path,
    get_images
)

__all__ = [
    # Logging
    "logger",
    "log_function_call",
    "log_async_function_call",
    
    # Exceptions
    "BaseServiceError",
    "ValidationError",
    "LLMServiceError",
    "QuestionGenerationError",
    "ImageProcessingError",
    "ResourceNotFoundError",
    "ConfigurationError",
    
    # Validators
    "validate_request",
    "validate_questions",
    "_validate_mcq",
    "_validate_descriptive",
    
    # Helpers
    "format_prompt",
    "encode_image_to_base64",

    "format_question_response",
    "validate_file_path",
    "get_images"
]