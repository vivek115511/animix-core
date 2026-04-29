import os
import shutil
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import moviepy.editor as mp
from moviepy.editor import VideoFileClip

app = FastAPI()

# Cloud Folders - Ensures Render has a place to save files
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
    export_type: str = Form(...), 
    aspect_ratio: str = Form(...),
    quality: str = Form(...),          
    remove_audio: str = Form(None),
    generate_thumb: str = Form(None)   
): 
    # 1. Save the raw file
    temp_input_path = f"processed_videos/raw_{video_file.filename}"
    with open(temp_input_path, "wb") as buffer:
        shutil.copyfileobj(video_file.file, buffer)

    try:
        clip = VideoFileClip(temp_input_path)
        
        # 2. Apply Edits (Using stable v1.0.3 commands: subclip, crop, resize)
        short_clip = clip.subclip(start_time, end_time)
        
        if aspect_ratio == "vertical":
            w, h = short_clip.size
            target_w = int(h * 9 / 16)
            # Correct command is .crop
            short_clip = short_clip.crop(x1=(w/2)-(target_w/2), y1=0, x2=(w/2)+(target_w/2), y2=h)

        if quality == "480p":
            # Correct command is .resize
            short_clip = short_clip.resize(height=480)

        if remove_audio == "true":
            short_clip = short_clip.without_audio()

        # 3. Export the finished file
        base_name = video_file.filename.split('.')[0]
        output_filename = f"short_{base_name}.mp4"
        
        # Added audio_codec for better compatibility
        short_clip.write_videofile(
            f"processed_videos/{output_filename}", 
            codec="libx264", 
            audio_codec="aac",
            temp_audiofile='temp-audio.m4a', 
            remove_temp=True
        )
        
        clip.close()
        short_clip.close()
        
        return templates.TemplateResponse(request, "result.html", {"video_name": output_filename})

    except Exception as e:
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)
