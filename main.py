import os
import shutil
import subprocess
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# 1. CREATE FOLDERS (Crucial for Render)
os.makedirs("processed_videos", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# 2. MOUNT STORAGE
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
    end_time: int = Form(10),
    export_type: str = Form("video"), 
    aspect_ratio: str = Form("landscape"),
    quality: str = Form("720p"),          
    remove_audio: str = Form("false"),
    generate_thumb: str = Form("false")   
): 
    # Clean filename for safe processing
    base_name = video_file.filename.split('.')[0].replace(" ", "_")
    input_path = f"processed_videos/raw_{video_file.filename}"
    
    # Extension logic
    ext = "mp4"
    if export_type == "mp3": ext = "mp3"
    elif export_type == "gif": ext = "gif"
    
    output_filename = f"out_{base_name}.{ext}"
    output_path = f"processed_videos/{output_filename}"
    thumb_name = f"thumb_{base_name}.jpg"

    # Save incoming file
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(video_file.file, buffer)

    duration = max(1, end_time - start_time)
    
    # 3. CONSTRUCT FFMPEG COMMAND (The most stable way)
    cmd = ["ffmpeg", "-y", "-ss", str(start_time), "-t", str(duration), "-i", input_path]

    if export_type == "mp3":
        # Safe Audio Export
        cmd += ["-vn", "-acodec", "libmp3lame", "-q:a", "2", output_path]
    elif export_type == "gif":
        cmd += ["-vf", "fps=10,scale=480:-1", output_path]
    else:
        # Video with Crop & Quality
        v_filter = f"scale=-1:{'480' if quality == '480p' else '720'}"
        if aspect_ratio == "vertical":
            v_filter = f"crop=ih*9/16:ih,{v_filter}"
        
        cmd += ["-vf", v_filter]
        if remove_audio == "true":
            cmd += ["-an"]
        else:
            cmd += ["-c:a", "aac"]
        cmd += ["-c:v", "libx264", "-preset", "ultrafast", output_path]

    try:
        # Run process
        subprocess.run(cmd, check=True)
        
        # Thumbnail Logic
        thumb_path = f"processed_videos/{thumb_name}"
        subprocess.run([
            "ffmpeg", "-y", "-ss", str(start_time + 0.5), "-i", input_path, 
            "-vframes", "1", thumb_path
        ], check=False)

        return templates.TemplateResponse(request, "result.html", {
            "video_name": output_filename, 
            "thumb_name": thumb_name
        })

    except Exception as e:
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)
