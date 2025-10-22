# app/services/video_service.py
import os
import base64
import random
import logging
from typing import List, Dict
from pathlib import Path
from datetime import datetime
from app.config import settings
from app.schemas.video_schema import VideoAnalysisResponse
from app.services.api_service import APIService
from app.services.pdf_service import PDFService

logger = logging.getLogger(__name__)

class VideoService:
    def __init__(self):
        self.api_service = APIService()
        self.pdf_service = PDFService()
    
    def get_video_files(self, interview_id: str) -> List[str]:
        """Get all video files for a given interview_id"""
        video_folder = Path(settings.VIDEO_BASE_PATH) / interview_id
        
        if not video_folder.exists():
            logger.warning(f"Video folder not found: {video_folder}")
            return []
        
        # Supported video formats
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
        
        video_files = []
        for file in video_folder.iterdir():
            if file.is_file() and file.suffix.lower() in video_extensions:
                video_files.append(str(file))
        
        logger.info(f"Found {len(video_files)} video files for interview_id: {interview_id}")
        return video_files
    
    def select_random_videos(self, video_files: List[str], num_videos: int = None) -> List[str]:
        """Randomly select n videos from the list"""
        if num_videos is None:
            num_videos = settings.NUM_RANDOM_VIDEOS
        
        # If we have fewer videos than requested, return all
        if len(video_files) <= num_videos:
            logger.info(f"Selecting all {len(video_files)} videos (requested: {num_videos})")
            return video_files
        
        selected = random.sample(video_files, num_videos)
        logger.info(f"Randomly selected {len(selected)} videos from {len(video_files)} total")
        return selected
    
    def video_to_base64(self, video_path: str) -> str:
        """Convert video file to base64 encoded string"""
        try:
            with open(video_path, 'rb') as video_file:
                video_data = video_file.read()
                base64_data = base64.b64encode(video_data).decode('utf-8')
            logger.info(f"Successfully encoded video: {video_path}")
            return base64_data
        except Exception as e:
            logger.error(f"Error encoding video {video_path}: {e}")
            raise
    
    def analyze_videos(self, interview_id: str, num_videos: int = None) -> Dict:
        """Main method to analyze videos for an interview"""
        # Get all video files
        video_files = self.get_video_files(interview_id)
        
        if not video_files:
            return {
                "status": "error",
                "message": f"No videos found for interview_id: {interview_id}"
            }
        
        # Select random videos
        selected_videos = self.select_random_videos(video_files, num_videos)
        
        # Analyze each video
        analysis_results = []
        detailed_analyses = []
        
        for video_path in selected_videos:
            try:
                video_name = os.path.basename(video_path)
                logger.info(f"Processing video: {video_name}")
                
                # Convert to base64
                video_base64 = self.video_to_base64(video_path)
                
                # Call API
                analysis = self.api_service.analyze_video(video_base64, video_name)
                
                # Store both summary and detailed analysis
                analysis_results.append({
                    "video_name": video_name,
                    "genuinity_score": analysis.genuinity_score,
                    "total_duration": analysis.total_duration,
                    "total_penalty": analysis.total_penalty
                })
                
                detailed_analyses.append(analysis)
                
            except Exception as e:
                logger.error(f"Error processing video {video_path}: {e}")
                continue
        
        if not analysis_results:
            return {
                "status": "error",
                "message": "Failed to analyze any videos"
            }
        
        # Calculate average genuinity score
        avg_score = sum(r["genuinity_score"] for r in analysis_results) / len(analysis_results)
        
        # Generate PDF report
        try:
            pdf_path = self.pdf_service.generate_report(
                interview_id=interview_id,
                average_score=avg_score,
                individual_results=analysis_results,
                detailed_analyses=detailed_analyses
            )
            logger.info(f"PDF report generated: {pdf_path}")
        except Exception as e:
            logger.error(f"Failed to generate PDF report: {e}")
            pdf_path = None
        
        return {
            "interview_id": interview_id,
            "videos_analyzed": len(analysis_results),
            "average_genuinity_score": round(avg_score, 4),
            "individual_scores": analysis_results,
            "status": "success",
            "message": f"Successfully analyzed {len(analysis_results)} videos",
            "pdf_report_path": pdf_path
        }
