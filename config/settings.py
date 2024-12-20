# src/config/settings.py
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """Application settings and configuration."""
    
    # Base Configuration
    API_TITLE: str = "Question Paper Generator API"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Directory Configuration
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    CONTENT_DIR: Path = Path("/Users/developer/Desktop/que/Root/Pdf")
    
    # LLM Model Settings
    LLM_MODEL: str = "llama3.2-vision"
    MAX_RETRIES: int = 3
    REQUEST_TIMEOUT: int = 300

    # Question Generation Settings
    MAX_QUESTIONS: int = 25
    MAX_LONG_DESCRIPTIVE: int = 10
    
    # Content Structure Settings
    SUPPORTED_LANGUAGES: List[str] = ["English"]
    SUPPORTED_ROLES: List[str] = ["Teacher", "Student"]
    SUPPORTED_SYLLABI: List[str] = ["NCERT"]
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DIR: Path = BASE_DIR / "logs"
    LOG_FILE: Path = LOG_DIR / "app.log"
    ERROR_LOG_FILE: Path = LOG_DIR / "error.log"
    
    class Config:
        env_file = ".env"
        arbitrary_types_allowed = True
        extra = "ignore" 

    def __init__(self):
        super().__init__()
        # Create necessary directories
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()