# app/routes/video_routes.py
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from app.schemas.video_schema import AnalyzeRequest, AnalyzeResponse
from app.controllers.video_controller import VideoController
import os

router = APIRouter()

def get_video_controller():
    return VideoController()

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_videos(
    request: AnalyzeRequest,
    controller: VideoController = Depends(get_video_controller)
):
    """
    Analyze videos for a given interview_id
    
    - **interview_id**: The ID of the interview to analyze
    - **num_videos**: (Optional) Number of random videos to select. If not provided, uses config default
    
    Returns analysis results including average genuinity score and PDF report path
    """
    return await controller.analyze_interview(request)

@router.get("/test/{interview_id}")
async def test_video_path(interview_id: str):
    """
    Test endpoint to check if videos exist for an interview_id
    """
    from app.services.video_service import VideoService
    service = VideoService()
    videos = service.get_video_files(interview_id)
    
    return {
        "interview_id": interview_id,
        "videos_found": len(videos),
        "video_paths": videos
    }

@router.get("/download-report/{interview_id}")
async def download_report(interview_id: str):
    """
    Download the PDF report for a specific interview
    """
    from app.config import settings
    import glob
    
    # Find the latest report for this interview_id
    pattern = os.path.join(settings.PDF_OUTPUT_PATH, f"{interview_id}_*.pdf")
    reports = glob.glob(pattern)
    
    if not reports:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Get the most recent report
    latest_report = max(reports, key=os.path.getctime)
    
    return FileResponse(
        latest_report,
        media_type='application/pdf',
        filename=os.path.basename(latest_report)
    )
