# src/utils/exceptions.py
from typing import List


class BaseServiceError(Exception):
    """Base class for service exceptions."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class LLMServiceError(BaseServiceError):
    """Exception raised for errors in LLM service."""
    pass

class ImageProcessingError(BaseServiceError):
    """Exception raised for errors in image processing."""
    pass

class QuestionGenerationError(BaseServiceError):
    """Exception raised for errors in question generation."""
    pass

class ValidationError(BaseServiceError):
    """Exception raised for validation errors."""
    def __init__(self, message: str, errors: List[str] = None):
        super().__init__(message)
        self.errors = errors or []