# app/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Video folder configuration
    VIDEO_BASE_PATH: str = "/path/to/project/uploads/videos/internal"
    NUM_RANDOM_VIDEOS: int = 2
    
    # API Configuration
    EXTERNAL_API_URL: str = "http://127.0.0.1:8000/api/v1/analyze-video"
    EXTERNAL_API_TIMEOUT: int = 300  # seconds
    
    # PDF Report Configuration
    PDF_OUTPUT_PATH: str = "./reports"
    COMPANY_NAME: str = "Your Company Name"
    REPORT_LOGO_PATH: Optional[str] = None  # Optional: path to company logo
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
