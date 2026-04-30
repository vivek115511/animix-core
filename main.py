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
    quality: str = Form("480p"),          
    remove_audio: str = Form(None)
): 
    base_name = video_file.filename.split('.')[0].replace(" ", "_")
    input_path = f"processed_videos/raw_{video_file.filename}"
    
    ext = "mp4"
    if export_type == "audio": 
        ext = "mp3"
    
    output_filename = f"animix_{base_name}.{ext}"
    output_path = f"processed_videos/{output_filename}"

    # CHUNKED STREAMING (Saves Memory for Heavy Files)
    try:
        with open(input_path, "wb") as buffer:
            while chunk := await video_file.read(1024 * 1024): # Read 1MB at a time
                buffer.write(chunk)
    except Exception as e:
        return HTMLResponse(content=f"Upload Failed: {str(e)}", status_code=500)

    duration = max(1, end_time - start_time)
    
    # ULTRA-LOW LOAD COMMAND
    cmd = ["ffmpeg", "-y", "-ss", str(start_time), "-t", str(duration), "-i", input_path]

    if export_type == "audio":
        cmd += ["-vn", "-acodec", "libmp3lame", "-b:a", "128k", output_path]
    else:
        # Lowering to 480p and using "ultrafast" to save CPU
        v_filter = "scale=-2:480" 
        if aspect_ratio == "vertical":
            v_filter = "crop=ih*9/16:ih:(iw-ow)/2:0,scale=-2:480"
        
        cmd += ["-vf", v_filter]
        
        if remove_audio == "true":
            cmd += ["-an"]
        else:
            cmd += ["-c:a", "aac", "-b:a", "64k"]
            
        cmd += ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "35", output_path]

    try:
        # Increased timeout to 120 seconds for heavy files
        subprocess.run(cmd, check=True, timeout=120)
        return templates.TemplateResponse(request, "result.html", {"video_name": output_filename})
    except subprocess.TimeoutExpired:
        return HTMLResponse(content="Render Timeout: This file is too heavy for a free server. Try a smaller file.", status_code=504)
    except Exception as e:
        return HTMLResponse(content=f"Processing Error: {str(e)}", status_code=500)
