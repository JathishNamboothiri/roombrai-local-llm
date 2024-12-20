# src/api/__init__.py
from .qp_gen_routes import router as qp_router
from .evaluation_routes import evaluation_router
from .error_handlers import add_error_handlers

__all__ = [
    "qp_router",
    "evaluation_router",
    "add_error_handlers"
]

# Version of the API
__version__ = "1.0.0"

# You can also add additional metadata
__author__ = "Jathish Namboothiri"
__description__ = "Question Paper Generator and Answer Evaluation API"