# src/utils/logger.py
import logging
import logging.handlers
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
import traceback
from functools import wraps
import time
from config.settings import settings

class CustomJSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage()
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        return json.dumps(log_data)

class Logger:
    """
    Custom logger class with enhanced functionality.
    """
    def __init__(self):
        self._setup_logging()
        self.logger = logging.getLogger("app")

    def _setup_logging(self) -> None:
        """
        Sets up logging configuration.
        """
        # Create logs directory if it doesn't exist
        log_dir = Path(settings.LOG_FILE).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        # Create root logger
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(CustomJSONFormatter())
        logger.addHandler(console_handler)

        # File handler
        file_handler = logging.handlers.RotatingFileHandler(
            settings.LOG_FILE,
            maxBytes=10485760,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(CustomJSONFormatter())
        logger.addHandler(file_handler)

        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            settings.LOG_FILE.parent / "error.log",
            maxBytes=10485760,
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(CustomJSONFormatter())
        logger.addHandler(error_handler)

    def log_with_context(self, level: int, message: str, extra: Dict[str, Any] = None) -> None:
        """
        Logs a message with additional context.
        """
        if extra is None:
            extra = {}
        
        record = logging.LogRecord(
            name="app",
            level=level,
            pathname=__file__,
            lineno=0,
            msg=message,
            args=(),
            exc_info=None
        )
        record.extra_data = extra
        
        self.logger.handle(record)

    def info(self, message: str, extra: Dict[str, Any] = None) -> None:
        """Log info message with context."""
        self.log_with_context(logging.INFO, message, extra)

    def error(self, message: str, extra: Dict[str, Any] = None) -> None:
        """Log error message with context."""
        self.log_with_context(logging.ERROR, message, extra)

    def warning(self, message: str, extra: Dict[str, Any] = None) -> None:
        """Log warning message with context."""
        self.log_with_context(logging.WARNING, message, extra)

    def debug(self, message: str, extra: Dict[str, Any] = None) -> None:
        """Log debug message with context."""
        self.log_with_context(logging.DEBUG, message, extra)

# Create logger instance
logger = Logger()

# Decorators for logging
def log_function_call(func):
    """
    Decorator to log function calls with timing.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        func_name = func.__name__
        
        logger.info(
            f"Calling function: {func_name}",
            {"arguments": {"args": str(args), "kwargs": str(kwargs)}}
        )
        
        try:
            result = func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            logger.info(
                f"Function {func_name} completed",
                {
                    "execution_time_ms": execution_time,
                    "success": True
                }
            )
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(
                f"Function {func_name} failed",
                {
                    "execution_time_ms": execution_time,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise
            
    return wrapper

def log_async_function_call(func):
    """
    Decorator to log async function calls with timing.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        func_name = func.__name__
        
        logger.info(
            f"Calling async function: {func_name}",
            {"arguments": {"args": str(args), "kwargs": str(kwargs)}}
        )
        
        try:
            result = await func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000
            
            logger.info(
                f"Async function {func_name} completed",
                {
                    "execution_time_ms": execution_time,
                    "success": True
                }
            )
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(
                f"Async function {func_name} failed",
                {
                    "execution_time_ms": execution_time,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise
            
    return wrapper

# Usage Example:
"""
from utils.logger import logger, log_function_call, log_async_function_call

# Regular function logging
@log_function_call
def process_data(data):
    logger.info("Processing data", {"data_size": len(data)})
    # Process data
    return result

# Async function logging
@log_async_function_call
async def generate_questions(request):
    logger.info("Generating questions", {"request": request.dict()})
    try:
        # Generate questions
        return result
    except Exception as e:
        logger.error("Question generation failed", {"error": str(e)})
        raise
"""