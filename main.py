import os
import shutil
import subprocess
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Auto-create necessary folders
os.makedirs("processed_videos", exist_ok=True)
os.makedirs("templates", exist_ok=True)

app.mount("/videos", StaticFiles(directory="processed_videos"), name="videos")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # FIXED: In the new FastAPI version, 'request' must be the first argument
    return templates.TemplateResponse(request, "home.html")

@app.post("/upload")
async def handle_upload(
    request: Request, 
    video_file: UploadFile = File(...),
    start_time: int = Form(...),  
    end_time: int = Form(...),
    export_type: str = Form("video"), 
    aspect_ratio: str = Form("landscape"),
    quality: str = Form("720p"),
    remove_audio: str = Form("false")
): 
    base_name = video_file.filename.split('.')[0]
    input_path = f"processed_videos/raw_{video_file.filename}"
    
    # Extension logic
    ext = "mp4"
    if export_type == "audio": ext = "mp3"
    elif export_type == "gif": ext = "gif"
    
    output_filename = f"export_{base_name}.{ext}"
    output_path = f"processed_videos/{output_filename}"
    thumb_filename = f"thumb_{base_name}.jpg"
    thumb_path = f"processed_videos/{thumb_filename}"

    # Save incoming file
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(video_file.file, buffer)

    duration = max(1, end_time - start_time)
    
    # FFmpeg Command Construction
    cmd = ["ffmpeg", "-y", "-ss", str(start_time), "-t", str(duration), "-i", input_path]

    if export_type == "gif":
        cmd += ["-vf", "fps=10,scale=480:-1:flags=lanczos", output_path]
    elif export_type == "audio":
        cmd += ["-vn", "-acodec", "libmp3lame", output_path]
    else:
        v_filter = f"scale=-1:{'480' if quality == '480p' else '720'}"
        if aspect_ratio == "vertical":
            v_filter = f"crop=ih*9/16:ih,scale=-1:{'480' if quality == '480p' else '720'}"
        cmd += ["-vf", v_filter, "-c:v", "libx264", "-preset", "ultrafast"]
        if remove_audio == "true":
            cmd += ["-an"]
        else:
            cmd += ["-c:a", "aac"]
        cmd.append(output_path)

    # Generate Thumbnail
    cmd_thumb = ["ffmpeg", "-y", "-ss", str(start_time), "-i", input_path, "-vframes", "1", thumb_path]

    try:
        subprocess.run(cmd, check=True)
        subprocess.run(cmd_thumb, check=True)
        # FIXED: Passing request first, then template name, then the data dictionary
        return templates.TemplateResponse(
            request, 
            "result.html", 
            {"video_name": output_filename, "thumb_name": thumb_filename}
        )
    except Exception as e:
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)
