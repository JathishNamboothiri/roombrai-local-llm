# src/utils/constants.py
from enum import Enum

class ErrorCodes(Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    LLM_ERROR = "LLM_ERROR"
    IMAGE_PROCESSING_ERROR = "IMAGE_PROCESSING_ERROR"
    SYSTEM_ERROR = "SYSTEM_ERROR"

class ErrorMessages:
    VALIDATION_ERROR = "Input validation failed"
    LLM_ERROR = "Error generating questions using LLM"
    IMAGE_PROCESSING_ERROR = "Error processing images"
    SYSTEM_ERROR = "Internal system error"