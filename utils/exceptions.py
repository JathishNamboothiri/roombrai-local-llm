# src/utils/exceptions.py
from typing import List, Optional

class BaseServiceError(Exception):
    """Base exception class for all service-level exceptions."""
    def __init__(self, message: str, service_name: str = None):
        self.message = message
        self.service_name = service_name
        super().__init__(self.message)

class ValidationError(BaseServiceError):
    """Exception raised for validation errors."""
    def __init__(self, message: str, details: Optional[List[str]] = None):
        super().__init__(
            message=message,
            service_name="Validation"
        )
        self.details = details or []
        self.status_code = 400
        self.error_code = "VALIDATION_ERROR"

class LLMServiceError(BaseServiceError):
    """Exception raised for errors in LLM service."""
    def __init__(self, message: str, details: Optional[List[str]] = None):
        super().__init__(
            message=message,
            service_name="LLMService"
        )
        self.details = details or []
        self.status_code = 503
        self.error_code = "LLM_SERVICE_ERROR"

class ImageProcessingError(BaseServiceError):
    """Exception raised for errors in image processing."""
    def __init__(self, message: str, details: Optional[List[str]] = None):
        super().__init__(
            message=message,
            service_name="ImageService"
        )
        self.details = details or []
        self.status_code = 500
        self.error_code = "IMAGE_PROCESSING_ERROR"

class QuestionGenerationError(BaseServiceError):
    """Exception raised for errors in question generation."""
    def __init__(self, message: str, details: Optional[List[str]] = None):
        super().__init__(
            message=message,
            service_name="QuestionService"
        )
        self.details = details or []
        self.status_code = 500
        self.error_code = "QUESTION_GENERATION_ERROR"

class ResourceNotFoundError(BaseServiceError):
    """Exception raised when a requested resource is not found."""
    def __init__(self, message: str, resource_type: str = None):
        super().__init__(
            message=message,
            service_name="ResourceService"
        )
        self.resource_type = resource_type
        self.status_code = 404
        self.error_code = "RESOURCE_NOT_FOUND"

class ConfigurationError(BaseServiceError):
    """Exception raised for configuration-related issues."""
    def __init__(self, message: str, config_key: str = None):
        super().__init__(
            message=message,
            service_name="Configuration"
        )
        self.config_key = config_key
        self.status_code = 500
        self.error_code = "CONFIGURATION_ERROR"