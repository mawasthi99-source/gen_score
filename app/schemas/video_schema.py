# app/schemas/video_schema.py
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

class DetailedError(BaseModel):
    error_type: str
    from_time: float
    to_time: float
    confidence: float

class VideoAnalysisResponse(BaseModel):
    video_name: str
    total_duration: float
    genuinity_score: float
    total_penalty: float
    errors_summary: Dict[str, Dict[str, float]]
    detailed_errors: List[DetailedError]
    analysis_timestamp: datetime

class AnalyzeRequest(BaseModel):
    interview_id: str
    num_videos: Optional[int] = None

class AnalyzeResponse(BaseModel):
    interview_id: str
    videos_analyzed: int
    average_genuinity_score: float
    individual_scores: List[Dict]
    status: str
    message: str
    pdf_report_path: Optional[str] = None
