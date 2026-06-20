from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from datetime import datetime

app = FastAPI(title="FactFlow API")


class GenerateVideoRequest(BaseModel):
    video_id: str | None = None
    script: str
    image_prompts: List[str]
    caption: str | None = None
    hashtags: List[str] = []


@app.get("/")
def health_check():
    return {
        "status": "ok",
        "message": "FactFlow API is running"
    }


@app.post("/generate-video")
def generate_video(data: GenerateVideoRequest):
    return {
        "success": True,
        "message": "Video generation endpoint is working",
        "video_id": data.video_id,
        "received_script": data.script,
        "image_prompts_count": len(data.image_prompts),
        "video_url": "https://example.com/demo-video.mp4",
        "duration": 30,
        "created_at": datetime.utcnow().isoformat()
    }