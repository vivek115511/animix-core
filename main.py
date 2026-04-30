import os
import shutil
import subprocess
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# 1. SETUP FOLDERS
os.makedirs("processed_videos", exist_ok=True)
os.makedirs("templates", exist_ok=True)

app.mount("/videos", StaticFiles(directory="processed_videos"), name="videos")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request, "home.html")

@app.post("/upload")
async def handle_upload(
    request: Request, 
    video_file: UploadFile = File(...),
    start_time: int = Form(0),  
    end_time: int = Form(15), # Default to 15s for Lite version
    export_type: str = Form("video"), 
    aspect_ratio: str = Form("landscape"),
    quality: str = Form("480p"),          
    remove_audio: str = Form(None)
): 
    base_name = video_file.filename.split('.')[0].replace(" ", "_")
    input_path = f"processed_videos/raw_{video_file.filename}"
    
    ext = "mp4" if export_type == "video" else "mp3"
    output_filename = f"animix_lite_{base_name}.{ext}"
    output_path = f"processed_videos/{output_filename}"

    # Memory-Safe Reading
    with open(input_path, "wb") as buffer:
        while chunk := await video_file.read(1024 * 1024):
            buffer.write(chunk)

    duration = max(1, end_time - start_time)
    
    # Fast Processing Command
    cmd = ["ffmpeg", "-y", "-ss", str(start_time), "-t", str(duration), "-i", input_path]

    if export_type == "audio":
        cmd += ["-vn", "-acodec", "libmp3lame", "-b:a", "128k", output_path]
    else:
        v_filter = "scale=-2:480" 
        if aspect_ratio == "vertical":
            v_filter = "crop=ih*9/16:ih:(iw-ow)/2:0,scale=-2:480"
        
        cmd += ["-vf", v_filter, "-c:v", "libx264", "-preset", "ultrafast", "-crf", "30"]
        if remove_audio == "true": cmd += ["-an"]
        else: cmd += ["-c:a", "aac", "-b:a", "64k"]
        cmd += [output_path]

    try:
        subprocess.run(cmd, check=True, timeout=90)
        return templates.TemplateResponse(request, "result.html", {"video_name": output_filename})
    except Exception as e:
        return HTMLResponse(content=f"Lite Error: {str(e)}. Try a shorter clip.", status_code=500)
