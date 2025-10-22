# app/main.py
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
