#!/usr/bin/env python3
"""
Video Analysis API - Project Setup Script (Without Database)
Run this script to create the complete project structure with all files.

Usage:
    python setup_project.py
"""

import os
import sys

# File contents as dictionary
FILES = {
    "app/__init__.py": "",
    
    "app/main.py": """# app/main.py
from fastapi import FastAPI
from app.routes import video_routes
from app.config import settings
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="Video Genuinity Analysis API",
    description="API for analyzing video genuinity scores and generating PDF reports",
    version="1.0.0"
)

# Include routers
app.include_router(video_routes.router, prefix="/api/v1", tags=["videos"])

@app.get("/")
async def root():
    return {
        "message": "Video Genuinity Analysis API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
""",

    "app/config.py": """# app/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Video folder configuration
    VIDEO_BASE_PATH: str = "/path/to/project/uploads/videos/internal"
    NUM_RANDOM_VIDEOS: int = 5
    
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
""",

    "app/controllers/__init__.py": "",

    "app/controllers/video_controller.py": """# app/controllers/video_controller.py
from fastapi import HTTPException
import logging
from app.schemas.video_schema import AnalyzeRequest, AnalyzeResponse
from app.services.video_service import VideoService

logger = logging.getLogger(__name__)

class VideoController:
    def __init__(self):
        self.video_service = VideoService()
    
    async def analyze_interview(self, request: AnalyzeRequest) -> AnalyzeResponse:
        \"\"\"
        Controller method to handle interview analysis
        \"\"\"
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
""",

    "app/routes/__init__.py": "",

    "app/routes/video_routes.py": """# app/routes/video_routes.py
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
    \"\"\"
    Analyze videos for a given interview_id
    
    - **interview_id**: The ID of the interview to analyze
    - **num_videos**: (Optional) Number of random videos to select. If not provided, uses config default
    
    Returns analysis results including average genuinity score and PDF report path
    \"\"\"
    return await controller.analyze_interview(request)

@router.get("/test/{interview_id}")
async def test_video_path(interview_id: str):
    \"\"\"
    Test endpoint to check if videos exist for an interview_id
    \"\"\"
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
    \"\"\"
    Download the PDF report for a specific interview
    \"\"\"
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
""",

    "app/schemas/__init__.py": "",

    "app/schemas/video_schema.py": """# app/schemas/video_schema.py
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
""",

    "app/services/__init__.py": "",

    "app/services/video_service.py": """# app/services/video_service.py
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
        \"\"\"Get all video files for a given interview_id\"\"\"
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
        \"\"\"Randomly select n videos from the list\"\"\"
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
        \"\"\"Convert video file to base64 encoded string\"\"\"
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
        \"\"\"Main method to analyze videos for an interview\"\"\"
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
""",

    "app/services/api_service.py": """# app/services/api_service.py
import requests
import logging
from datetime import datetime
from app.config import settings
from app.schemas.video_schema import VideoAnalysisResponse, DetailedError

logger = logging.getLogger(__name__)

class APIService:
    def analyze_video(self, video_base64: str, video_name: str) -> VideoAnalysisResponse:
        \"\"\"
        Analyze video using external API
        \"\"\"
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
            
            data = response.json()
            
            # Parse the response into our schema
            return VideoAnalysisResponse(
                video_name=video_name,
                total_duration=data.get("total_duration", 0),
                genuinity_score=data.get("genuinity_score", 0),
                total_penalty=data.get("total_penalty", 0),
                errors_summary=data.get("errors_summary", {}),
                detailed_errors=[
                    DetailedError(**error) for error in data.get("detailed_errors", [])
                ],
                analysis_timestamp=datetime.fromisoformat(
                    data.get("analysis_timestamp", datetime.now().isoformat())
                )
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API call failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Error parsing API response: {e}")
            raise
""",

    "app/services/pdf_service.py": """# app/services/pdf_service.py
import os
from datetime import datetime
from typing import List, Dict
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from app.config import settings
from app.schemas.video_schema import VideoAnalysisResponse
import logging

logger = logging.getLogger(__name__)

class PDFService:
    def __init__(self):
        # Create reports directory if it doesn't exist
        os.makedirs(settings.PDF_OUTPUT_PATH, exist_ok=True)
        
        # Define custom styles
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        self.normal_style = self.styles['Normal']
    
    def generate_report(
        self,
        interview_id: str,
        average_score: float,
        individual_results: List[Dict],
        detailed_analyses: List[VideoAnalysisResponse]
    ) -> str:
        \"\"\"Generate comprehensive PDF report\"\"\"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{interview_id}_{timestamp}.pdf"
        filepath = os.path.join(settings.PDF_OUTPUT_PATH, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Container for PDF elements
        elements = []
        
        # Add title
        elements.append(Paragraph(
            f"Video Analysis Report",
            self.title_style
        ))
        elements.append(Spacer(1, 0.2*inch))
        
        # Add header information
        header_data = [
            ["Interview ID:", interview_id],
            ["Report Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            ["Videos Analyzed:", str(len(individual_results))],
            ["Average Genuinity Score:", f"{average_score:.2f}/10"]
        ]
        
        header_table = Table(header_data, colWidths=[2.5*inch, 3.5*inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Add summary section
        elements.append(Paragraph("Summary", self.heading_style))
        
        # Score interpretation
        if average_score >= 8:
            score_text = "Excellent - High genuinity detected"
            score_color = colors.green
        elif average_score >= 6:
            score_text = "Good - Acceptable genuinity level"
            score_color = colors.orange
        else:
            score_text = "Poor - Multiple violations detected"
            score_color = colors.red
        
        summary_style = ParagraphStyle(
            'Summary',
            parent=self.normal_style,
            fontSize=12,
            textColor=score_color,
            spaceAfter=10
        )
        elements.append(Paragraph(f"<b>Assessment:</b> {score_text}", summary_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Add individual video scores table
        elements.append(Paragraph("Individual Video Scores", self.heading_style))
        
        video_data = [["#", "Video Name", "Duration (s)", "Score", "Penalty"]]
        for idx, result in enumerate(individual_results, 1):
            video_data.append([
                str(idx),
                result['video_name'][:30] + "..." if len(result['video_name']) > 30 else result['video_name'],
                f"{result['total_duration']:.1f}",
                f"{result['genuinity_score']:.2f}",
                f"{result['total_penalty']:.2f}"
            ])
        
        video_table = Table(video_data, colWidths=[0.5*inch, 2.5*inch, 1*inch, 1*inch, 1*inch])
        video_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        elements.append(video_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Add detailed analysis for videos with errors
        videos_with_errors = [
            analysis for analysis in detailed_analyses
            if len(analysis.detailed_errors) > 0
        ]
        
        if videos_with_errors:
            elements.append(PageBreak())
            elements.append(Paragraph("Detailed Error Analysis", self.heading_style))
            elements.append(Paragraph(
                f"The following {len(videos_with_errors)} video(s) had detected violations:",
                self.normal_style
            ))
            elements.append(Spacer(1, 0.2*inch))
            
            for analysis in videos_with_errors:
                # Video name header
                video_heading = ParagraphStyle(
                    'VideoHeading',
                    parent=self.normal_style,
                    fontSize=13,
                    textColor=colors.HexColor('#2c3e50'),
                    fontName='Helvetica-Bold',
                    spaceAfter=8
                )
                elements.append(Paragraph(f"Video: {analysis.video_name}", video_heading))
                elements.append(Paragraph(
                    f"Score: {analysis.genuinity_score:.2f}/10 | "
                    f"Duration: {analysis.total_duration:.1f}s | "
                    f"Total Penalty: {analysis.total_penalty:.2f}",
                    self.normal_style
                ))
                elements.append(Spacer(1, 0.1*inch))
                
                # Errors table
                if analysis.detailed_errors:
                    error_data = [["Error Type", "From (s)", "To (s)", "Duration (s)", "Confidence"]]
                    for error in analysis.detailed_errors:
                        duration = error.to_time - error.from_time
                        error_data.append([
                            error.error_type.replace('_', ' ').title(),
                            f"{error.from_time:.1f}",
                            f"{error.to_time:.1f}",
                            f"{duration:.1f}",
                            f"{error.confidence:.2f}"
                        ])
                    
                    error_table = Table(error_data, colWidths=[2*inch, 0.8*inch, 0.8*inch, 1*inch, 1*inch])
                    error_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.lightpink),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('FONTSIZE', (0, 1), (-1, -1), 8)
                    ]))
                    elements.append(error_table)
                
                # Error summary
                if analysis.errors_summary:
                    elements.append(Spacer(1, 0.15*inch))
                    elements.append(Paragraph("<b>Error Summary:</b>", self.normal_style))
                    
                    for error_type, summary in analysis.errors_summary.items():
                        if summary:
                            summary_text = f"• {error_type.replace('_', ' ').title()}: "
                            details = []
                            for key, value in summary.items():
                                details.append(f"{key}={value:.2f}")
                            summary_text += ", ".join(details)
                            elements.append(Paragraph(summary_text, self.normal_style))
                
                elements.append(Spacer(1, 0.3*inch))
        else:
            elements.append(Paragraph(
                "<b>No violations detected in any video!</b>",
                ParagraphStyle('GoodNews', parent=self.normal_style, textColor=colors.green, fontSize=12)
            ))
        
        # Add footer
        elements.append(PageBreak())
        elements.append(Spacer(1, 0.5*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=self.normal_style,
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        elements.append(Paragraph(
            f"Report generated by {settings.COMPANY_NAME}<br/>"
            f"Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}",
            footer_style
        ))
        
        # Build PDF
        doc.build(elements)
        logger.info(f"PDF report generated successfully: {filepath}")
        
        return filepath
""",

    "requirements.txt": """fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0
requests==2.31.0
python-dotenv==1.0.0
reportlab==4.0.7
""",

    ".env.example": """# .env.example
# Copy this file to .env and update with your actual values

# Video Configuration
VIDEO_BASE_PATH=/path/to/your/project/uploads/videos/internal
NUM_RANDOM_VIDEOS=5

# API Configuration
EXTERNAL_API_URL=http://127.0.0.1:8000/api/v1/analyze-video
EXTERNAL_API_TIMEOUT=300

# PDF Report Configuration
PDF_OUTPUT_PATH=./reports
COMPANY_NAME=Your Company Name
REPORT_LOGO_PATH=
""",

    ".gitignore": """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Environment
.env

# Reports
reports/
*.pdf

# IDEs
.vscode/
.idea/
*.swp
*.swo
*.sublime-project
*.sublime-workspace

# OS
.DS_Store
Thumbs.db

# Logs
*.log
""",

    "README.md": """# Video Genuinity Analysis API (No Database)

A FastAPI application that analyzes interview videos using an external proctoring API and generates comprehensive PDF reports.

## Features

- 🎥 Random video selection from interview folders
- 🔍 Integration with external video analysis API
- 📊 Comprehensive PDF report generation with timestamps
- 📈 Detailed error analysis and visualization
- 🎯 Average genuinity score calculation across multiple videos

## Quick Start

### 1. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your settings
```

**Important Configuration:**
- `VIDEO_BASE_PATH`: Path to folder containing interview folders (e.g., `/path/to/uploads/videos/internal`)
- `NUM_RANDOM_VIDEOS`: Number of videos to randomly analyze (default: 5)
- `EXTERNAL_API_URL`: Your proctoring API endpoint (default: `http://127.0.0.1:8000/api/v1/analyze-video`)
- `PDF_OUTPUT_PATH`: Where to save PDF reports (default: `./reports`)
- `COMPANY_NAME`: Your company name for PDF reports

### 4. Run the Application
```bash
uvicorn app.main:app --reload --port 8001
```

**Note:** Use a different port (8001) if your proctoring API is running on 8000.

### 5. Access API Documentation
Open http://localhost:8001/docs

## API Endpoints

### POST /api/v1/analyze
Analyze videos for an interview and generate PDF report.

**Request:**
```json
{
  "interview_id": "INT123",
  "num_videos": 5
}
```

**Response:**
```json
{
  "interview_id": "INT123",
  "videos_analyzed": 5,
  "average_genuinity_score": 7.8542,
  "individual_scores": [
    {
      "video_name": "video1.mp4",
      "genuinity_score": 8.2,
      "total_duration": 245.5,
      "total_penalty": 0.15
    }
  ],
  "status": "success",
  "message": "Successfully analyzed 5 videos",
  "pdf_report_path": "./reports/INT123_20251021_143022.pdf"
}
```

### GET /api/v1/test/{interview_id}
Test if videos exist for an interview.

### GET /api/v1/download-report/{interview_id}
Download the latest PDF report for an interview.

## Project Structure

```
video-analysis-api/
├── app/
│   ├── main.py              # FastAPI app initialization
│   ├── config.py            # Configuration management
│   ├── controllers/
│   │   └── video_controller.py
│   ├── routes/
│   │   └── video_routes.py  # API endpoints
│   ├── schemas/
│   │   └── video_schema.py  # Pydantic models
│   └── services/
│       ├── video_service.py # Video processing logic
│       ├── api_service.py   # External API calls
│       └── pdf_service.py   # PDF generation
├── reports/                 # Generated PDF reports
├── .env                     # Environment variables
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## How It Works

### 1. Video Folder Structure
```
VIDEO_BASE_PATH/
├── INT123/
│   ├── video1.mp4
│   ├── video2.mp4
│   └── video3.mp4
├── INT124/
│   └── video1.mp4
```

### 2. Analysis Flow
1. API receives interview_id
2. Finds all videos in the interview folder
3. Randomly selects N videos
4. Converts each video to base64
5. Sends to external proctoring API
6. Collects analysis results
7. Calculates average score
8. Generates PDF report
9. Returns results with report path

## Example Usage

```python
import requests

# Analyze interview videos
response = requests.post(
    "http://localhost:8001/api/v1/analyze",
    json={
        "interview_id": "INT123",
        "num_videos": 5
    }
)

result = response.json()
print(f"Average Score: {result['average_genuinity_score']}")
print(f"PDF Report: {result['pdf_report_path']}")
```

## Troubleshooting

### Videos Not Found
- Check `VIDEO_BASE_PATH` in .env file
- Ensure interview folder exists
- Verify video files have supported extensions

### API Connection Failed
- Check `EXTERNAL_API_URL` is correct
- Ensure proctoring API is running
- Verify API timeout settings

### PDF Generation Failed
- Check `PDF_OUTPUT_PATH` exists and is writable
- Ensure ReportLab is installed correctly

## License

[Your License]
""",
}


