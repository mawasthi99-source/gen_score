import requests
import logging
from datetime import datetime
from app.config import settings
from app.schemas.video_schema import VideoAnalysisResponse, DetailedError

logger = logging.getLogger(__name__)

class APIService:
    def analyze_video(self, video_base64: str, video_name: str) -> VideoAnalysisResponse:
        """
        Analyze video using external API
        """
        logger.info(f"Calling API for video: {video_name}")
        
        try:
            payload = {
                "video_blob": video_base64
            }
            
            response = requests.post(
                settings.EXTERNAL_API_URL,
                json=payload,
                timeout=settings.EXTERNAL_API_TIMEOUT
            )
            
            response.raise_for_status()
            
            response_json = response.json()
            
            # Log the response status
            logger.info(f"API Response Status: {response_json.get('status')} - {response_json.get('message')}")
            
            # Extract data from the nested "data" object
            data = response_json.get("data", {})
            
            if not data:
                logger.error(f"No data in API response for {video_name}")
                raise ValueError("API response missing 'data' field")
            
            # Log the scores
            logger.info(f"Video: {video_name} | Score: {data.get('genuinity_score')} | Duration: {data.get('total_duration')} | Penalty: {data.get('total_penalty')}")
            
            # Parse the response into our schema
            return VideoAnalysisResponse(
                video_name=video_name,
                total_duration=float(data.get("total_duration", 0.0)),
                genuinity_score=float(data.get("genuinity_score", 0.0)),
                total_penalty=float(data.get("total_penalty", 0.0)),
                errors_summary=data.get("errors_summary", {}),
                detailed_errors=[
                    DetailedError(**error) for error in data.get("detailed_errors", [])
                ],
                analysis_timestamp=datetime.fromisoformat(
                    data.get("analysis_timestamp", datetime.now().isoformat())
                )
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API call failed for {video_name}: {e}")
            raise
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing API response for {video_name}: {e}")
            logger.error(f"Response: {response_json}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error for {video_name}: {e}")
            raise