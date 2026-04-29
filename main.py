import os
import shutil
import subprocess
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
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
    end_time: int = Form(5),
    export_type: str = Form("video"), 
    aspect_ratio: str = Form("landscape"),
    quality: str = Form("720p"),          
    remove_audio: str = Form(None),
    generate_thumb: str = Form(None)   
): 
    # Clean filename
    base_name = video_file.filename.split('.')[0].replace(" ", "_")
    input_path = f"processed_videos/raw_{video_file.filename}"
    
    # Determine output extension
    ext = "mp4"
    if export_type == "audio": ext = "mp3"
    elif export_type == "gif": ext = "gif"
    
    output_filename = f"animix_{base_name}.{ext}"
    output_path = f"processed_videos/{output_filename}"
    thumb_name = f"thumb_{base_name}.jpg" if generate_thumb == "true" else None

    # Save incoming file
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(video_file.file, buffer)

    duration = max(1, end_time - start_time)
    
    # 2. CONSTRUCT FFMPEG COMMAND
    cmd = ["ffmpeg", "-y", "-ss", str(start_time), "-t", str(duration), "-i", input_path]

    if export_type == "audio":
        # Extract Audio
        cmd += ["-vn", "-acodec", "libmp3lame", "-b:a", "192k", output_path]
    elif export_type == "gif":
        # Create High-Quality GIF
        cmd += ["-vf", "fps=10,scale=480:-1:flags=lanczos", output_path]
    else:
        # Video with Crop & Quality (Smart Centering)
        v_filter = f"scale=-1:{'480' if quality == '480p' else '720'}"
        if aspect_ratio == "vertical":
            v_filter = f"crop=ih*9/16:ih:(iw-ow)/2:0,scale=-1:{'480' if quality == '480p' else '720'}"
        
        cmd += ["-vf", v_filter]
        if remove_audio == "true":
            cmd += ["-an"]
        else:
            cmd += ["-c:a", "aac", "-b:a", "128k"]
        cmd += ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "28", output_path]

    try:
        # Run process
        subprocess.run(cmd, check=True)
        
        # 3. GENERATE THUMBNAIL
        if thumb_name:
            thumb_path = f"processed_videos/{thumb_name}"
            subprocess.run([
                "ffmpeg", "-y", "-ss", str(start_time + 0.5), "-i", input_path, 
                "-vframes", "1", "-q:v", "2", thumb_path
            ], check=False)

        return templates.TemplateResponse(request, "result.html", {
            "video_name": output_filename, 
            "thumb_name": thumb_name
        })

    except Exception as e:
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)