def create_file(filepath, content):
    """Create a file with the given content"""
    try:
        # Get the directory path
        directory = os.path.dirname(filepath)
        
        # Create directory if it doesn't exist and directory is not empty
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        # Write content to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ Created: {filepath}")
        return True
    except Exception as e:
        print(f"✗ Failed to create {filepath}: {e}")
        return False


def main():
    """Main function to create all project files"""
    print("=" * 60)
    print("Video Analysis API - Complete Project Setup")
    print("With PDF Report Generation (No Database)")
    print("=" * 60)
    print()
    
    # Get current directory
    current_dir = os.getcwd()
    print(f"Creating project in: {current_dir}")
    print()
    
    # Ask for confirmation
    response = input("Do you want to continue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Setup cancelled.")
        sys.exit(0)
    
    print()
    print("Creating project structure...")
    print("-" * 60)
    
    # Create all files
    success_count = 0
    total_count = len(FILES)
    
    for filepath, content in FILES.items():
        if create_file(filepath, content):
            success_count += 1
    
    print("-" * 60)
    print()
    
    # Summary
    print("=" * 60)
    print(f"Setup Complete: {success_count}/{total_count} files created")
    print("=" * 60)
    print()
    
    if success_count == total_count:
        print("✓ All files created successfully!")
        print()
        print("Next steps:")
        print()
        print("1. Create virtual environment:")
        print("   python -m venv venv")
        print()
        print("2. Activate virtual environment:")
        print("   - Linux/Mac: source venv/bin/activate")
        print("   - Windows: venv\\Scripts\\activate")
        print()
        print("3. Install dependencies:")
        print("   pip install -r requirements.txt")
        print()
        print("4. Configure environment:")
        print("   cp .env.example .env")
        print()
        print("5. Edit .env file with your settings:")
        print("   - VIDEO_BASE_PATH: Path to your videos folder")
        print("   - EXTERNAL_API_URL: Your proctoring API endpoint")
        print("   - COMPANY_NAME: Your company name for reports")
        print()
        print("6. Run the application:")
        print("   uvicorn app.main:app --reload --port 8001")
        print()
        print("7. Access API documentation:")
        print("   http://localhost:8001/docs")
        print()
        print("8. Test the endpoint:")
        print('   POST http://localhost:8001/api/v1/analyze')
        print('   Body: {"interview_id": "YOUR_INTERVIEW_ID", "num_videos": 5}')
        print()
        print("Key Features:")
        print("✓ Random video selection")
        print("✓ External API integration")
        print("✓ Comprehensive PDF reports")
        print("✓ Detailed error analysis")
        print("✓ No database required")
        print()
    else:
        print(f"⚠ Warning: Only {success_count}/{total_count} files were created")
        print("Please check the errors above and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
