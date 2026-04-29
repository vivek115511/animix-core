import os
import shutil
import subprocess
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

os.makedirs("processed_videos", exist_ok=True)
app.mount("/videos", StaticFiles(directory="processed_videos"), name="videos")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.post("/upload")
async def handle_upload(
    request: Request, 
    video_file: UploadFile = File(...),
    start_time: int = Form(...),  
    end_time: int = Form(...),
    aspect_ratio: str = Form(...),
    quality: str = Form(...)
): 
    input_path = f"processed_videos/raw_{video_file.filename}"
    output_filename = f"short_{video_file.filename.split('.')[0]}.mp4"
    output_path = f"processed_videos/{output_filename}"

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(video_file.file, buffer)

    # Calculate duration
    duration = end_time - start_time
    
    # Build the FFmpeg command (Ultra-fast and low memory)
    # This trims and resizes in one shot
    cmd = [
        "ffmpeg", "-y", "-ss", str(start_time), "-t", str(duration),
        "-i", input_path, "-vf", 
        "scale=-1:480" if quality == "480p" else "scale=-1:720",
        "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", output_path
    ]

    try:
        subprocess.run(cmd, check=True)
        return templates.TemplateResponse("result.html", {"request": request, "video_name": output_filename})
    except Exception as e:
        return HTMLResponse(content=f"FFmpeg Error: {str(e)}", status_code=500)
