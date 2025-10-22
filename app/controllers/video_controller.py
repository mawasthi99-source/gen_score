# app/controllers/video_controller.py
from fastapi import HTTPException
import logging
from app.schemas.video_schema import AnalyzeRequest, AnalyzeResponse
from app.services.video_service import VideoService

logger = logging.getLogger(__name__)

class VideoController:
    def __init__(self):
        self.video_service = VideoService()
    
    async def analyze_interview(self, request: AnalyzeRequest) -> AnalyzeResponse:
        """
        Controller method to handle interview analysis
        """
        try:
            logger.info(f"Received analysis request for interview_id: {request.interview_id}")
            
            # Call service layer
            result = self.video_service.analyze_videos(
                interview_id=request.interview_id,
                num_videos=request.num_videos
            )
            
            if result["status"] == "error":
                raise HTTPException(status_code=404, detail=result["message"])
            
            return AnalyzeResponse(**result)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in controller: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
