import os
import shutil
import subprocess
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# SETUP FOLDERS
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

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(video_file.file, buffer)

    duration = max(1, end_time - start_time)
    
    # PERFORMANCE OPTIMIZED FFMPEG COMMAND
    cmd = ["ffmpeg", "-y", "-ss", str(start_time), "-t", str(duration), "-i", input_path]

    if export_type == "audio":
        cmd += ["-vn", "-acodec", "libmp3lame", "-b:a", "128k", output_path]
    else:
        # Use 480p as default for speed on free servers
        v_filter = "scale=-2:480" 
        if aspect_ratio == "vertical":
            v_filter = "crop=ih*9/16:ih:(iw-ow)/2:0,scale=-2:480"
        
        cmd += ["-vf", v_filter]
        
        if remove_audio == "true":
            cmd += ["-an"]
        else:
            cmd += ["-c:a", "aac", "-b:a", "64k"] # Lower audio bitrate for speed
            
        # preset superfast is the key to stopping the "too much time" error
        cmd += ["-c:v", "libx264", "-preset", "superfast", "-crf", "32", output_path]

    try:
        subprocess.run(cmd, check=True, timeout=60) # Timeout after 60 seconds
        return templates.TemplateResponse(request, "result.html", {"video_name": output_filename})
    except subprocess.TimeoutExpired:
        return HTMLResponse(content="Error: Processing took too long. Try a shorter clip.", status_code=504)
    except Exception as e:
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)
