import os
import uuid
import asyncio
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont
import edge_tts


BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

STATIC_DIR = "static"
VIDEO_DIR = "static/videos"
AUDIO_DIR = "static/audio"
IMAGE_DIR = "static/images"

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)

app = FastAPI(title="FactFlow API")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class GenerateVideoRequest(BaseModel):
    video_id: Optional[str] = None
    script: str
    image_prompts: List[str]
    caption: Optional[str] = None
    hashtags: List[str] = []


@app.get("/")
def health_check():
    return {
        "status": "ok",
        "message": "FactFlow API is running"
    }


def wrap_text(text: str, max_chars: int = 28) -> List[str]:
    words = text.split()
    lines = []
    current = ""

    for word in words:
        if len(current + " " + word) <= max_chars:
            current = f"{current} {word}".strip()
        else:
            lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines[:5]


def create_image(text: str, output_path: str):
    width, height = 1080, 1920
    img = Image.new("RGB", (width, height), color=(10, 18, 35))
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 58)
        font_body = ImageFont.truetype("DejaVuSans.ttf", 42)
    except:
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()

    title = "FactFlow AI"
    draw.text((60, 120), title, fill=(255, 255, 255), font=font_title)

    lines = wrap_text(text, max_chars=26)
    y = 700

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_body)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        draw.text((x, y), line, fill=(230, 240, 255), font=font_body)
        y += 70

    draw.text(
        (60, 1700),
        "Follow for more curious facts",
        fill=(170, 210, 255),
        font=font_body
    )

    img.save(output_path)


async def generate_voice(text: str, output_path: str):
    voice = "vi-VN-NamMinhNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


def create_video_from_assets(image_paths: List[str], audio_path: str, output_path: str):
    audio = AudioFileClip(audio_path)
    duration = audio.duration

    scene_duration = duration / len(image_paths)

    clips = []
    for image_path in image_paths:
        clip = (
            ImageClip(image_path)
            .set_duration(scene_duration)
            .resize((1080, 1920))
            .fadein(0.3)
            .fadeout(0.3)
        )
        clips.append(clip)

    final_video = concatenate_videoclips(clips, method="compose")
    final_video = final_video.set_audio(audio)
    final_video.write_videofile(
        output_path,
        fps=30,
        codec="libx264",
        audio_codec="aac"
    )

    audio.close()
    final_video.close()


@app.post("/generate-video")
async def generate_video(data: GenerateVideoRequest):
    try:
        video_id = data.video_id or str(uuid.uuid4())

        audio_path = f"{AUDIO_DIR}/{video_id}.mp3"
        video_path = f"{VIDEO_DIR}/{video_id}.mp4"

        await generate_voice(data.script, audio_path)

        image_paths = []
        prompts = data.image_prompts or [data.script]

        for index, prompt in enumerate(prompts[:5]):
            image_path = f"{IMAGE_DIR}/{video_id}_{index}.png"
            create_image(prompt, image_path)
            image_paths.append(image_path)

        create_video_from_assets(image_paths, audio_path, video_path)

        video_url = f"{BASE_URL}/static/videos/{video_id}.mp4"

        return {
            "success": True,
            "message": "Video generated successfully",
            "video_id": video_id,
            "video_url": video_url,
            "video_path": video_path,
            "created_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }