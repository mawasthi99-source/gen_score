# Video Genuinity Analysis API (No Database)

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
source venv/bin/activate  # Windows: venv\Scripts\activate
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
