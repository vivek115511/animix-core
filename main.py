
      import os
import shutil
import subprocess
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Setup folders
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
    end_time: int = Form(10),
    export_type: str = Form("video"), 
    aspect_ratio: str = Form("landscape"),
    quality: str = Form("720p"),
    remove_audio: str = Form("false")
): 
    base_name = video_file.filename.split('.')[0].replace(" ", "_")
    input_path = f"processed_videos/raw_{video_file.filename}"
    
    # Determine extension
    ext = "mp4"
    if export_type == "audio": ext = "mp3"
    elif export_type == "gif": ext = "gif"
    
    output_filename = f"out_{base_name}.{ext}"
    output_path = f"processed_videos/{output_filename}"
    thumb_filename = f"thumb_{base_name}.jpg"
    thumb_path = f"processed_videos/{thumb_filename}"

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(video_file.file, buffer)

    duration = max(1, end_time - start_time)
    
    # --- CORE LOGIC ---
    if export_type == "audio":
        # Simple MP3 extraction
        cmd = ["ffmpeg", "-y", "-ss", str(start_time), "-t", str(duration), "-i", input_path, "-q:a", "2", output_path]
    
    elif export_type == "gif":
        # Reliable GIF conversion
        cmd = ["ffmpeg", "-y", "-ss", str(start_time), "-t", str(duration), "-i", input_path, "-vf", "fps=10,scale=480:-1", output_path]
    
    else:
        # Video Processing
        # Better Vertical Logic: Forces 9:16 and centers it
        v_filter = "scale=-1:720"
        if aspect_ratio == "vertical":
            v_filter = "crop=ih*9/16:ih,scale=-1:720"
        
        if quality == "480p":
            v_filter += ",scale=-1:480"

        cmd = ["ffmpeg", "-y", "-ss", str(start_time), "-t", str(duration), "-i", input_path, "-vf", v_filter]
        
        if remove_audio == "true":
            cmd += ["-an"]
        else:
            cmd += ["-c:a", "aac", "-strict", "experimental"]
            
        cmd += ["-c:v", "libx264", "-preset", "ultrafast", output_path]

    # Thumbnail: Offset by 0.5s to avoid black frames
    cmd_thumb = ["ffmpeg", "-y", "-ss", str(start_time + 0.5), "-i", input_path, "-vframes", "1", thumb_path]

    try:
        subprocess.run(cmd, check=True)
        subprocess.run(cmd_thumb, check=True)
        return templates.TemplateResponse(request, "result.html", {
            "video_name": output_filename, 
            "thumb_name": thumb_filename
        })
    except Exception as e:
        return HTMLResponse(content=f"Processing Error: {str(e)}", status_code=500)
