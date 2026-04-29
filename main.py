import os
import shutil
import subprocess
from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.post("/upload")
async def handle_upload(
    request: Request, 
    video_file: UploadFile = File(...),
    start_time: int = Form(...),  
    end_time: int = Form(...),
    export_type: str = Form(...), 
    aspect_ratio: str = Form(...),
    quality: str = Form(...),          
    remove_audio: str = Form(None),
    generate_thumb: str = Form(None)   
): 
    # 1. Safety Check
    if not video_file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Please upload a valid video file.")
    
    base_name = video_file.filename.split('.')[0].replace(" ", "_")
    temp_input_path = f"processed_videos/raw_{video_file.filename}"
    
    # Set the right extension
    ext = "mp4"
    if export_type == "mp3": ext = "mp3"
    elif export_type == "gif": ext = "gif"
    
    output_filename = f"out_{base_name}.{ext}"
    output_path = f"processed_videos/{output_filename}"
    thumb_name = f"thumb_{base_name}.jpg" if generate_thumb == "true" else None

    # Save the file
    with open(temp_input_path, "wb") as buffer:
        shutil.copyfileobj(video_file.file, buffer)

    duration = max(1, end_time - start_time)
    
    # 2. Build the FFmpeg Command
    cmd = ["ffmpeg", "-y", "-ss", str(start_time), "-t", str(duration), "-i", temp_input_path]

    if export_type == "mp3":
        # SAFE AUDIO EXPORT
        cmd += ["-vn", "-acodec", "libmp3lame", "-q:a", "2", output_path]
    elif export_type == "gif":
        cmd += ["-vf", "fps=10,scale=480:-1", output_path]
    else:
        # VIDEO PROCESSING (Crop, Quality, Mute)
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
        # Run Video/Audio process
        subprocess.run(cmd, check=True)
        
        # 3. Handle Thumbnail separately to avoid errors
        if thumb_name:
            thumb_path = f"processed_videos/{thumb_name}"
            subprocess.run([
                "ffmpeg", "-y", "-ss", str(start_time + 0.5), "-i", temp_input_path, 
                "-vframes", "1", thumb_path
            ], check=False)

        return templates.TemplateResponse(request, "result.html", {
            "video_name": output_filename, 
            "thumb_name": thumb_name
        })

    except Exception as e:
        return HTTPException(status_code=500, detail=f"FFmpeg Error: {str(e)}")
